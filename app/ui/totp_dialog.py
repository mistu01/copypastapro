"""
Dialog for adding or editing a 2FA TOTP Account.
Supports manual Base32 key entry or one-click otpauth:// URI parsing.
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QComboBox, QMessageBox, QFrame
)
from PySide6.QtCore import Qt
from app.totp_manager import TOTPManager


class AddTotpDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add 2FA Authenticator Account")
        self.setFixedWidth(420)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        self.setStyleSheet("""
            QDialog {
                background-color: #080d0a;
                color: #f0fdf4;
            }
            QLabel {
                color: #a7f3d0;
                font-weight: 500;
                font-size: 12px;
            }
            QLineEdit, QComboBox {
                background-color: rgba(16, 185, 129, 0.08);
                border: 1px solid rgba(16, 185, 129, 0.25);
                border-radius: 6px;
                padding: 7px 10px;
                color: #ffffff;
                font-size: 13px;
            }
            QLineEdit:focus, QComboBox:focus {
                border-color: #00f59b;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 20)

        # Title
        title_label = QLabel("🔑 New Two-Factor Authenticator")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #00f59b;")
        layout.addWidget(title_label)

        # Quick import URI section
        layout.addWidget(QLabel("Paste otpauth:// URI (Optional quick fill):"))
        self.uri_input = QLineEdit()
        self.uri_input.setPlaceholderText("otpauth://totp/Service:user@mail.com?secret=...")
        self.uri_input.textChanged.connect(self._on_uri_changed)
        layout.addWidget(self.uri_input)

        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet("color: rgba(255, 255, 255, 0.1); margin: 4px 0;")
        layout.addWidget(sep)

        # Issuer (Service name)
        layout.addWidget(QLabel("Service / Issuer (e.g. Google, GitHub, Microsoft):"))
        self.issuer_input = QLineEdit()
        self.issuer_input.setPlaceholderText("e.g. GitHub")
        layout.addWidget(self.issuer_input)

        # Account Name / Email
        layout.addWidget(QLabel("Account Name / Email / Username:"))
        self.account_input = QLineEdit()
        self.account_input.setPlaceholderText("e.g. user@example.com")
        layout.addWidget(self.account_input)

        # Secret Key
        layout.addWidget(QLabel("Secret Key (Base32):"))
        self.secret_input = QLineEdit()
        self.secret_input.setPlaceholderText("e.g. JBSWY3DPEHPK3PXP")
        self.secret_input.textChanged.connect(self._validate_secret_live)
        layout.addWidget(self.secret_input)

        self.secret_status_label = QLabel("")
        self.secret_status_label.setStyleSheet("font-size: 11px;")
        layout.addWidget(self.secret_status_label)

        # Digits & Period
        opts_layout = QHBoxLayout()
        digits_layout = QVBoxLayout()
        digits_layout.addWidget(QLabel("Digits:"))
        self.digits_combo = QComboBox()
        self.digits_combo.addItems(["6", "8"])
        digits_layout.addWidget(self.digits_combo)
        opts_layout.addLayout(digits_layout)

        period_layout = QVBoxLayout()
        period_layout.addWidget(QLabel("Period (Seconds):"))
        self.period_combo = QComboBox()
        self.period_combo.addItems(["30", "60"])
        period_layout.addWidget(self.period_combo)
        opts_layout.addLayout(period_layout)

        layout.addLayout(opts_layout)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setProperty("class", "SecondaryButton")
        self.cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self.cancel_btn)

        self.save_btn = QPushButton("Save Account")
        self.save_btn.setProperty("class", "PrimaryButton")
        self.save_btn.clicked.connect(self._on_save)
        btn_layout.addWidget(self.save_btn)

        layout.addLayout(btn_layout)

    def _on_uri_changed(self, text: str):
        text = text.strip()
        if text.startswith("otpauth://"):
            try:
                data = TOTPManager.parse_otpauth_uri(text)
                if data["issuer"]:
                    self.issuer_input.setText(data["issuer"])
                if data["account_name"]:
                    self.account_input.setText(data["account_name"])
                if data["secret"]:
                    self.secret_input.setText(data["secret"])
                self.digits_combo.setCurrentText(str(data["digits"]))
                self.period_combo.setCurrentText(str(data["period"]))
            except Exception as e:
                self.secret_status_label.setText(f"⚠️ Invalid URI: {e}")
                self.secret_status_label.setStyleSheet("color: #ef4444; font-size: 11px;")

    def _validate_secret_live(self, text: str):
        if not text.strip():
            self.secret_status_label.setText("")
            return
        if TOTPManager.validate_secret(text):
            self.secret_status_label.setText("✓ Valid Base32 secret key")
            self.secret_status_label.setStyleSheet("color: #10b981; font-size: 11px;")
        else:
            self.secret_status_label.setText("✗ Invalid Base32 characters detected")
            self.secret_status_label.setStyleSheet("color: #ef4444; font-size: 11px;")

    def _on_save(self):
        issuer = self.issuer_input.text().strip()
        account = self.account_input.text().strip()
        secret = self.secret_input.text().strip()

        if not issuer:
            QMessageBox.warning(self, "Validation Error", "Please provide a Service / Issuer name.")
            self.issuer_input.setFocus()
            return

        if not account:
            account = "Account"

        if not secret or not TOTPManager.validate_secret(secret):
            QMessageBox.warning(self, "Validation Error", "Please enter a valid Base32 secret key.")
            self.secret_input.setFocus()
            return

        self.accept()

    def get_data(self) -> dict:
        return {
            "issuer": self.issuer_input.text().strip(),
            "account_name": self.account_input.text().strip() or "Account",
            "secret": TOTPManager.clean_secret(self.secret_input.text().strip()),
            "digits": int(self.digits_combo.currentText()),
            "period": int(self.period_combo.currentText()),
            "algorithm": "SHA1"
        }
