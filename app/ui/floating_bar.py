"""
Floating Bar Widget for CopyPasta.
A luxury, translucent, draggable Dynamic Island pill docked at the desktop edge.
Supports dual-sided drag handles (left & right), full draggable surface in minimized mode,
live 2FA code chip, and smooth expand to detailed flyout.
"""

import os
import sys
import json
import ctypes
from ctypes import wintypes
from typing import List, Dict, Any, Optional
from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QLabel, QPushButton, QFrame,
    QMenu, QApplication, QToolTip
)
from PySide6.QtCore import Qt, QPoint, Signal, QTimer, QSize, QRect
from PySide6.QtGui import QAction, QCursor


from app.database import Database
from app.totp_manager import TOTPManager
from app.paste_helper import PasteHelper
from app.icons import AppIcons
from app.styles import DARK_THEME_QSS
from app.version import APP_NAME


class DragHandleButton(QPushButton):
    """A button that acts as an explicit drag grip for the floating bar."""
    def __init__(self, parent_bar, tooltip="Drag to move floating bar"):
        super().__init__()
        self.parent_bar = parent_bar
        self.setProperty("class", "DragGripBtn")
        self.setIcon(AppIcons.drag_grip(18, "#94a3b8"))
        self.setFixedSize(18, 26)
        self.setCursor(Qt.OpenHandCursor)
        self.setToolTip(tooltip)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.parent_bar.start_drag(event.globalPosition().toPoint())
            event.accept()
        elif event.button() == Qt.RightButton:
            self.parent_bar._show_context_menu(event.globalPosition().toPoint())
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.LeftButton:
            self.parent_bar.update_drag(event.globalPosition().toPoint())
            event.accept()

    def mouseReleaseEvent(self, event):
        self.parent_bar.end_drag()
        event.accept()


