"""
CopyPasta - Main Application Entry Point
Next-generation Windows Clipboard Manager with 10-slot Pinning, 2FA TOTP Generator, and Floating Bar.
"""

import sys
import os
import ctypes
from ctypes import wintypes
from typing import Optional

from PySide6.QtWidgets import (
    QApplication, QSystemTrayIcon, QMenu, QMessageBox
)
from PySide6.QtGui import QIcon, QPixmap, QPainter, QColor, QFont, QPen, QLinearGradient
from PySide6.QtCore import Qt, QPoint, QTimer

from app.database import Database
from app.paste_helper import PasteHelper
from app.totp_manager import TOTPManager
from app.hotkey import HotkeyListener
from app.ui.detailed_window import DetailedWindow
from app.ui.floating_bar import FloatingBar
from app.ui.selection_badge import SelectionCopyBadge


from app.icons import AppIcons
from app.version import APP_NAME, APP_VERSION, APP_MUTEX_NAME


def create_app_icon() -> QIcon:
    """Create a crisp modern Fluent app icon with vector Lucide artwork in ZeBeyond Cyber-Emerald palette."""
    pix = QPixmap(64, 64)
    pix.fill(Qt.transparent)
    painter = QPainter(pix)
    painter.setRenderHint(QPainter.Antialiasing)
    painter.setRenderHint(QPainter.SmoothPixmapTransform)

    # ZeBeyond Cyber-Emerald gradient tile with rounded corners
    grad = QLinearGradient(0, 0, 64, 64)
    grad.setColorAt(0, QColor("#059669"))
    grad.setColorAt(1, QColor("#064e3b"))
    painter.setBrush(grad)
    painter.setPen(QPen(QColor("#00f59b"), 1.2))
    painter.drawRoundedRect(4, 4, 56, 56, 14, 14)

    # Crisp vector Lucide clipboard icon in center
    clip_pix = AppIcons.pixmap("clipboard", 34, "#ffffff", stroke_width=2.2)
    painter.drawPixmap(15, 15, clip_pix)
    painter.end()

    return QIcon(pix)


def check_single_instance() -> Optional[wintypes.HANDLE]:
    """Ensure only one instance of Mistus Copy Pasta runs at a time using Windows Mutex."""
    kernel32 = ctypes.windll.kernel32
    ERROR_ALREADY_EXISTS = 183
    mutex = kernel32.CreateMutexW(None, False, APP_MUTEX_NAME)
    last_err = kernel32.GetLastError()
    if last_err == ERROR_ALREADY_EXISTS:
        return None
    return mutex


