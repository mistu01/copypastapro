"""
TOTP (Time-based One-Time Password) Manager for CopyPasta.
Complies with RFC 6238 and RFC 4226.
Supports custom issuers, secret validation, otpauth URI parsing, and live countdowns.
"""

import time
import re
import urllib.parse
import base64
import pyotp


class TOTPManager:
    @staticmethod
    def clean_secret(raw_secret: str) -> str:
        """Clean and normalize a Base32 secret string."""
        if not raw_secret:
            return ""
        # Remove spaces, dashes, and convert to uppercase
        clean = re.sub(r'[\s\-]', '', raw_secret).upper()
        # Ensure proper Base32 padding with '='
        missing_padding = len(clean) % 8
        if missing_padding:
            clean += '=' * (8 - missing_padding)
        return clean

    @staticmethod
    def validate_secret(secret: str) -> bool:
        """Validate if a secret is valid Base32."""
        try:
            cleaned = TOTPManager.clean_secret(secret)
            if not cleaned:
                return False
            # Try decoding base32
            base64.b32decode(cleaned, casefold=True)
            return True
        except Exception:
            return False

    @staticmethod
    def parse_otpauth_uri(uri: str) -> dict:
        """
        Parse an otpauth://totp/ URI.
        Returns a dict with: issuer, account_name, secret, digits, period, algorithm.
        """
        parsed = urllib.parse.urlparse(uri.strip())
        if parsed.scheme.lower() != 'otpauth':
            raise ValueError("URI scheme must be 'otpauth'")
        if parsed.netloc.lower() not in ('totp', ''):
            # Some URIs are otpauth://totp/...
            pass

        # Path usually contains /Issuer:Account or /Account
        path = urllib.parse.unquote(parsed.path.lstrip('/'))
        if ':' in path:
            path_issuer, account_name = path.split(':', 1)
        else:
            path_issuer = ""
            account_name = path

        query_params = urllib.parse.parse_qs(parsed.query)
        secret = query_params.get('secret', [''])[0]
        issuer = query_params.get('issuer', [path_issuer])[0]
        digits = int(query_params.get('digits', [6])[0])
        period = int(query_params.get('period', [30])[0])
        algorithm = query_params.get('algorithm', ['SHA1'])[0].upper()

        if not secret:
            raise ValueError("Secret key missing from otpauth URI")

        return {
            'issuer': issuer or path_issuer or "Unknown",
            'account_name': account_name or "Account",
            'secret': TOTPManager.clean_secret(secret),
            'digits': digits,
            'period': period,
            'algorithm': algorithm
        }

    @staticmethod
    def generate_code(secret: str, digits: int = 6, period: int = 30) -> tuple[str, str, int, float]:
        """
        Generate current TOTP code.
        Returns (raw_code, formatted_code, time_remaining, progress_fraction)
        """
        cleaned = TOTPManager.clean_secret(secret)
        totp = pyotp.TOTP(cleaned, digits=digits, interval=period)
        now = time.time()
        raw_code = totp.now()
        
        # Formatted with space in middle if 6 or 8 digits
        if len(raw_code) == 6:
            formatted_code = f"{raw_code[:3]} {raw_code[3:]}"
        elif len(raw_code) == 8:
            formatted_code = f"{raw_code[:4]} {raw_code[4:]}"
        else:
            formatted_code = raw_code

        time_remaining = int(period - (now % period))
        progress = time_remaining / float(period)
        return raw_code, formatted_code, time_remaining, progress

    @staticmethod
    def detect_totp_key(text: str) -> dict | None:
        """
        Auto-detect if copied text is a 2FA TOTP secret key or otpauth:// URI.
        Returns dict with secret, issuer, account, or None if not a 2FA key.
        """
        if not text:
            return None
        text_clean = text.strip()

        # 1. Check otpauth:// URI
        if text_clean.lower().startswith('otpauth://'):
            try:
                data = TOTPManager.parse_otpauth_uri(text_clean)
                return {
                    'type': 'uri',
                    'secret': data['secret'],
                    'issuer': data['issuer'],
                    'account_name': data['account_name'],
                    'digits': data['digits'],
                    'period': data['period'],
                    'source': 'URI'
                }
            except Exception:
                pass

        # 2. Check if chunked in uniform 4-char groups (e.g. 'HXDM VJEC JJWS RB3H WIZR 4IFU GFTM XBOZ')
        if ' ' in text_clean:
            chunks = text_clean.split()
            if len(chunks) in (4, 6, 8) and all(len(c) == 4 for c in chunks):
                combined = ''.join(chunks).upper()
                if re.match(r'^[A-Z2-7]+$', combined) and TOTPManager.validate_secret(combined):
                    return {
                        'type': 'secret',
                        'secret': combined,
                        'issuer': 'Auto-Detected',
                        'account_name': 'Live Key',
                        'digits': 6,
                        'period': 30,
                        'source': 'Chunked'
                    }

        # 3. Check continuous Base32 secret string (with optional dashes)
        continuous = re.sub(r'[\s\-]', '', text_clean).upper()
        if len(continuous) in (16, 20, 24, 26, 32, 40, 64) and re.match(r'^[A-Z2-7]+$', continuous):
            if TOTPManager.validate_secret(continuous):
                return {
                    'type': 'secret',
                    'secret': continuous,
                    'issuer': 'Auto-Detected',
                    'account_name': 'Live Key',
                    'digits': 6,
                    'period': 30,
                    'source': 'Clipboard'
                }

        return None

    @staticmethod
    def mask_secret(secret: str) -> str:
        """Format a secret for display like 'JBSW •••• 3PXP'."""
        cleaned = TOTPManager.clean_secret(secret).replace('=', '')
        if len(cleaned) <= 8:
            return cleaned
        return f"{cleaned[:4]} {'•' * 6} {cleaned[-4:]}"