class FloatingBar(QWidget):
    expand_requested = Signal()
    item_clicked = Signal(str)
    totp_cleared = Signal()
    screenshot_requested = Signal()
    minimized_to_tray = Signal()
    pinned_changed = Signal()

    def __init__(self, db: Database, paste_helper: PasteHelper, parent=None):
        super().__init__(parent)
        self.db = db
        self.paste_helper = paste_helper
        self.is_collapsed = self.db.get_bool_setting("floating_bar_collapsed", False)
        self._dragging = False
        self._drag_start_pos = QPoint()

        self._init_window()
        self._init_ui()
        self._load_position()
        self._setup_totp_timer()

    def _init_window(self):
        self.setObjectName("FloatingBarWidget")
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool | Qt.WindowDoesNotAcceptFocus)
        self.setAttribute(Qt.WA_ShowWithoutActivating, True)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setStyleSheet(DARK_THEME_QSS)

    def showEvent(self, event):
        super().showEvent(event)
        hwnd = int(self.winId())
        if hwnd:
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
                return True, 3  # MA_NOACTIVATE: process mouse click without activating window
        return super().nativeEvent(eventType, message)

    def _init_ui(self):
        self.main_layout = QHBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)

        # Pill Container
        self.pill_frame = QFrame()
        self.pill_frame.setObjectName("FloatingBarContainer")
        self.pill_layout = QHBoxLayout(self.pill_frame)
        self.pill_layout.setContentsMargins(8, 4, 8, 4)
        self.pill_layout.setSpacing(6)

        # Left Drag Handle
        self.left_grip = DragHandleButton(self, "Drag to move • Right-click for options")
        self.left_grip.setIcon(AppIcons.drag_grip(18, "#6ee7b7"))
        self.pill_layout.addWidget(self.left_grip)

        # Brand / App Icon Button
        self.app_icon_btn = QPushButton()
        self.app_icon_btn.setIcon(AppIcons.clipboard(18, "#00f59b"))
        self.app_icon_btn.setFixedSize(22, 22)
        self.app_icon_btn.setProperty("class", "IconButton")
        self.app_icon_btn.setToolTip(f"{APP_NAME} • Click to expand")
        self.app_icon_btn.clicked.connect(self._on_expand_clicked)
        self.pill_layout.addWidget(self.app_icon_btn)

        # Live 2FA Chip Container (Interactive Pill + Dismiss Cross Button)
        self.totp_container = QFrame()
        self.totp_container.setObjectName("FloatingTotpContainer")
        self.totp_container_layout = QHBoxLayout(self.totp_container)
        self.totp_container_layout.setContentsMargins(6, 2, 4, 2)
        self.totp_container_layout.setSpacing(2)

        self.totp_chip = QPushButton()
        self.totp_chip.setObjectName("FloatingTotpInnerBtn")
        self.totp_chip.setIcon(AppIcons.shield_check(14, "#00f59b"))
        self.totp_chip.setIconSize(QSize(14, 14))
        self.totp_chip.setCursor(Qt.PointingHandCursor)
        self.totp_chip.clicked.connect(self._on_totp_chip_clicked)
        self.totp_container_layout.addWidget(self.totp_chip)

        self.totp_close_btn = QPushButton()
        self.totp_close_btn.setObjectName("FloatingTotpDismissBtn")
        self.totp_close_btn.setIcon(AppIcons.close_cross(12, "#6ee7b7"))
        self.totp_close_btn.setIconSize(QSize(12, 12))
        self.totp_close_btn.setFixedSize(18, 18)
        self.totp_close_btn.setToolTip("Remove active 2FA code")
        self.totp_close_btn.setCursor(Qt.PointingHandCursor)
        self.totp_close_btn.clicked.connect(self._on_dismiss_totp)
        self.totp_container_layout.addWidget(self.totp_close_btn)

        self.totp_container.hide()
        self.pill_layout.addWidget(self.totp_container)

        # Center Chips Container for recent snippets
        self.chips_container = QWidget()
        self.chips_layout = QHBoxLayout(self.chips_container)
        self.chips_layout.setContentsMargins(0, 0, 0, 0)
        self.chips_layout.setSpacing(6)
        self.pill_layout.addWidget(self.chips_container)

        # Minimized Label (shown only when collapsed)
        self.minimized_lbl = QLabel()
        self.minimized_lbl.setStyleSheet("color: #6ee7b7; font-size: 11px; font-weight: 600; padding: 0 4px; font-family: 'Segoe UI', Arial, sans-serif;")
        self.minimized_lbl.setCursor(Qt.PointingHandCursor)
        self.minimized_lbl.mousePressEvent = self._on_minimized_lbl_mouse_press
        self.minimized_lbl.hide()
        self.pill_layout.addWidget(self.minimized_lbl)

        # Minimized 2FA Dismiss Cross Button (shown only when collapsed with active 2FA)
        self.minimized_totp_close_btn = QPushButton()
        self.minimized_totp_close_btn.setObjectName("FloatingTotpDismissBtn")
        self.minimized_totp_close_btn.setIcon(AppIcons.close_cross(11, "#6ee7b7"))
        self.minimized_totp_close_btn.setIconSize(QSize(11, 11))
        self.minimized_totp_close_btn.setFixedSize(18, 18)
        self.minimized_totp_close_btn.setToolTip("Remove active 2FA code")
        self.minimized_totp_close_btn.setCursor(Qt.PointingHandCursor)
        self.minimized_totp_close_btn.clicked.connect(self._on_dismiss_totp)
        self.minimized_totp_close_btn.hide()
        self.pill_layout.addWidget(self.minimized_totp_close_btn)

        # Expand to detailed flyout button
        self.expand_btn = QPushButton()
        self.expand_btn.setIcon(AppIcons.expand(16, "#00f59b"))
        self.expand_btn.setToolTip("Expand to detailed flyout (Win + V)")
        self.expand_btn.setProperty("class", "IconButton")
        self.expand_btn.setFixedSize(24, 24)
        self.expand_btn.clicked.connect(self._on_expand_clicked)
        self.pill_layout.addWidget(self.expand_btn)

        # Collapse / Expand toggle button
        self.collapse_btn = QPushButton()
        self.collapse_btn.setIcon(AppIcons.collapse(16, "#6ee7b7"))
        self.collapse_btn.setToolTip("Collapse floating bar to pill")
        self.collapse_btn.setProperty("class", "IconButton")
        self.collapse_btn.setFixedSize(22, 22)
        self.collapse_btn.clicked.connect(self._toggle_collapse)
        self.pill_layout.addWidget(self.collapse_btn)

        # Minimize to Tray button
        self.tray_minimize_btn = QPushButton()
        self.tray_minimize_btn.setIcon(AppIcons.minimize(14, "#6ee7b7"))
        self.tray_minimize_btn.setToolTip("Minimize pill to system tray" if self.is_collapsed else "Minimize to system tray")
        self.tray_minimize_btn.setProperty("class", "IconButton")
        self.tray_minimize_btn.setFixedSize(22, 22)
        self.tray_minimize_btn.setCursor(Qt.PointingHandCursor)
        self.tray_minimize_btn.clicked.connect(self._minimize_to_tray)
        self.pill_layout.addWidget(self.tray_minimize_btn)

        # Right Drag Handle (Resolves right side dragging!)
        self.right_grip = DragHandleButton(self, "Drag to move • Right-click for options")
        self.right_grip.setIcon(AppIcons.drag_grip(18, "#6ee7b7"))
        self.pill_layout.addWidget(self.right_grip)

        self.main_layout.addWidget(self.pill_frame)

        if self.is_collapsed:
            self.pill_frame.setObjectName("MinimizedFloatingContainer")
            self.collapse_btn.setIcon(AppIcons.expand(16, "#38bdf8"))
            self.collapse_btn.setToolTip("Expand floating island")
            self.expand_btn.hide()
            self.totp_container.hide()
            self.chips_container.hide()
            self.minimized_lbl.show()

        self.update_opacity()
        self.refresh_chips()

    def _setup_totp_timer(self):
        self.totp_timer = QTimer(self)
        self.totp_timer.setInterval(900)
        self.totp_timer.timeout.connect(self._update_totp_chip)
        self.totp_timer.start()

    def update_opacity(self):
        try:
            opacity = float(self.db.get_setting("floating_bar_opacity", "0.95"))
        except ValueError:
            opacity = 0.95
        self.setWindowOpacity(opacity)

    def _on_minimized_lbl_mouse_press(self, event):
        if event.button() == Qt.LeftButton:
            self._on_minimized_lbl_clicked()
        elif event.button() == Qt.RightButton:
            self._show_context_menu(event.globalPosition().toPoint())

    def _on_minimized_lbl_clicked(self):
        active_totp = self.db.get_active_totp()
        if active_totp and active_totp.get("secret"):
            try:
                raw_code, _, _, _ = TOTPManager.generate_code(active_totp["secret"])
                self.paste_helper.set_clipboard_text(raw_code)
                auto_paste = self.db.get_bool_setting("auto_paste_on_select", True)
                if auto_paste:
                    self.paste_helper.restore_focus_and_paste()
                self.minimized_lbl.setText("✓ Copied!")
                QTimer.singleShot(1000, self._update_totp_chip)
                return
            except Exception:
                pass
        self._on_expand_clicked()

    def _update_totp_chip(self):
        active_totp = self.db.get_active_totp()
        if not active_totp or not active_totp.get("secret"):
            self.totp_container.hide()
            self.minimized_totp_close_btn.hide()
            if self.is_collapsed:
                count = self.db.get_history_count()
                self.minimized_lbl.setText(f"{count} clips")
                self.minimized_lbl.setStyleSheet("color: #94a3b8; font-size: 11px; font-weight: 600; padding: 0 4px; font-family: 'Segoe UI', Arial, sans-serif;")
                self.minimized_lbl.show()
            return

        try:
            raw_code, formatted, remaining, _ = TOTPManager.generate_code(
                active_totp["secret"], active_totp.get("digits", 6), active_totp.get("period", 30)
            )
            self.totp_chip.setText(f"{formatted}  {remaining}s")
            self.totp_chip.setToolTip(f"Active 2FA ({active_totp['issuer']})\nClick to copy & paste: {raw_code}\nExpires in {remaining}s")
            self.totp_chip.setProperty("raw_code", raw_code)

            if self.is_collapsed:
                # In minimized mode, show the live code in the minimized label with Segoe UI!
                self.totp_container.hide()
                self.minimized_lbl.setText(f"{formatted} ({remaining}s)")
                self.minimized_lbl.setStyleSheet("color: #38bdf8; font-weight: 700; font-family: 'Segoe UI', Arial, sans-serif; font-size: 12px; padding: 0 4px;")
                self.minimized_lbl.show()
                self.minimized_totp_close_btn.show()
            else:
                self.minimized_lbl.hide()
                self.minimized_totp_close_btn.hide()
                self.totp_container.show()
        except Exception:
            self.totp_container.hide()
            self.minimized_totp_close_btn.hide()

    def _on_totp_chip_clicked(self):
        raw_code = self.totp_chip.property("raw_code")
        if raw_code:
            self.paste_helper.set_clipboard_text(raw_code)
            auto_paste = self.db.get_bool_setting("auto_paste_on_select", True)
            if auto_paste:
                self.paste_helper.restore_focus_and_paste()
            self.totp_chip.setText("✓ Copied!")
            QTimer.singleShot(1000, self._update_totp_chip)

    def _on_dismiss_totp(self):
        self.db.clear_active_totp()
        self.totp_container.hide()
        self.minimized_totp_close_btn.hide()
        self.totp_cleared.emit()
        self.refresh_chips()

    def refresh_chips(self):
        self._update_totp_chip()

        # Clear existing history chips
        while self.chips_layout.count() > 0:
            item = self.chips_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if self.is_collapsed:
            self.chips_container.hide()
            self.adjustSize()
            return

        self.chips_container.show()
        try:
            bar_limit = int(self.db.get_setting("floating_bar_entry_count", "5"))
        except ValueError:
            bar_limit = 5
        bar_limit = max(1, min(10, bar_limit))

        recent_items = self.db.get_floating_bar_items(bar_limit=bar_limit)
        if not recent_items and not self.totp_container.isVisible():
            empty_lbl = QLabel("Clipboard empty")
            empty_lbl.setStyleSheet("color: #64748b; font-size: 11px; padding: 0 4px;")
            self.chips_layout.addWidget(empty_lbl)
            self.adjustSize()
            self._ensure_within_screen()
            return

        for item in recent_items:
            btn = self._build_chip_button(item)
            self.chips_layout.addWidget(btn)

        self.adjustSize()
        self._ensure_within_screen()

    def _build_chip_button(self, item: Dict[str, Any]) -> QPushButton:
        is_img = item.get("content_type") == "image"
        meta = {}
        if is_img:
            try:
                meta = json.loads(item["content"])
            except Exception:
                meta = {}
            src = meta.get("source_path", "")
            w = meta.get("width", 0)
            h = meta.get("height", 0)
            preview = os.path.basename(src) if src else f"{w}×{h}"
            if len(preview) > 12:
                preview = preview[:12] + "…"
        else:
            content = item["content"].strip().replace("\n", " ")
            preview = (content[:16] + "…") if len(content) > 16 else content

        btn = QPushButton()
        is_pinned = bool(item.get("is_pinned"))
        if is_pinned:
            btn.setProperty("class", "FloatingChipPinned")
        else:
            btn.setProperty("class", "FloatingChip")
        btn.setIconSize(QSize(14, 14))

        # Icon based on type or pinned
        if is_pinned:
            btn.setIcon(AppIcons.pin_icon(14, "#f59e0b", filled=True))
        elif is_img:
            btn.setIcon(AppIcons.get("image", 14, "#38bdf8"))
        elif item["content_type"] == "url":
            btn.setIcon(AppIcons.link(14, "#38bdf8"))
        elif item["content_type"] == "code":
            btn.setIcon(AppIcons.code(14, "#c084fc"))
        elif item["content_type"] == "email":
            btn.setIcon(AppIcons.mail(14, "#f59e0b"))
        else:
            btn.setIcon(AppIcons.file_text(14, "#94a3b8"))

        btn.setText(f" {preview}")

        pin_label = "📌 Pinned • " if is_pinned else ""
        if is_img:
            btn.setToolTip(f"{pin_label}Image: {preview}\nDimensions: {meta.get('width', 0)} × {meta.get('height', 0)} px\n\nClick to copy & paste • Right-click for options")
        else:
            btn.setToolTip(f"{pin_label}{content}\n\nClick to copy & paste • Right-click for options")
        btn.setCursor(Qt.PointingHandCursor)
        btn.clicked.connect(lambda _, it=item: self._on_chip_clicked(it))

        btn.setContextMenuPolicy(Qt.CustomContextMenu)
        btn.customContextMenuRequested.connect(lambda pos, it=item, b=btn: self._show_chip_context_menu(pos, it, b))
        return btn

    def _show_chip_context_menu(self, pos: QPoint, item: Dict[str, Any], chip_btn: QPushButton):
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: #080d0a;
                border: 1px solid rgba(16, 185, 129, 0.25);
                border-radius: 8px;
                padding: 6px;
                color: #f0fdf4;
            }
            QMenu::item {
                padding: 6px 18px;
                border-radius: 4px;
                font-size: 12px;
            }
            QMenu::item:selected {
                background-color: #059669;
                color: #ffffff;
            }
        """)

        is_pinned = bool(item.get("is_pinned"))
        if is_pinned:
            act_pin = menu.addAction(AppIcons.pin_icon(14, "#f59e0b", filled=False), "Unpin from Pill Bar")
            act_pin.triggered.connect(lambda: self._unpin_chip(item))
        else:
            act_pin = menu.addAction(AppIcons.pin_icon(14, "#f59e0b", filled=True), "Pin to Pill Bar")
            act_pin.triggered.connect(lambda: self._pin_chip(item, chip_btn))

        menu.addSeparator()

        act_paste = menu.addAction(AppIcons.clipboard(14, "#00f59b"), "Copy & Paste")
        act_paste.triggered.connect(lambda: self._on_chip_clicked(item))

        act_del = menu.addAction(AppIcons.trash(14, "#f43f5e"), "Delete Clipping")
        act_del.triggered.connect(lambda: self._delete_chip(item))

        menu.exec(chip_btn.mapToGlobal(pos))

    def _pin_chip(self, item: Dict[str, Any], chip_btn: Optional[QPushButton] = None):
        item_id = item["id"]
        try:
            bar_limit = int(self.db.get_setting("floating_bar_entry_count", "5"))
        except ValueError:
            bar_limit = 5
        bar_limit = max(1, min(10, bar_limit))
        max_pill_pinned = 2 if bar_limit >= 5 else 1

        pinned_items = self.db.get_pinned_items(limit=max_pill_pinned)
        if len(pinned_items) >= max_pill_pinned:
            tip_msg = (
                f"Pill bar allows up to {max_pill_pinned} pinned {'item' if max_pill_pinned == 1 else 'items'} "
                f"({'5+' if bar_limit >= 5 else '<5'} entries enabled).\n"
                f"Please unpin an item first."
            )
            if chip_btn:
                pos = chip_btn.mapToGlobal(QPoint(0, chip_btn.height() + 4))
                QToolTip.showText(pos, tip_msg, chip_btn, QRect(), 3500)
            return

        success, msg = self.db.pin_item(item_id)
        if success:
            self.refresh_chips()
            self.pinned_changed.emit()
        else:
            if chip_btn:
                pos = chip_btn.mapToGlobal(QPoint(0, chip_btn.height() + 4))
                QToolTip.showText(pos, msg, chip_btn, QRect(), 3000)

    def _unpin_chip(self, item: Dict[str, Any]):
        item_id = item["id"]
        self.db.unpin_item(item_id)
        self.refresh_chips()
        self.pinned_changed.emit()

    def _delete_chip(self, item: Dict[str, Any]):
        item_id = item["id"]
        self.db.delete_item(item_id)
        self.refresh_chips()
        self.pinned_changed.emit()

    def _on_chip_clicked(self, item: Dict[str, Any]):
        content = item["content"]
        content_type = item.get("content_type", "text")
        self.db.touch_item(item["id"])

        if content_type == "image":
            try:
                meta = json.loads(content)
                self.paste_helper.set_clipboard_image(meta.get("image_path", ""), meta.get("source_path", ""))
            except Exception as e:
                print(f"[FloatingBar] Error setting clipboard image: {e}")
        else:
            self.paste_helper.set_clipboard_text(content)

        auto_paste = self.db.get_bool_setting("auto_paste_on_select", True)
        if auto_paste:
            self.paste_helper.restore_focus_and_paste()

        self.item_clicked.emit(content)
        # Note: Do not refresh_chips here so the entry position remains stable and doesn't shift on paste!


    def _on_expand_clicked(self):
        self.expand_requested.emit()

    def _toggle_collapse(self):
        self.is_collapsed = not self.is_collapsed
        self.db.set_setting("floating_bar_collapsed", str(self.is_collapsed).lower())
        if self.is_collapsed:
            self.pill_frame.setObjectName("MinimizedFloatingContainer")
            self.collapse_btn.setIcon(AppIcons.expand(16, "#38bdf8"))
            self.collapse_btn.setToolTip("Expand floating island")
            if hasattr(self, "tray_minimize_btn"):
                self.tray_minimize_btn.setToolTip("Minimize pill to system tray")
            self.expand_btn.hide()
            self.totp_container.hide()
            self.chips_container.hide()
            self.minimized_lbl.show()
            active_totp = self.db.get_active_totp()
            if active_totp and active_totp.get("secret"):
                self.minimized_totp_close_btn.show()
            else:
                self.minimized_totp_close_btn.hide()
        else:
            self.pill_frame.setObjectName("FloatingBarContainer")
            self.collapse_btn.setIcon(AppIcons.collapse(16, "#6ee7b7"))
            self.collapse_btn.setToolTip("Collapse floating island to pill")
            if hasattr(self, "tray_minimize_btn"):
                self.tray_minimize_btn.setToolTip("Minimize floating bar to system tray")
            self.expand_btn.show()
            self.minimized_lbl.hide()
            self.minimized_totp_close_btn.hide()
            self.chips_container.show()
            self.refresh_chips()

        self.pill_frame.setStyle(self.pill_frame.style())  # re-apply styling
        self._update_totp_chip()
        self.adjustSize()
        self._ensure_within_screen()

    def _ensure_within_screen(self):
        screen = QApplication.primaryScreen().availableGeometry()
        cur_x = self.x()
        cur_y = self.y()
        w = self.width()
        h = self.height()

        new_x = cur_x
        new_y = cur_y
        if cur_x + w > screen.right() - 8:
            new_x = screen.right() - w - 8
        if new_x < screen.left() + 8:
            new_x = screen.left() + 8
        if cur_y + h > screen.bottom() - 8:
            new_y = screen.bottom() - h - 8
        if new_y < screen.top() + 8:
            new_y = screen.top() + 8

        if new_x != cur_x or new_y != cur_y:
            self.move(new_x, new_y)

    # ================= Universal Dragging Support =================
    def start_drag(self, global_pos: QPoint):
        self._dragging = True
        self._drag_start_pos = global_pos - self.frameGeometry().topLeft()
        self.setCursor(Qt.ClosedHandCursor)

    def update_drag(self, global_pos: QPoint):
        if self._dragging:
            self.move(global_pos - self._drag_start_pos)

    def end_drag(self):
        if self._dragging:
            self._dragging = False
            self.setCursor(Qt.ArrowCursor)
            self.db.set_setting("floating_bar_x", str(self.x()))
            self.db.set_setting("floating_bar_y", str(self.y()))

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.start_drag(event.globalPosition().toPoint())
            event.accept()
        elif event.button() == Qt.RightButton:
            self._show_context_menu(event.globalPosition().toPoint())
            event.accept()

    def mouseMoveEvent(self, event):
        if self._dragging and event.buttons() & Qt.LeftButton:
            self.update_drag(event.globalPosition().toPoint())
            event.accept()

    def mouseReleaseEvent(self, event):
        self.end_drag()
        event.accept()

    def _load_position(self):
        screen = QApplication.primaryScreen().availableGeometry()
        try:
            x = int(self.db.get_setting("floating_bar_x", "-1"))
            y = int(self.db.get_setting("floating_bar_y", "-1"))
        except ValueError:
            x, y = -1, -1

        if x < 0 or y < 0:
            x = screen.right() - 380
            y = screen.bottom() - 65

        x = max(screen.left() + 5, min(x, screen.right() - 180))
        y = max(screen.top() + 5, min(y, screen.bottom() - 45))
        self.move(x, y)

    def _show_context_menu(self, global_pos: QPoint):
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: #080d0a;
                border: 1px solid rgba(16, 185, 129, 0.25);
                border-radius: 8px;
                padding: 6px;
                color: #ffffff;
            }
            QMenu::item {
                padding: 6px 20px;
                border-radius: 4px;
            }
            QMenu::item:selected {
                background-color: #059669;
            }
        """)

        act_expand = menu.addAction(AppIcons.clipboard(16, "#00f59b"), "Open Detailed Manager (Win + V)")
        act_expand.triggered.connect(self._on_expand_clicked)

        act_shot = menu.addAction(AppIcons.camera(16, "#38bdf8"), "Take Screenshot (PrtScn)")
        act_shot.triggered.connect(self.screenshot_requested.emit)

        menu.addSeparator()

        if self.is_collapsed:
            act_toggle = menu.addAction(AppIcons.expand(16, "#34d399"), "Expand to Floating Bar")
            act_toggle.triggered.connect(self._toggle_collapse)
        else:
            act_toggle = menu.addAction(AppIcons.collapse(16, "#34d399"), "Collapse to Compact Pill")
            act_toggle.triggered.connect(self._toggle_collapse)

        menu.addSeparator()

        act_dock_br = menu.addAction(AppIcons.pin_icon(14, "#94a3b8"), "Dock to Bottom-Right")
        act_dock_br.triggered.connect(self._dock_bottom_right)

        act_dock_tr = menu.addAction(AppIcons.pin_icon(14, "#94a3b8"), "Dock to Top-Right")
        act_dock_tr.triggered.connect(self._dock_top_right)

        menu.addSeparator()

        act_tray = menu.addAction(AppIcons.minimize(14, "#f59e0b"), "Minimize to System Tray")
        act_tray.triggered.connect(self._minimize_to_tray)

        menu.exec(global_pos)

    def _dock_bottom_right(self):
        screen = QApplication.primaryScreen().availableGeometry()
        self.move(screen.right() - self.width() - 16, screen.bottom() - self.height() - 16)
        self.db.set_setting("floating_bar_x", str(self.x()))
        self.db.set_setting("floating_bar_y", str(self.y()))

    def _dock_top_right(self):
        screen = QApplication.primaryScreen().availableGeometry()
        self.move(screen.right() - self.width() - 16, screen.top() + 16)
        self.db.set_setting("floating_bar_x", str(self.x()))
        self.db.set_setting("floating_bar_y", str(self.y()))

    def _minimize_to_tray(self):
        self.db.set_setting("floating_bar_enabled", "false")
        self.hide()
        self.minimized_to_tray.emit()

    def _hide_bar(self):
        self._minimize_to_tray()
