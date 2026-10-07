"""
Database layer for CopyPasta using SQLite.
Handles clipboard history, pinned items (max 5 slots), DPAPI-encrypted 2FA accounts, and user settings.
"""

import os
import sqlite3
import time
import re
import json
from typing import Optional, List, Dict, Tuple, Any
from app.security import encrypt_string, decrypt_string


def get_db_path() -> str:
    """Return the path to the SQLite database file in AppData or workspace."""
    app_data = os.environ.get("APPDATA")
    if app_data:
        folder = os.path.join(app_data, "CopyPasta")
    else:
        folder = os.path.join(os.path.expanduser("~"), ".copypasta")
    os.makedirs(folder, exist_ok=True)
    return os.path.join(folder, "copypasta.db")


def get_media_dir() -> str:
    """Return the path to the local media directory for cached clipboard images."""
    app_data = os.environ.get("APPDATA")
    if app_data:
        folder = os.path.join(app_data, "CopyPasta", "media")
    else:
        folder = os.path.join(os.path.expanduser("~"), ".copypasta", "media")
    os.makedirs(folder, exist_ok=True)
    return folder


class Database:
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or get_db_path()
        self._mem_conn = sqlite3.connect(':memory:') if self.db_path == ':memory:' else None
        if self._mem_conn:
            self._mem_conn.row_factory = sqlite3.Row
        self._init_tables()
        self._init_default_settings()

    def _get_connection(self) -> sqlite3.Connection:
        if self._mem_conn:
            return self._mem_conn
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_tables(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            # Clipboard items table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS clipboard_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    content TEXT NOT NULL,
                    content_type TEXT DEFAULT 'text',
                    char_count INTEGER,
                    is_pinned INTEGER DEFAULT 0,
                    pin_slot INTEGER DEFAULT NULL,
                    created_at REAL,
                    last_used_at REAL
                )
            """)
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_is_pinned ON clipboard_items(is_pinned)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_last_used ON clipboard_items(last_used_at)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_pin_slot ON clipboard_items(pin_slot)")

            # 2FA TOTP accounts table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS totp_accounts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    issuer TEXT NOT NULL,
                    account_name TEXT NOT NULL,
                    encrypted_secret BLOB NOT NULL,
                    digits INTEGER DEFAULT 6,
                    period INTEGER DEFAULT 30,
                    algorithm TEXT DEFAULT 'SHA1',
                    created_at REAL
                )
            """)

            # Settings table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value TEXT
                )
            """)
            conn.commit()

    def _init_default_settings(self):
        defaults = {
            "intercept_win_v": "true",
            "custom_hotkey_enabled": "true",
            "custom_hotkey": "Ctrl+Shift+V",
            "floating_bar_enabled": "true",
            "floating_bar_opacity": "0.95",
            "floating_bar_x": "-1",
            "floating_bar_y": "-1",
            "auto_paste_on_select": "true",
            "selection_c_copy_enabled": "true",
            "floating_bar_entry_count": "5",
            "max_history_count": "500",
            "theme": "dark"
        }
        with self._get_connection() as conn:
            cursor = conn.cursor()
            for k, v in defaults.items():
                cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)", (k, v))
            conn.commit()

    # ================= Settings =================
    def get_setting(self, key: str, default: str = "") -> str:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
            row = cursor.fetchone()
            return row["value"] if row else default

    def get_bool_setting(self, key: str, default: bool = False) -> bool:
        val = self.get_setting(key, str(default).lower()).lower()
        return val in ("true", "1", "yes")

    def set_setting(self, key: str, value: Any):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, str(value)))
            conn.commit()

    # ================= Clipboard Management =================
    @staticmethod
    def detect_content_type(text: str) -> str:
        s = text.strip()
        if re.match(r'^https?://[^\s]+$', s):
            return "url"
        if re.match(r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$', s):
            return "email"
        if re.match(r'^#(?:[0-9a-fA-F]{3}){1,2}$', s):
            return "color"
        if "\n" in s and any(kw in s for kw in ["def ", "class ", "import ", "function", "const ", "let ", "var ", "SELECT ", "<div", "{", "}"]):
            return "code"
        return "text"

    def trim_history(self) -> int:
        """
        Trim unpinned history to max_history_count setting.
        Cleans up orphaned media files from disk. Never deletes pinned items.
        """
        try:
            max_history = int(self.get_setting("max_history_count", "500"))
        except ValueError:
            max_history = 500

        media_dir = get_media_dir()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            # Find image items that will be deleted
            cursor.execute("""
                SELECT content, content_type FROM clipboard_items
                WHERE is_pinned = 0 AND id NOT IN (
                    SELECT id FROM clipboard_items
                    WHERE is_pinned = 0
                    ORDER BY last_used_at DESC
                    LIMIT ?
                )
            """, (max_history,))
            to_delete = cursor.fetchall()
            for row in to_delete:
                if row["content_type"] == "image":
                    try:
                        meta = json.loads(row["content"])
                        for p in (meta.get("image_path"), meta.get("thumb_path")):
                            if p and os.path.isfile(p) and p.startswith(media_dir):
                                os.remove(p)
                    except Exception:
                        pass

            cursor.execute("""
                DELETE FROM clipboard_items
                WHERE is_pinned = 0 AND id NOT IN (
                    SELECT id FROM clipboard_items
                    WHERE is_pinned = 0
                    ORDER BY last_used_at DESC
                    LIMIT ?
                )
            """, (max_history,))
            conn.commit()
            return cursor.rowcount

    def add_clipboard_item(self, content: str) -> Optional[int]:
        """
        Add an item to clipboard history. If it already exists, update its timestamp.
        """
        if not content or not content.strip():
            return None
        
        now = time.time()
        c_type = self.detect_content_type(content)
        char_count = len(content)

        with self._get_connection() as conn:
            cursor = conn.cursor()
            # Check if identical content exists
            cursor.execute("SELECT id, is_pinned FROM clipboard_items WHERE content = ?", (content,))
            existing = cursor.fetchone()
            if existing:
                item_id = existing["id"]
                cursor.execute("UPDATE clipboard_items SET last_used_at = ? WHERE id = ?", (now, item_id))
                conn.commit()
                return item_id
            
            cursor.execute("""
                INSERT INTO clipboard_items (content, content_type, char_count, is_pinned, pin_slot, created_at, last_used_at)
                VALUES (?, ?, ?, 0, NULL, ?, ?)
            """, (content, c_type, char_count, now, now))
            new_id = cursor.lastrowid
            conn.commit()

        # Trim history to max_history_count (never delete pinned items)
        self.trim_history()
        return new_id

    def add_image_item(self, image_meta: Dict[str, Any]) -> Optional[int]:
        """
        Add an image item to clipboard history. If identical hash or image path
        already exists, update its last_used_at timestamp.
        """
        image_path = image_meta.get("image_path")
        if not image_path:
            return None

        content = json.dumps(image_meta)
        now = time.time()
        size_bytes = image_meta.get("size_bytes", 0)

        with self._get_connection() as conn:
            cursor = conn.cursor()
            image_hash = image_meta.get("hash")
            existing = None
            if image_hash:
                cursor.execute(
                    "SELECT id, is_pinned FROM clipboard_items WHERE content_type = 'image' AND content LIKE ?",
                    (f'%"{image_hash}"%',)
                )
                existing = cursor.fetchone()

            if not existing and image_path:
                cursor.execute(
                    "SELECT id, is_pinned FROM clipboard_items WHERE content_type = 'image' AND content LIKE ?",
                    (f'%"{image_path}"%',)
                )
                existing = cursor.fetchone()

            if existing:
                item_id = existing["id"]
                cursor.execute("UPDATE clipboard_items SET last_used_at = ? WHERE id = ?", (now, item_id))
                conn.commit()
                return item_id

            cursor.execute("""
                INSERT INTO clipboard_items (content, content_type, char_count, is_pinned, pin_slot, created_at, last_used_at)
                VALUES (?, 'image', ?, 0, NULL, ?, ?)
            """, (content, size_bytes, now, now))
            new_id = cursor.lastrowid
            conn.commit()

        self.trim_history()
        return new_id

    def get_history_count(self) -> int:
        """Return total count of clipboard history items in the database."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM clipboard_items")
            row = cursor.fetchone()
            return row[0] if row else 0

    def get_history(self, search: str = "", limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Return history with pinned items first (slots 1..10), then recent items by last_used_at DESC.
        If limit is None, defaults to the user's max_history_count setting.
        """
        if limit is None:
            try:
                limit = int(self.get_setting("max_history_count", "500"))
            except ValueError:
                limit = 500

        with self._get_connection() as conn:
            cursor = conn.cursor()
            if search.strip():
                query = f"%{search.strip()}%"
                cursor.execute("""
                    SELECT * FROM clipboard_items
                    WHERE content LIKE ?
                    ORDER BY is_pinned DESC, pin_slot ASC, last_used_at DESC
                    LIMIT ?
                """, (query, limit))
            else:
                cursor.execute("""
                    SELECT * FROM clipboard_items
                    ORDER BY is_pinned DESC, pin_slot ASC, last_used_at DESC
                    LIMIT ?
                """, (limit,))
            return [dict(row) for row in cursor.fetchall()]

    def get_pinned_items(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Return the pinned items (up to configured limit), ordered by pin_slot ASC."""
        if limit is None:
            try:
                limit = int(self.get_setting("max_pinned_slots", "10"))
            except ValueError:
                limit = 10
        limit = max(1, min(10, limit))
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM clipboard_items
                WHERE is_pinned = 1
                ORDER BY pin_slot ASC, last_used_at DESC
                LIMIT ?
            """, (limit,))
            return [dict(row) for row in cursor.fetchall()]

    def get_recent_items(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Return the most recent items (pinned or unpinned) for the floating bar."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM clipboard_items
                ORDER BY last_used_at DESC
                LIMIT ?
            """, (limit,))
            return [dict(row) for row in cursor.fetchall()]

    def pin_item(self, item_id: int) -> Tuple[bool, str]:
        """
        Pin an item to the top. Maximum configured entries can be pinned (1..10).
        Returns (success: bool, message: str)
        """
        try:
            max_slots = int(self.get_setting("max_pinned_slots", "10"))
        except ValueError:
            max_slots = 10
        max_slots = max(1, min(10, max_slots))

        with self._get_connection() as conn:
            cursor = conn.cursor()
            # Check if item exists and if already pinned
            cursor.execute("SELECT id, is_pinned, pin_slot FROM clipboard_items WHERE id = ?", (item_id,))
            item = cursor.fetchone()
            if not item:
                return False, "Item not found."
            if item["is_pinned"]:
                return True, f"Item is already pinned to slot #{item['pin_slot']}."

            # Check total pinned count
            cursor.execute("SELECT pin_slot FROM clipboard_items WHERE is_pinned = 1")
            used_slots = [row["pin_slot"] for row in cursor.fetchall() if row["pin_slot"] is not None]
            if len(used_slots) >= max_slots:
                return False, f"Maximum of {max_slots} items can be pinned. Please unpin an item first."

            # Find lowest available slot 1..max_slots
            available_slot = 1
            for slot in range(1, max_slots + 1):
                if slot not in used_slots:
                    available_slot = slot
                    break

            cursor.execute("""
                UPDATE clipboard_items
                SET is_pinned = 1, pin_slot = ?, last_used_at = ?
                WHERE id = ?
            """, (available_slot, time.time(), item_id))
            conn.commit()
            return True, f"Pinned to slot #{available_slot}."

    def unpin_item(self, item_id: int) -> bool:
        """Unpin an item."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE clipboard_items
                SET is_pinned = 0, pin_slot = NULL
                WHERE id = ?
            """, (item_id,))
            conn.commit()
            return cursor.rowcount > 0

    def delete_item(self, item_id: int) -> bool:
        """Delete an item from clipboard history and remove cached media if applicable."""
        media_dir = get_media_dir()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT content, content_type FROM clipboard_items WHERE id = ?", (item_id,))
            row = cursor.fetchone()
            if row and row["content_type"] == "image":
                try:
                    meta = json.loads(row["content"])
                    for p in (meta.get("image_path"), meta.get("thumb_path")):
                        if p and os.path.isfile(p) and p.startswith(media_dir):
                            os.remove(p)
                except Exception:
                    pass

            cursor.execute("DELETE FROM clipboard_items WHERE id = ?", (item_id,))
            conn.commit()
            return cursor.rowcount > 0

    def clear_unpinned_history(self) -> int:
        """Clear all non-pinned history items and their media files. Returns number of cleared items."""
        media_dir = get_media_dir()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT content, content_type FROM clipboard_items WHERE is_pinned = 0")
            for row in cursor.fetchall():
                if row["content_type"] == "image":
                    try:
                        meta = json.loads(row["content"])
                        for p in (meta.get("image_path"), meta.get("thumb_path")):
                            if p and os.path.isfile(p) and p.startswith(media_dir):
                                os.remove(p)
                    except Exception:
                        pass

            cursor.execute("DELETE FROM clipboard_items WHERE is_pinned = 0")
            count = cursor.rowcount
            conn.commit()
            return count

    def touch_item(self, item_id: int):
        """Update last_used_at for an item when copied/pasted."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE clipboard_items SET last_used_at = ? WHERE id = ?", (time.time(), item_id))
            conn.commit()

    # ================= 2FA TOTP Accounts =================
    def add_totp_account(self, issuer: str, account_name: str, secret: str, digits: int = 6, period: int = 30, algorithm: str = "SHA1") -> int:
        """
        Encrypt secret with Windows DPAPI and save 2FA account.
        """
        encrypted_secret = encrypt_string(secret, f"CopyPasta 2FA: {issuer} ({account_name})")
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO totp_accounts (issuer, account_name, encrypted_secret, digits, period, algorithm, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (issuer.strip(), account_name.strip(), encrypted_secret, digits, period, algorithm, time.time()))
            conn.commit()
            return cursor.lastrowid

    def get_totp_accounts(self) -> List[Dict[str, Any]]:
        """
        Return all 2FA accounts with decrypted secrets.
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM totp_accounts ORDER BY issuer ASC, account_name ASC")
            rows = cursor.fetchall()
            accounts = []
            for r in rows:
                acc = dict(r)
                try:
                    acc["secret"] = decrypt_string(acc["encrypted_secret"])
                except Exception as e:
                    print(f"Error decrypting account {acc['id']}: {e}")
                    acc["secret"] = ""
                # Do not expose raw encrypted bytes in dictionary
                del acc["encrypted_secret"]
                accounts.append(acc)
            return accounts

    def delete_totp_account(self, account_id: int) -> bool:
        """Delete a 2FA account."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM totp_accounts WHERE id = ?", (account_id,))
            conn.commit()
            return cursor.rowcount > 0

    def update_totp_account(self, account_id: int, issuer: str, account_name: str, secret: Optional[str] = None) -> bool:
        """Update a 2FA account's details."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            if secret:
                encrypted_secret = encrypt_string(secret, f"CopyPasta 2FA: {issuer} ({account_name})")
                cursor.execute("""
                    UPDATE totp_accounts
                    SET issuer = ?, account_name = ?, encrypted_secret = ?
                    WHERE id = ?
                """, (issuer.strip(), account_name.strip(), encrypted_secret, account_id))
            else:
                cursor.execute("""
                    UPDATE totp_accounts
                    SET issuer = ?, account_name = ?
                    WHERE id = ?
                """, (issuer.strip(), account_name.strip(), account_id))
            conn.commit()
            return cursor.rowcount > 0

    # ================= Active / Live 2FA Key =================
    def set_active_totp(self, secret: str, issuer: str = "Auto-Detected", account_name: str = "Live Key") -> bool:
        """Store the current active/detected 2FA key (DPAPI encrypted)."""
        if not secret:
            return False
        import base64
        enc = encrypt_string(secret, "CopyPasta Active 2FA")
        enc_b64 = base64.b64encode(enc).decode("utf-8")
        self.set_setting("active_totp_secret", enc_b64)
        self.set_setting("active_totp_issuer", issuer)
        self.set_setting("active_totp_account", account_name)
        self.set_setting("active_totp_updated_at", str(time.time()))
        return True

    def get_active_totp(self) -> Optional[Dict[str, Any]]:
        """Retrieve the active/detected 2FA key, decrypted."""
        enc_b64 = self.get_setting("active_totp_secret", "")
        if not enc_b64:
            return None
        import base64
        try:
            enc = base64.b64decode(enc_b64.encode("utf-8"))
            secret = decrypt_string(enc)
            if not secret:
                return None
            return {
                "secret": secret,
                "issuer": self.get_setting("active_totp_issuer", "Auto-Detected"),
                "account_name": self.get_setting("active_totp_account", "Live Key"),
                "updated_at": float(self.get_setting("active_totp_updated_at", "0")),
                "digits": 6,
                "period": 30
            }
        except Exception as e:
            print(f"[DB] Error decrypting active totp: {e}")
            return None

    def clear_active_totp(self):
        self.set_setting("active_totp_secret", "")
        self.set_setting("active_totp_issuer", "")
        self.set_setting("active_totp_account", "")
