"""
Mistus Copy Pasta - Input Field Quick Paste Dot & Floating Row (v1.3.0)
ZeBeyond Cyber-Emerald Theme.
Automatically detects when the user clicks into an input field or text box in any application,
or when the QuickDot global hotkey (Alt+V / Ctrl+Alt+V) is pressed.
Hovering over the dot menu instantly auto-expands the compact row of recent pastable entries without clicking.
Clicking any entry pastes it directly into the active field.
"""

import sys
import os
import time
import threading
import ctypes
from ctypes import wintypes
from typing import Optional, Tuple, Dict, Any, List

from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QPushButton, QLabel,
    QGraphicsDropShadowEffect, QApplication
)
from PySide6.QtGui import (
    QPainter, QColor, QBrush, QPen, QLinearGradient,
    QCursor, QFont, QGuiApplication, QIcon, QPixmap
)
from PySide6.QtCore import Qt, QPoint, QRect, QTimer, Signal, QObject

from app.icons import AppIcons
from app.database import Database
from app.paste_helper import PasteHelper

user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32
oleacc = ctypes.windll.oleacc

WH_MOUSE_LL = 14
WM_LBUTTONUP = 0x0202
WM_QUIT = 0x0012

ROLE_SYSTEM_TEXT = 42
ROLE_SYSTEM_COMBOBOX = 46

class POINT(ctypes.Structure):
    _fields_ = [("x", wintypes.LONG), ("y", wintypes.LONG)]

