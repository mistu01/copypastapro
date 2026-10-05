"""
Selection Copy Badge for CopyPasta.
A subtle, non-intrusive floating indicator that appears when text is selected anywhere on screen.
Allows pressing 'C' (or clicking) to copy selected text without needing Ctrl + C.
"""

import sys
import ctypes
from ctypes import wintypes
from typing import Optional

from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QLabel, QPushButton, QFrame, QApplication
)
from PySide6.QtCore import Qt, QPoint, Signal, QTimer, QSize
from PySide6.QtGui import QCursor, QFont

from app.icons import AppIcons


class SelectionCopyBadge(QWidget):
    # Signals
    copy_requested = Signal()
    dismissed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("SelectionCopyBadgeWidget")
        self._is_copied_state = False

        self._init_window()
        self._init_ui()
        self._setup_timer()

    def _init_window(self):
        self.setWindowFlags(
            Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool | Qt.WindowDoesNotAcceptFocus
        )
        self.setAttribute(Qt.WA_ShowWithoutActivating, True)
        self.setAttribute(Qt.WA_TranslucentBackground, True)

    def showEvent(self, event):
        super().showEvent(event)
        hwnd = int(self.winId())
        if hwnd and sys.platform == "win32":
            try:
                user32 = ctypes.windll.user32
                GWL_EXSTYLE = -20
                WS_EX_NOACTIVATE = 0x08000000
                GetWindowLong = getattr(user32, "GetWindowLongPtrW", user32.GetWindowLongW)
                SetWindowLong = getattr(user32, "SetWindowLongPtrW", user32.SetWindowLongW)
                ex_style = GetWindowLong(hwnd, GWL_EXSTYLE)
                SetWindowLong(hwnd, GWL_EXSTYLE, ex_style | WS_EX_NOACTIVATE)
            except Exception:
                pass

    def nativeEvent(self, eventType, message):
        if sys.platform == "win32" and eventType == b"windows_generic_MSG":
            msg = wintypes.MSG.from_address(int(message))
            if msg.message == 0x0021:  # WM_MOUSEACTIVATE
                return True, 3  # MA_NOACTIVATE
        return super().nativeEvent(eventType, message)

    def _init_ui(self):
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Container Pill
        self.pill = QFrame()
        self.pill.setStyleSheet("""
            QFrame {
                background: rgba(6, 16, 11, 0.94);
                border: 1px solid rgba(0, 245, 155, 0.45);
                border-radius: 8px;
            }
        """)
        pill_layout = QHBoxLayout(self.pill)
        pill_layout.setContentsMargins(8, 4, 8, 4)
        pill_layout.setSpacing(6)

        # Icon Label
        self.icon_lbl = QLabel()
        self.icon_lbl.setPixmap(AppIcons.pixmap("clipboard", 13, "#00f59b"))
        self.icon_lbl.setStyleSheet("background: transparent; border: none;")
        pill_layout.addWidget(self.icon_lbl)

        # Interactive Action Button
        self.action_btn = QPushButton("Press 'C' to Copy")
        self.action_btn.setCursor(Qt.PointingHandCursor)
        self.action_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                color: #e2e8f0;
                font-family: 'Segoe UI', Arial, sans-serif;
                font-size: 11px;
                font-weight: 600;
                padding: 1px 2px;
            }
            QPushButton:hover {
                color: #00f59b;
            }
        """)
        self.action_btn.clicked.connect(self._on_action_clicked)
        pill_layout.addWidget(self.action_btn)

        # Key Cap Badge "[C]"
        self.keycap_lbl = QLabel("C")
        self.keycap_lbl.setStyleSheet("""
            background: rgba(0, 245, 155, 0.18);
            border: 1px solid rgba(0, 245, 155, 0.4);
            border-radius: 4px;
            color: #00f59b;
            font-size: 10px;
            font-weight: 700;
            padding: 1px 5px;
            font-family: 'Segoe UI', monospace;
        """)
        pill_layout.addWidget(self.keycap_lbl)

        # Small dismiss button
        self.close_btn = QPushButton("×")
        self.close_btn.setFixedSize(16, 16)
        self.close_btn.setCursor(Qt.PointingHandCursor)
        self.close_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                color: #64748b;
                font-size: 13px;
                font-weight: 700;
                padding: 0;
                margin-left: 2px;
            }
            QPushButton:hover {
                color: #f43f5e;
            }
        """)
        self.close_btn.clicked.connect(self.hide_badge)
        pill_layout.addWidget(self.close_btn)

        main_layout.addWidget(self.pill)

    def _setup_timer(self):
        self.auto_dismiss_timer = QTimer(self)
        self.auto_dismiss_timer.setSingleShot(True)
        self.auto_dismiss_timer.setInterval(3800)  # 3.8s auto-dismiss
        self.auto_dismiss_timer.timeout.connect(self.hide_badge)

    def show_at(self, x: int, y: int):
        """Display the interactive copy badge near the selection point."""
        self._is_copied_state = False
        self.action_btn.setText("Press 'C' to Copy")
        self.icon_lbl.setPixmap(AppIcons.pixmap("clipboard", 13, "#00f59b"))
        self.keycap_lbl.show()
        self.pill.setStyleSheet("""
            QFrame {
                background: rgba(6, 16, 11, 0.94);
                border: 1px solid rgba(0, 245, 155, 0.45);
                border-radius: 8px;
            }
        """)

        self.adjustSize()
        w = self.width()
        h = self.height()

        # Position slightly above cursor release point so it doesn't obscure text
        target_x = x - (w // 2)
        target_y = y - h - 14

        # Bounds check against available screen geometry
        screen = QApplication.primaryScreen()
        if screen:
            geom = screen.availableGeometry()
            if target_y < geom.top():
                target_y = y + 22  # Place below if near top edge
            target_x = max(geom.left() + 10, min(target_x, geom.right() - w - 10))

        self.move(target_x, target_y)
        self.show()
        self.auto_dismiss_timer.start()

    def on_copy_success(self):
        """Feedback animation when copied."""
        self._is_copied_state = True
        self.auto_dismiss_timer.stop()
        self.icon_lbl.setPixmap(AppIcons.pixmap("check", 13, "#00f59b"))
        self.action_btn.setText("✓ Copied!")
        self.action_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                color: #00f59b;
                font-family: 'Segoe UI', Arial, sans-serif;
                font-size: 11px;
                font-weight: 700;
                padding: 1px 2px;
            }
        """)
        self.keycap_lbl.hide()
        self.pill.setStyleSheet("""
            QFrame {
                background: rgba(4, 26, 16, 0.96);
                border: 1px solid rgba(0, 245, 155, 0.8);
                border-radius: 8px;
            }
        """)
        self.adjustSize()
        QTimer.singleShot(650, self.hide_badge)

    def _on_action_clicked(self):
        if not self._is_copied_state:
            self.copy_requested.emit()

    def hide_badge(self):
        self.auto_dismiss_timer.stop()
        self.hide()
        self.dismissed.emit()