class CopyPastaApp:
    def __init__(self, qt_app: QApplication):
        self.app = qt_app
        self.app.setQuitOnLastWindowClosed(False)
        self.app_icon = create_app_icon()
        self.app.setWindowIcon(self.app_icon)

        # Core services
        self.db = Database()
        self.paste_helper = PasteHelper()

        # UI Components
        self.detailed_window = DetailedWindow(self.db, self.paste_helper)
        self.floating_bar = FloatingBar(self.db, self.paste_helper)
        self.selection_badge = SelectionCopyBadge()

        # Hotkey listener (Win+V, Ctrl+Shift+V, and 'C' key selection copy)
        self.hotkey_listener = HotkeyListener(
            intercept_win_v=self.db.get_bool_setting("intercept_win_v", True),
            custom_hotkey_enabled=self.db.get_bool_setting("custom_hotkey_enabled", True),
            selection_c_copy_enabled=self.db.get_bool_setting("selection_c_copy_enabled", True)
        )
        self.hotkey_listener.hotkey_triggered.connect(self._on_hotkey_triggered)
        self.hotkey_listener.selection_detected.connect(self._on_selection_detected)
        self.hotkey_listener.c_copy_triggered.connect(self._on_c_copy_triggered)
        self.hotkey_listener.selection_cancelled.connect(self._on_selection_cancelled)
        self.hotkey_listener.start()

        # Selection Badge Signals
        self.selection_badge.copy_requested.connect(self._on_c_copy_triggered)
        self.selection_badge.dismissed.connect(lambda: self.hotkey_listener.set_selection_mode(False))

        # Wire Signals
        self.floating_bar.expand_requested.connect(self._on_expand_requested)
        self.floating_bar.totp_cleared.connect(self._on_totp_cleared)
        self.detailed_window.settings_changed.connect(self._on_settings_changed)
        self.detailed_window.pinned_changed.connect(self.floating_bar.refresh_chips)

        # Clipboard Monitor
        self._last_clip_text = ""
        self.clipboard = self.app.clipboard()
        self.clipboard.dataChanged.connect(self._on_clipboard_changed)

        # System Tray
        self._init_tray()

        # Show Floating Bar if enabled
        if self.db.get_bool_setting("floating_bar_enabled", True):
            self.floating_bar.show()

    def _init_tray(self):
        self.tray = QSystemTrayIcon(self.app_icon, self.app)
        self.tray.setToolTip(f"{APP_NAME} - Windows Clipboard Manager & 2FA")

        tray_menu = QMenu()
        tray_menu.setStyleSheet("""
            QMenu {
                background-color: #080d0a;
                border: 1px solid rgba(16, 185, 129, 0.25);
                border-radius: 8px;
                padding: 6px;
                color: #f0fdf4;
            }
            QMenu::item {
                padding: 6px 20px;
                border-radius: 4px;
            }
            QMenu::item:selected {
                background-color: #059669;
                color: #ffffff;
            }
        """)

        act_open = tray_menu.addAction(AppIcons.clipboard(16, "#00f59b"), "Open Clipboard Manager (Win + V)")
        act_open.triggered.connect(self.toggle_detailed_window)

        act_toggle_bar = tray_menu.addAction(AppIcons.expand(16, "#34d399"), "Toggle Floating Bar")
        act_toggle_bar.triggered.connect(self._toggle_floating_bar)

        act_add_2fa = tray_menu.addAction(AppIcons.shield_check(16, "#10b981"), "Add 2FA Account...")
        act_add_2fa.triggered.connect(self._open_2fa_dialog)

        tray_menu.addSeparator()

        act_settings = tray_menu.addAction(AppIcons.settings(16, "#a7f3d0"), "Settings")
        act_settings.triggered.connect(self._open_settings)

        act_exit = tray_menu.addAction(AppIcons.close_cross(16, "#f43f5e"), f"Exit {APP_NAME}")
        act_exit.triggered.connect(self.quit)

        self.tray.setContextMenu(tray_menu)
        self.tray.activated.connect(self._on_tray_activated)
        self.tray.show()

    def _on_tray_activated(self, reason):
        if reason in (QSystemTrayIcon.DoubleClick, QSystemTrayIcon.Trigger):
            self.toggle_detailed_window()

    def _on_hotkey_triggered(self, key_name: str):
        self.toggle_detailed_window()

    def toggle_detailed_window(self):
        if self.detailed_window.isVisible():
            self.detailed_window.hide_window()
        else:
            self.detailed_window.show_flyout()

    def _on_expand_requested(self):
        # Position flyout conveniently right next to floating bar
        bar_pos = self.floating_bar.pos()
        screen = QApplication.primaryScreen().availableGeometry()
        
        target_x = bar_pos.x()
        target_y = bar_pos.y() - self.detailed_window.height() - 10
        if target_y < screen.top():
            target_y = bar_pos.y() + self.floating_bar.height() + 10

        self.detailed_window.show_flyout(QPoint(target_x, target_y))

    def _on_clipboard_changed(self):
        try:
            text = self.clipboard.text()
            if not text or not text.strip():
                return
            if text == self._last_clip_text or text == getattr(self.paste_helper, "last_copied_text", None):
                self._last_clip_text = text
                return

            self._last_clip_text = text
            self.db.add_clipboard_item(text)

            # Auto-detect if copied text is a 2FA secret key or otpauth:// URI
            detected = TOTPManager.detect_totp_key(text)
            if detected:
                self.db.set_active_totp(
                    detected["secret"],
                    detected.get("issuer", "Auto-Detected"),
                    detected.get("account_name", "Live Key")
                )
                try:
                    _, formatted, rem, _ = TOTPManager.generate_code(detected["secret"])
                    self.detailed_window.toast.show_message(
                        f"🔑 2FA Key Auto-Detected! Code: {formatted} ({rem}s)"
                    )
                except Exception:
                    pass
                if self.detailed_window.isVisible():
                    self.detailed_window.refresh_totp_accounts()

            self.floating_bar.refresh_chips()
            if self.detailed_window.isVisible():
                self.detailed_window.refresh_clipboard_items()
        except Exception as e:
            print(f"[Clipboard] Error reading clipboard: {e}")

    def _on_selection_detected(self, x: int, y: int):
        if not self.db.get_bool_setting("selection_c_copy_enabled", True):
            return
        pos = QPoint(x, y)
        if self.floating_bar.isVisible() and self.floating_bar.frameGeometry().contains(pos):
            return
        if self.detailed_window.isVisible() and self.detailed_window.frameGeometry().contains(pos):
            return
        if self.selection_badge.isVisible() and self.selection_badge.frameGeometry().contains(pos):
            return

        self.hotkey_listener.set_selection_mode(True)
        self.selection_badge.show_at(x, y)

    def _on_c_copy_triggered(self):
        self.paste_helper.copy_selection()
        self.selection_badge.on_copy_success()
        self.hotkey_listener.set_selection_mode(False)

    def _on_selection_cancelled(self):
        self.hotkey_listener.set_selection_mode(False)
        self.selection_badge.hide_badge()

    def _on_totp_cleared(self):
        if self.detailed_window.isVisible():
            self.detailed_window.refresh_totp_accounts()

    def _on_settings_changed(self):
        # Update hotkey listener
        self.hotkey_listener.update_settings(
            intercept_win_v=self.db.get_bool_setting("intercept_win_v", True),
            custom_hotkey_enabled=self.db.get_bool_setting("custom_hotkey_enabled", True),
            selection_c_copy_enabled=self.db.get_bool_setting("selection_c_copy_enabled", True)
        )
        if not self.db.get_bool_setting("selection_c_copy_enabled", True):
            self.hotkey_listener.set_selection_mode(False)
            self.selection_badge.hide_badge()

        # Update floating bar
        bar_enabled = self.db.get_bool_setting("floating_bar_enabled", True)
        if bar_enabled:
            self.floating_bar.update_opacity()
            self.floating_bar.refresh_chips()
            self.floating_bar.show()
        else:
            self.floating_bar.hide()

    def _toggle_floating_bar(self):
        cur = self.db.get_bool_setting("floating_bar_enabled", True)
        new_val = not cur
        self.db.set_setting("floating_bar_enabled", str(new_val).lower())
        self._on_settings_changed()

    def _open_2fa_dialog(self):
        self.detailed_window.show_flyout()
        self.detailed_window._switch_tab(2)
        self.detailed_window._show_add_totp_dialog()

    def _open_settings(self):
        self.detailed_window.show_flyout()
        self.detailed_window._switch_tab(3)

    def quit(self):
        self.hotkey_listener.stop()
        self.selection_badge.hide()
        self.tray.hide()
        self.app.quit()


def main():
    # Enable High DPI scaling
    os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"

    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setApplicationVersion(APP_VERSION)
    app.setOrganizationName("Mistus")

    # Single instance check
    mutex = check_single_instance()
    if not mutex:
        # Another instance is already running
        QMessageBox.information(
            None,
            APP_NAME,
            f"{APP_NAME} is already running in the system tray!\nPress Win + V or check your taskbar tray."
        )
        sys.exit(0)

    manager = CopyPastaApp(app)
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