class MSLLHOOKSTRUCT(ctypes.Structure):
    _fields_ = [
        ("pt", POINT),
        ("mouseData", wintypes.DWORD),
        ("flags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ctypes.c_size_t),
    ]

HOOKPROC = ctypes.WINFUNCTYPE(ctypes.c_long, ctypes.c_int, wintypes.WPARAM, wintypes.LPARAM)

class VARIANT(ctypes.Structure):
    _fields_ = [
        ("vt", wintypes.WORD),
        ("wReserved1", wintypes.WORD),
        ("wReserved2", wintypes.WORD),
        ("wReserved3", wintypes.WORD),
        ("val", ctypes.c_int64),
        ("val2", ctypes.c_int64),
    ]

class GUITHREADINFO(ctypes.Structure):
    _fields_ = [
        ("cbSize", wintypes.DWORD),
        ("flags", wintypes.DWORD),
        ("hwndActive", wintypes.HWND),
        ("hwndFocus", wintypes.HWND),
        ("hwndCapture", wintypes.HWND),
        ("hwndMenuOwner", wintypes.HWND),
        ("hwndMoveSize", wintypes.HWND),
        ("hwndCaret", wintypes.HWND),
        ("rcCaret", wintypes.RECT),
    ]

GetGUIThreadInfo = user32.GetGUIThreadInfo
GetGUIThreadInfo.argtypes = [wintypes.DWORD, ctypes.POINTER(GUITHREADINFO)]
GetGUIThreadInfo.restype = wintypes.BOOL

AccessibleObjectFromPoint = oleacc.AccessibleObjectFromPoint
AccessibleObjectFromPoint.argtypes = [
    POINT,
    ctypes.POINTER(ctypes.c_void_p),
    ctypes.POINTER(VARIANT)
]
AccessibleObjectFromPoint.restype = ctypes.c_long


def inspect_input_at_point(x: int, y: int, our_pid: int) -> Tuple[bool, Optional[Tuple[int, int, int, int]], Optional[int]]:
    """
    Determines if the screen point (x, y) belongs to an editable text input box.
    Returns (is_input, (left, top, width, height), hwnd).
    """
    try:
        pt = POINT(x, y)
        hwnd = user32.WindowFromPoint(pt)
        if not hwnd:
            return False, None, None

        # Check PID to ignore our own CopyPasta windows
        pid = wintypes.DWORD()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        if pid.value == our_pid:
            return False, None, None

        # 1. Check Win32 Class Name
        buf = ctypes.create_unicode_buffer(256)
        user32.GetClassNameW(hwnd, buf, 256)
        class_name = buf.value.lower()

        known_edit_classes = (
            "edit", "richedit", "richedit20w", "richedit50w", "scintilla",
            "textbox", "search", "directuihwnd", "consolewindowclass",
            "windows.ui.core.corewindow", "applicationframewindow", "term"
        )
        is_known_class = any(k in class_name for k in known_edit_classes)

        # 2. Check IAccessible / MSAA (Chromium, Firefox, Electron, Web inputs, modern forms)
        pacc = ctypes.c_void_p()
        var_child = VARIANT()
        hr = AccessibleObjectFromPoint(pt, ctypes.byref(pacc), ctypes.byref(var_child))
        if hr == 0 and pacc.value:
            try:
                vtable_ptr = ctypes.cast(pacc, ctypes.POINTER(ctypes.c_void_p))[0]
                vtable = ctypes.cast(vtable_ptr, ctypes.POINTER(ctypes.c_void_p))

                # get_accRole (index 13)
                get_acc_role = ctypes.WINFUNCTYPE(
                    ctypes.c_long, ctypes.c_void_p, VARIANT, ctypes.POINTER(VARIANT)
                )(vtable[13])
                var_role = VARIANT()
                hr_role = get_acc_role(pacc.value, var_child, ctypes.byref(var_role))
                role = (var_role.val & 0xFFFFFFFF) if hr_role == 0 else 0

                # accLocation (index 22)
                acc_loc = ctypes.WINFUNCTYPE(
                    ctypes.c_long, ctypes.c_void_p,
                    ctypes.POINTER(ctypes.c_long), ctypes.POINTER(ctypes.c_long),
                    ctypes.POINTER(ctypes.c_long), ctypes.POINTER(ctypes.c_long),
                    VARIANT
                )(vtable[22])
                l, t, w, h = ctypes.c_long(), ctypes.c_long(), ctypes.c_long(), ctypes.c_long()
                hr_loc = acc_loc(pacc.value, ctypes.byref(l), ctypes.byref(t), ctypes.byref(w), ctypes.byref(h), var_child)

                # Release interface
                release_func = ctypes.WINFUNCTYPE(ctypes.c_ulong, ctypes.c_void_p)(vtable[2])
                release_func(pacc.value)

                if role in (ROLE_SYSTEM_TEXT, ROLE_SYSTEM_COMBOBOX):
                    rect = (l.value, t.value, w.value, h.value) if (hr_loc == 0 and w.value > 0 and h.value > 0) else None
                    return True, rect, hwnd
            except Exception:
                pass

        # 3. Check Caret via GetGUIThreadInfo for standard/foreground threads
        gui_info = GUITHREADINFO()
        gui_info.cbSize = ctypes.sizeof(GUITHREADINFO)
        tid = user32.GetWindowThreadProcessId(hwnd, None)
        if GetGUIThreadInfo(tid, ctypes.byref(gui_info)):
            if gui_info.hwndCaret:
                rc = gui_info.rcCaret
                pt_caret = POINT(rc.left, rc.top)
                user32.ClientToScreen(gui_info.hwndCaret, ctypes.byref(pt_caret))
                rect = (pt_caret.x, pt_caret.y, rc.right - rc.left, rc.bottom - rc.top)
                return True, rect, hwnd

        # 4. If class is known edit control
        if is_known_class:
            rect_buf = wintypes.RECT()
            if user32.GetWindowRect(hwnd, ctypes.byref(rect_buf)):
                rect = (
                    rect_buf.left,
                    rect_buf.top,
                    rect_buf.right - rect_buf.left,
                    rect_buf.bottom - rect_buf.top
                )
                return True, rect, hwnd

    except Exception:
        pass

    return False, None, None


class LowLevelMouseHook(QObject):
    """Low-level Windows mouse hook running in a dedicated thread."""
    mouse_clicked = Signal(int, int)

    def __init__(self):
        super().__init__()
        self._hook_id = None
        self._thread = None
        self._thread_id = None
        self._running = False
        self._hook_proc_ref = None

    def start(self):
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._run_hook, daemon=True)
        self._thread.start()

    def stop(self):
        self._running = False
        if self._thread_id:
            user32.PostThreadMessageW(self._thread_id, WM_QUIT, 0, 0)
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=0.5)

    def _mouse_proc(self, nCode, wParam, lParam):
        if nCode >= 0 and wParam == WM_LBUTTONUP:
            try:
                ms = MSLLHOOKSTRUCT.from_address(lParam)
                self.mouse_clicked.emit(ms.pt.x, ms.pt.y)
            except Exception:
                pass
        return user32.CallNextHookEx(self._hook_id, nCode, wParam, lParam)

    def _run_hook(self):
        self._thread_id = kernel32.GetCurrentThreadId()
        self._hook_proc_ref = HOOKPROC(self._mouse_proc)
        self._hook_id = user32.SetWindowsHookExW(
            WH_MOUSE_LL,
            self._hook_proc_ref,
            kernel32.GetModuleHandleW(None),
            0
        )
        if not self._hook_id:
            return

        msg = wintypes.MSG()
        while self._running:
            res = user32.GetMessageW(ctypes.byref(msg), None, 0, 0)
            if res <= 0:
                break
            user32.TranslateMessage(ctypes.byref(msg))
            user32.DispatchMessageW(ctypes.byref(msg))

        if self._hook_id:
            user32.UnhookWindowsHookEx(self._hook_id)
            self._hook_id = None


class QuickDotWindow(QWidget):
    """
    Subtle, sleek floating dot button displayed near the active input field.
    Auto-expands the pasteable entries row on hover without needing to click!
    Does NOT steal focus or deactivate the target application window.
    """
    dot_hovered = Signal(QPoint, int)
    dot_clicked = Signal(QPoint, int)

    def __init__(self):
        super().__init__()
        self.setWindowFlags(
            Qt.WindowStaysOnTopHint |
            Qt.FramelessWindowHint |
            Qt.Tool |
            Qt.WindowDoesNotAcceptFocus
        )
        self.setAttribute(Qt.WA_ShowWithoutActivating, True)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setFixedSize(24, 24)
        self.setCursor(Qt.PointingHandCursor)
        self.setToolTip("Mistus Quick Paste • Hover to reveal recent clips")

        self.target_hwnd: Optional[int] = None
        self._hovered = False

        # Auto-dismiss timer: hides dot after 7s of inactivity
        self.auto_hide_timer = QTimer(self)
        self.auto_hide_timer.setInterval(7000)
        self.auto_hide_timer.setSingleShot(True)
        self.auto_hide_timer.timeout.connect(self.hide)

        # Hover trigger debounce timer
        self._hover_expand_timer = QTimer(self)
        self._hover_expand_timer.setInterval(60)
        self._hover_expand_timer.setSingleShot(True)
        self._hover_expand_timer.timeout.connect(self._trigger_hover_expand)

    def show_at(self, pos: QPoint, target_hwnd: Optional[int]):
        self.target_hwnd = target_hwnd
        self.move(pos)
        self.show()
        self.auto_hide_timer.start()

    def enterEvent(self, event):
        self._hovered = True
        self.auto_hide_timer.start()
        self.update()
        # Auto-expand pasteable entries on hover without clicking!
        self._hover_expand_timer.start()
        super().enterEvent(event)

    def _trigger_hover_expand(self):
        if self._hovered and self.isVisible():
            self.dot_hovered.emit(self.pos(), self.target_hwnd)

    def leaveEvent(self, event):
        self._hovered = False
        self._hover_expand_timer.stop()
        self.update()
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            event.accept()
            target = self.target_hwnd
            pos = self.pos()
            self.dot_clicked.emit(pos, target)
        else:
            super().mousePressEvent(event)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)

        rect = self.rect()

        if self._hovered:
            # Luminous ZeBeyond Mint glow ring on hover
            glow_pen = QPen(QColor(0, 245, 155, 230), 2.0)
            painter.setPen(glow_pen)
            painter.setBrush(QBrush(QColor(5, 150, 105, 240)))
            painter.drawEllipse(2, 2, rect.width() - 4, rect.height() - 4)
        else:
            # Deep Obsidian Emerald Badge
            grad = QLinearGradient(0, 0, rect.width(), rect.height())
            grad.setColorAt(0, QColor(7, 18, 13, 240))
            grad.setColorAt(1, QColor(13, 34, 24, 240))
            painter.setBrush(QBrush(grad))
            painter.setPen(QPen(QColor(0, 245, 155, 160), 1.5))
            painter.drawEllipse(2, 2, rect.width() - 4, rect.height() - 4)

        # Center vector clipboard icon
        icon_color = "#080d0a" if self._hovered else "#00f59b"
        icon_pix = AppIcons.pixmap("clipboard", 12, icon_color, stroke_width=2.2)
        px = (rect.width() - icon_pix.width()) // 2
        py = (rect.height() - icon_pix.height()) // 2
        painter.drawPixmap(px, py, icon_pix)
        painter.end()


class QuickPasteRow(QWidget):
    """
    Compact, sleek horizontal floating chip bar appearing directly above the input field.
    Displays recent clips and pinned items. Clicking any entry instantly inserts it.
    Styled with the ZeBeyond Cyber-Emerald palette. Proportioned to be compact and elegant.
    """
    expand_flyout_requested = Signal()

    def __init__(self, db: Database, paste_helper: PasteHelper):
        super().__init__()
        self.db = db
        self.paste_helper = paste_helper
        self.target_hwnd: Optional[int] = None
        self._is_mouse_inside = False

        self.setWindowFlags(
            Qt.WindowStaysOnTopHint |
            Qt.FramelessWindowHint |
            Qt.Tool |
            Qt.WindowDoesNotAcceptFocus
        )
        self.setAttribute(Qt.WA_ShowWithoutActivating, True)
        self.setAttribute(Qt.WA_TranslucentBackground, True)

        self.auto_hide_timer = QTimer(self)
        self.auto_hide_timer.setInterval(8000)
        self.auto_hide_timer.setSingleShot(True)
        self.auto_hide_timer.timeout.connect(self._on_auto_hide_timeout)

        self._init_ui()

    def _init_ui(self):
        self.main_layout = QHBoxLayout(self)
        self.main_layout.setContentsMargins(4, 2, 4, 2)
        self.main_layout.setSpacing(4)

        # Style sheet for floating bar container - ZeBeyond Cyber-Emerald Theme
        self.setStyleSheet("""
            QuickPasteRow {
                background: transparent;
            }
            #QuickContainer {
                background-color: rgba(8, 15, 11, 0.96);
                border: 1px solid rgba(0, 245, 155, 0.45);
                border-radius: 12px;
            }
            QPushButton.ChipBtn {
                background-color: rgba(16, 185, 129, 0.08);
                border: 1px solid rgba(16, 185, 129, 0.22);
                border-radius: 7px;
                color: #ecfdf5;
                padding: 2px 7px;
                font-size: 11px;
                font-family: 'Segoe UI', system-ui;
                font-weight: 500;
                height: 20px;
            }
            QPushButton.ChipBtn:hover {
                background-color: rgba(16, 185, 129, 0.28);
                border: 1px solid #00f59b;
                color: #ffffff;
            }
            QPushButton.ChipBtn:pressed {
                background-color: rgba(5, 150, 105, 0.65);
            }
            QPushButton.ActionBtn {
                background-color: transparent;
                border: none;
                border-radius: 6px;
                padding: 2px;
            }
            QPushButton.ActionBtn:hover {
                background-color: rgba(16, 185, 129, 0.2);
            }
        """)

        # Container widget for drop shadow and clean border
        self.container = QWidget()
        self.container.setObjectName("QuickContainer")
        self.container_layout = QHBoxLayout(self.container)
        self.container_layout.setContentsMargins(6, 3, 6, 3)
        self.container_layout.setSpacing(4)

        # Left indicator
        self.badge_lbl = QLabel()
        self.badge_lbl.setPixmap(AppIcons.pixmap("clipboard", 12, "#00f59b"))
        self.badge_lbl.setToolTip("Mistus Quick Paste")
        self.container_layout.addWidget(self.badge_lbl)

        # Chips container layout
        self.chips_layout = QHBoxLayout()
        self.chips_layout.setSpacing(4)
        self.container_layout.addLayout(self.chips_layout)

        # Expand full flyout button
        self.btn_expand = QPushButton()
        self.btn_expand.setProperty("class", "ActionBtn")
        self.btn_expand.setIcon(AppIcons.expand(11, "#6ee7b7"))
        self.btn_expand.setToolTip("Open full clipboard manager (Win + V)")
        self.btn_expand.setFixedSize(18, 18)
        self.btn_expand.clicked.connect(self._on_expand_clicked)
        self.container_layout.addWidget(self.btn_expand)

        # Close button
        self.btn_close = QPushButton()
        self.btn_close.setProperty("class", "ActionBtn")
        self.btn_close.setIcon(AppIcons.close_cross(11, "#6ee7b7"))
        self.btn_close.setToolTip("Dismiss")
        self.btn_close.setFixedSize(18, 18)
        self.btn_close.clicked.connect(self.hide)
        self.container_layout.addWidget(self.btn_close)

        # Drop shadow
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(14)
        shadow.setColor(QColor(0, 0, 0, 180))
        shadow.setOffset(0, 3)
        self.container.setGraphicsEffect(shadow)

        self.main_layout.addWidget(self.container)

    def enterEvent(self, event):
        self._is_mouse_inside = True
        self.auto_hide_timer.stop()  # Keep open while browsing
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._is_mouse_inside = False
        self.auto_hide_timer.start(1200)  # Grace period before closing
        super().leaveEvent(event)

    def _on_auto_hide_timeout(self):
        if not self._is_mouse_inside:
            self.hide()

    def show_above(self, dot_pos: QPoint, target_hwnd: Optional[int]):
        """Populate recent clips and position horizontally directly above the input field."""
        self.target_hwnd = target_hwnd

        # Clear old chips
        while self.chips_layout.count():
            item = self.chips_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        # Query pinned items first, then recent items
        pinned_items = self.db.get_pinned_items()
        recent_items = self.db.get_clipboard_history(limit=6)

        # Build compact unique entries list (max 3 to 4 items so it never looks oversized)
        entries: List[Dict[str, Any]] = []
        seen_texts = set()

        for item in pinned_items:
            content = item.get("content", "").strip()
            if content and content not in seen_texts:
                seen_texts.add(content)
                entries.append({"content": content, "pinned": True, "slot": item.get("slot_number", 1)})
                if len(entries) >= 4:
                    break

        if len(entries) < 4:
            for item in recent_items:
                content = item.get("content", "").strip()
                if content and content not in seen_texts:
                    seen_texts.add(content)
                    entries.append({"content": content, "pinned": False})
                    if len(entries) >= 4:
                        break

        if not entries:
            no_clips_lbl = QLabel("No recent clips")
            no_clips_lbl.setStyleSheet("color: #6ee7b7; font-size: 11px; padding: 2px 4px;")
            self.chips_layout.addWidget(no_clips_lbl)
        else:
            for entry in entries:
                btn = self._create_chip_button(entry)
                self.chips_layout.addWidget(btn)

        # Adjust size and position above input box
        self.adjustSize()
        row_w = self.width()
        row_h = self.height()

        # Center above dot position
        row_x = dot_pos.x() - (row_w // 2) + 12
        row_y = dot_pos.y() - row_h - 6

        # Clamping within screen bounds
        screen = QGuiApplication.primaryScreen().availableGeometry()
        row_x = max(screen.left() + 8, min(row_x, screen.right() - row_w - 8))

        # If too close to screen top, flip below the dot
        if row_y < screen.top() + 8:
            row_y = dot_pos.y() + 28

        self.move(row_x, row_y)
        self.show()
        self.auto_hide_timer.start(8000)

    def _create_chip_button(self, entry: Dict[str, Any]) -> QPushButton:
        full_text = entry["content"]
        is_pinned = entry.get("pinned", False)

        # Format snippet: one-line preview, truncated compactly to 13 chars max
        clean_preview = " ".join(full_text.split())
        if len(clean_preview) > 13:
            clean_preview = clean_preview[:11] + "…"

        btn = QPushButton()
        btn.setProperty("class", "ChipBtn")

        if is_pinned:
            slot = entry.get("slot", 1)
            btn.setText(f"#{slot} {clean_preview}")
            btn.setIcon(AppIcons.pin_icon(10, "#fbbf24", filled=True))
        else:
            btn.setText(clean_preview)
            btn.setIcon(AppIcons.clipboard(10, "#00f59b"))

        btn.setToolTip(full_text)
        btn.clicked.connect(lambda: self._on_chip_clicked(full_text))
        return btn

    def _on_chip_clicked(self, text: str):
        target = self.target_hwnd
        self.hide()
        # Set clipboard & simulate Ctrl+V into target input field directly
        self.paste_helper.set_clipboard_text(text)
        self.paste_helper.restore_focus_and_paste(target)

    def _on_expand_clicked(self):
        self.hide()
        self.expand_flyout_requested.emit()


class InputAnchorManager(QObject):
    """
    Coordinates global mouse clicks, caret position, and hotkey activation (Alt+V / Ctrl+Alt+V).
    Hovering on the dot auto-expands the pasteable entries row.
    """
    def __init__(self, db: Database, paste_helper: PasteHelper):
        super().__init__()
        self.db = db
        self.paste_helper = paste_helper
        self.our_pid = os.getpid()

        self.quick_dot = QuickDotWindow()
        self.quick_row = QuickPasteRow(db, paste_helper)

        # Hook & Signals
        self.mouse_hook = LowLevelMouseHook()
        self.mouse_hook.mouse_clicked.connect(self._on_mouse_clicked)

        # Hover on dot auto-expands recent entries without clicking!
        self.quick_dot.dot_hovered.connect(self._on_dot_activated)
        self.quick_dot.dot_clicked.connect(self._on_dot_activated)

        # Start hook if enabled
        if self.db.get_bool_setting("quick_paste_dot_enabled", True):
            self.mouse_hook.start()

    def update_settings(self):
        enabled = self.db.get_bool_setting("quick_paste_dot_enabled", True)
        if enabled:
            self.mouse_hook.start()
        else:
            self.mouse_hook.stop()
            self.quick_dot.hide()
            self.quick_row.hide()

    def on_user_typing(self):
        """Immediately hide the dot when the user begins typing so it never obstructs."""
        if self.quick_dot.isVisible() and not self.quick_row.isVisible():
            self.quick_dot.hide()

    def activate_at_caret_or_cursor(self):
        """
        Triggered when pressing the hotkey (Alt + V / Ctrl + Alt + V).
        Locates the active input caret or mouse cursor and auto-expands the quick paste row!
        """
        fore_hwnd = user32.GetForegroundWindow()
        if not fore_hwnd:
            return

        pid = wintypes.DWORD()
        tid = user32.GetWindowThreadProcessId(fore_hwnd, ctypes.byref(pid))
        if pid.value == self.our_pid:
            return

        screen = QGuiApplication.primaryScreen().availableGeometry()
        dot_w = self.quick_dot.width()
        dot_h = self.quick_dot.height()

        target_x = None
        target_y = None

        # 1. Try to read active caret position
        gui_info = GUITHREADINFO()
        gui_info.cbSize = ctypes.sizeof(GUITHREADINFO)
        if GetGUIThreadInfo(tid, ctypes.byref(gui_info)):
            if gui_info.hwndCaret and win32_is_window_valid(gui_info.hwndCaret):
                rc = gui_info.rcCaret
                pt_caret = POINT(rc.right, rc.top)
                user32.ClientToScreen(gui_info.hwndCaret, ctypes.byref(pt_caret))
                target_x = pt_caret.x + 8
                target_y = pt_caret.y

        # 2. Fallback to cursor position
        if target_x is None:
            pt_cur = POINT()
            user32.GetCursorPos(ctypes.byref(pt_cur))
            target_x = pt_cur.x + 12
            target_y = pt_cur.y - 12

        # Clamp within screen bounds
        target_x = max(screen.left() + 4, min(target_x, screen.right() - dot_w - 4))
        target_y = max(screen.top() + 4, min(target_y, screen.bottom() - dot_h - 4))

        dot_pos = QPoint(target_x, target_y)
        self.quick_dot.show_at(dot_pos, fore_hwnd)
        # Immediately auto-expand the pastable entries row above the caret!
        self._on_dot_activated(dot_pos, fore_hwnd)

    def _on_mouse_clicked(self, x: int, y: int):
        if not self.db.get_bool_setting("quick_paste_dot_enabled", True):
            return

        click_pt = QPoint(x, y)

        # If user clicked inside our own quick dot or quick row, let Qt handle the interaction
        if self.quick_dot.isVisible() and self.quick_dot.geometry().contains(click_pt):
            return
        if self.quick_row.isVisible() and self.quick_row.geometry().contains(click_pt):
            return

        # If quick row was open and clicked outside, dismiss it
        if self.quick_row.isVisible():
            self.quick_row.hide()

        # Inspect if clicked area is an input field
        is_input, rect, target_hwnd = inspect_input_at_point(x, y, self.our_pid)
        if is_input:
            screen = QGuiApplication.primaryScreen().availableGeometry()
            dot_w = self.quick_dot.width()
            dot_h = self.quick_dot.height()

            if rect and rect[2] > 20 and 15 < rect[3] < 120:
                # Place near the right edge inside the field or just beside cursor
                target_x = min(rect[0] + rect[2] - dot_w - 4, max(rect[0] + 4, x + 14))
                target_y = rect[1] + (rect[3] - dot_h) // 2
            else:
                target_x = x + 14
                target_y = y - (dot_h // 2)

            # Clamp within screen bounds
            target_x = max(screen.left() + 4, min(target_x, screen.right() - dot_w - 4))
            target_y = max(screen.top() + 4, min(target_y, screen.bottom() - dot_h - 4))

            self.quick_dot.show_at(QPoint(target_x, target_y), target_hwnd)
        else:
            # Clicked outside an input field -> hide dot
            if self.quick_dot.isVisible():
                self.quick_dot.hide()

    def _on_dot_activated(self, dot_pos: QPoint, target_hwnd: Optional[int]):
        """Expands the pastable entries row right above the dot (triggered on hover or click)."""
        self.quick_row.show_above(dot_pos, target_hwnd)


def win32_is_window_valid(hwnd) -> bool:
    try:
        import win32gui
        return bool(win32gui.IsWindow(hwnd))
    except Exception:
        return True
