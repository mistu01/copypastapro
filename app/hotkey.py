"""
Global Hotkey & Selection Manager using Low-Level Windows Hooks (WH_KEYBOARD_LL & WH_MOUSE_LL).
- Intercepts Win+V and/or custom hotkeys (e.g. Ctrl+Shift+V) reliably system-wide.
- Detects text selection completion on screen and enables instant 'C' key copying instead of Ctrl + C.
"""

import sys
import time
import threading
import winreg
import ctypes
from ctypes import wintypes
from PySide6.QtCore import QObject, Signal

user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32

WH_KEYBOARD_LL = 13
WH_MOUSE_LL = 14

WM_KEYDOWN = 0x0100
WM_KEYUP = 0x0101
WM_SYSKEYDOWN = 0x0104
WM_SYSKEYUP = 0x0105
WM_QUIT = 0x0012

WM_LBUTTONDOWN = 0x0201
WM_LBUTTONUP = 0x0202
WM_RBUTTONDOWN = 0x0204
WM_MBUTTONDOWN = 0x0207

VK_LWIN = 0x5B
VK_RWIN = 0x5C
VK_CONTROL = 0x11
VK_SHIFT = 0x10
VK_MENU = 0x12  # Alt key
VK_V = 0x56
VK_C = 0x43
VK_ESCAPE = 0x1B

# Structure for low-level keyboard input
class KBDLLHOOKSTRUCT(ctypes.Structure):
    _fields_ = [
        ("vkCode", wintypes.DWORD),
        ("scanCode", wintypes.DWORD),
        ("flags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ctypes.c_size_t)
    ]

# Structure for low-level mouse input
class MSLLHOOKSTRUCT(ctypes.Structure):
    _fields_ = [
        ("pt", wintypes.POINT),
        ("mouseData", wintypes.DWORD),
        ("flags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ctypes.c_size_t)
    ]

HOOKPROC = ctypes.WINFUNCTYPE(ctypes.c_ssize_t, ctypes.c_int, wintypes.WPARAM, wintypes.LPARAM)
user32.CallNextHookEx.restype = ctypes.c_ssize_t
user32.CallNextHookEx.argtypes = [wintypes.HHOOK, ctypes.c_int, wintypes.WPARAM, wintypes.LPARAM]

# Win32 Window & Hit-Test Constants
GA_ROOT = 2
WM_NCHITTEST = 0x0084
SMTO_ABORTIFHUNG = 0x0002
HTCLIENT = 1

# System Cursor Constants
IDC_ARROW = 32512
IDC_IBEAM = 32513
IDC_SIZENS = 32645
IDC_SIZEWE = 32644
IDC_SIZENWSE = 32643
IDC_SIZENESW = 32642
IDC_SIZEALL = 32646
IDC_NO = 32648

class CURSORINFO(ctypes.Structure):
    _fields_ = [
        ("cbSize", wintypes.DWORD),
        ("flags", wintypes.DWORD),
        ("hCursor", wintypes.HANDLE),
        ("ptScreenPos", wintypes.POINT)
    ]

# Window and control classes where text selection is invalid
EXCLUDED_ROOT_CLASSES = {
    "progman",
    "workerw",
    "shell_traywnd",
    "shell_secondarytraywnd",
    "notifyiconoverflowwindow",
    "windows.ui.core.corewindow",
    "xamlhost",
    "xamlexplorerhostislandwindow",
}

EXCLUDED_CONTROL_CLASSES = {
    "scrollbar",
    "#32768",             # Context & popup menus
    "button",
    "toolbarwindow32",
    "msctls_trackbar32",   # Sliders
    "msctls_statusbar32",
    "msctls_progress32",
    "combobox",
    "sysheaderview32",
}

EXPLORER_ROOT_CLASSES = {
    "cabinetwclass",
    "explorewclass",
}

try:
    _h_ibeam = user32.LoadCursorW(None, IDC_IBEAM)
    _h_arrow = user32.LoadCursorW(None, IDC_ARROW)
    _h_no = user32.LoadCursorW(None, IDC_NO)
    _h_resize = {
        user32.LoadCursorW(None, c) for c in (IDC_SIZENS, IDC_SIZEWE, IDC_SIZENWSE, IDC_SIZENESW, IDC_SIZEALL)
    }
except Exception:
    _h_ibeam = 0
    _h_arrow = 0
    _h_no = 0
    _h_resize = set()


def _get_active_cursor():
    """Returns active cursor handle, or 0 if query fails."""
    try:
        ci = CURSORINFO()
        ci.cbSize = ctypes.sizeof(CURSORINFO)
        if user32.GetCursorInfo(ctypes.byref(ci)) and (ci.flags & 1):
            return ci.hCursor
    except Exception:
        pass
    return 0


def _inspect_point(x: int, y: int):
    """
    Inspects control, root window, and hit-test code under point (x, y)
    with a safe 15ms timeout that never hangs hooks.
    """
    try:
        pt = wintypes.POINT(x, y)
        hwnd = user32.WindowFromPoint(pt)
        if not hwnd:
            return 0, "", "", HTCLIENT

        c_buf = ctypes.create_unicode_buffer(256)
        user32.GetClassNameW(hwnd, c_buf, 256)
        ctrl_class = c_buf.value.lower()

        root_class = ""
        root_hwnd = user32.GetAncestor(hwnd, GA_ROOT)
        if root_hwnd:
            r_buf = ctypes.create_unicode_buffer(256)
            user32.GetClassNameW(root_hwnd, r_buf, 256)
            root_class = r_buf.value.lower()

        lparam = ((y & 0xFFFF) << 16) | (x & 0xFFFF)
        hit_res = wintypes.DWORD(HTCLIENT)
        user32.SendMessageTimeoutW(
            hwnd,
            WM_NCHITTEST,
            0,
            lparam,
            SMTO_ABORTIFHUNG,
            15,
            ctypes.byref(hit_res)
        )
        return hwnd, ctrl_class, root_class, hit_res.value
    except Exception:
        return 0, "", "", HTCLIENT


def configure_windows_clipboard_override(disable_native: bool = True):
    """
    Configures Windows registry so Windows Explorer does not intercept Win+V
    and disables native Windows Clipboard History flyout in favor of CopyPasta.
    Only touches Current User (HKCU) - requires no admin elevation.
    """
    try:
        # 1. Disable Win+V in Windows Explorer hotkey list
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced") as key:
            try:
                cur_disabled, _ = winreg.QueryValueEx(key, "DisabledHotkeys")
            except FileNotFoundError:
                cur_disabled = ""

            if disable_native:
                if "V" not in cur_disabled:
                    new_val = cur_disabled + "V"
                    winreg.SetValueEx(key, "DisabledHotkeys", 0, winreg.REG_SZ, new_val)
            else:
                if "V" in cur_disabled:
                    new_val = cur_disabled.replace("V", "")
                    winreg.SetValueEx(key, "DisabledHotkeys", 0, winreg.REG_SZ, new_val)

        # 2. Turn off built-in Windows 10/11 Clipboard History
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Clipboard") as key:
            val = 0 if disable_native else 1
            winreg.SetValueEx(key, "EnableClipboardHistory", 0, winreg.REG_DWORD, val)

    except Exception as e:
        print(f"[Hotkey] Note: Could not update Windows clipboard registry: {e}")


class HotkeyListener(QObject):
    # Signals
    hotkey_triggered = Signal(str)
    selection_detected = Signal(int, int)  # screen x, screen y
    c_copy_triggered = Signal()
    selection_cancelled = Signal()

    def __init__(
        self,
        intercept_win_v: bool = True,
        custom_hotkey_enabled: bool = True,
        selection_c_copy_enabled: bool = True
    ):
        super().__init__()
        self.intercept_win_v = intercept_win_v
        self.custom_hotkey_enabled = custom_hotkey_enabled
        self.selection_c_copy_enabled = selection_c_copy_enabled

        self.hook_id = None
        self.mouse_hook_id = None
        self._thread = None
        self._thread_id = None
        self._running = False
        self._hook_proc_ref = None
        self._mouse_hook_proc_ref = None

        self._win_down = False
        self._selection_mode_active = False

        # Mouse selection drag tracking with window/control discrimination
        self._lbutton_down = False
        self._down_pt = (0, 0)
        self._down_time = 0.0
        self._down_ctrl_class = ""
        self._down_root_class = ""
        self._down_hit = HTCLIENT
        self._down_cursor = 0
        self._last_click_time = 0.0
        self._last_click_pt = (0, 0)

        # Configure Windows registry for Win+V override
        if self.intercept_win_v:
            configure_windows_clipboard_override(True)

    def set_selection_mode(self, active: bool):
        """Enable or disable single-key 'C' copy interception mode."""
        self._selection_mode_active = active

    def update_settings(
        self,
        intercept_win_v: bool,
        custom_hotkey_enabled: bool,
        selection_c_copy_enabled: bool = True
    ):
        self.intercept_win_v = intercept_win_v
        self.custom_hotkey_enabled = custom_hotkey_enabled
        self.selection_c_copy_enabled = selection_c_copy_enabled
        configure_windows_clipboard_override(self.intercept_win_v)

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
            self._thread.join(timeout=1.0)

    def _low_level_keyboard_handler(self, nCode, wParam, lParam):
        if nCode >= 0:
            try:
                kb = KBDLLHOOKSTRUCT.from_address(lParam)

                # Never intercept synthetic/injected keystrokes (allows PasteHelper Ctrl+V and Ctrl+C to pass through!)
                # LLKHF_INJECTED = 0x10, LLKHF_LOWER_IL_INJECTED = 0x02
                if kb.flags & 0x12:
                    return user32.CallNextHookEx(self.hook_id, nCode, wParam, lParam)

                is_down = wParam in (WM_KEYDOWN, WM_SYSKEYDOWN)
                is_up = wParam in (WM_KEYUP, WM_SYSKEYUP)

                # Track Windows key state instantly
                if kb.vkCode in (VK_LWIN, VK_RWIN):
                    if is_down:
                        self._win_down = True
                    elif is_up:
                        self._win_down = False

                phys_win = bool((user32.GetAsyncKeyState(VK_LWIN) | user32.GetAsyncKeyState(VK_RWIN)) & 0x8000)
                if not phys_win:
                    self._win_down = False
                win_active = self._win_down or phys_win

                ctrl_active = bool(user32.GetAsyncKeyState(VK_CONTROL) & 0x8000)
                shift_active = bool(user32.GetAsyncKeyState(VK_SHIFT) & 0x8000)
                alt_active = (
                    bool(kb.flags & 0x20) or
                    bool(user32.GetAsyncKeyState(VK_MENU) & 0x8000) or
                    (wParam in (WM_SYSKEYDOWN, WM_SYSKEYUP))
                )

                # 1. Quick Copy on Selection ('C' key)
                if self.selection_c_copy_enabled and self._selection_mode_active:
                    if kb.vkCode == VK_C and not win_active and not ctrl_active and not alt_active:
                        if is_down:
                            self.c_copy_triggered.emit()
                        # Suppress the raw 'c' key so it doesn't overwrite the selected text!
                        return 1
                    elif kb.vkCode == VK_ESCAPE:
                        if is_down:
                            self.selection_cancelled.emit()
                        return 1
                    elif kb.vkCode not in (VK_LWIN, VK_RWIN, VK_CONTROL, VK_SHIFT, VK_MENU):
                        # Any other typing key cancels selection copy mode and passes through normally
                        self.selection_cancelled.emit()

                # 2. Intercept Win + V
                if kb.vkCode == VK_V:
                    if win_active and not ctrl_active and not shift_active and not alt_active:
                        if self.intercept_win_v:
                            if is_down:
                                self.hotkey_triggered.emit("Win+V")
                                # Send vkE8 dummy mask key to prevent Windows Shell from opening the Start menu
                                user32.keybd_event(0xE8, 0, 0, 0)
                                user32.keybd_event(0xE8, 0, 2, 0)
                            # Suppress BOTH key-down and key-up so Windows 11 never triggers on key-up
                            return 1

                    # 3. Intercept Ctrl + Shift + V
                    if ctrl_active and shift_active and not win_active and not alt_active:
                        if self.custom_hotkey_enabled:
                            if is_down:
                                self.hotkey_triggered.emit("Ctrl+Shift+V")
                            return 1

            except Exception:
                pass

        return user32.CallNextHookEx(self.hook_id, nCode, wParam, lParam)

    def _low_level_mouse_handler(self, nCode, wParam, lParam):
        if nCode >= 0:
            try:
                if not self.selection_c_copy_enabled:
                    return user32.CallNextHookEx(self.mouse_hook_id, nCode, wParam, lParam)

                ms = MSLLHOOKSTRUCT.from_address(lParam)
                now = time.time()

                if wParam == WM_LBUTTONDOWN:
                    self._lbutton_down = True
                    self._down_pt = (ms.pt.x, ms.pt.y)
                    self._down_time = now
                    self._down_cursor = _get_active_cursor()

                    # Inspect origin window, control class, and hit-test
                    (
                        _,
                        self._down_ctrl_class,
                        self._down_root_class,
                        self._down_hit
                    ) = _inspect_point(ms.pt.x, ms.pt.y)

                    # If selection mode was active and user clicks away, dismiss it
                    if self._selection_mode_active:
                        self.selection_cancelled.emit()

                elif wParam == WM_LBUTTONUP:
                    if self._lbutton_down:
                        self._lbutton_down = False
                        x_down, y_down = self._down_pt
                        x_up, y_up = ms.pt.x, ms.pt.y
                        dx = abs(x_up - x_down)
                        dy = abs(y_up - y_down)
                        duration = now - self._down_time
                        up_cursor = _get_active_cursor()

                        # Inspect release window, control class, and hit-test
                        (
                            _,
                            up_ctrl_class,
                            up_root_class,
                            up_hit
                        ) = _inspect_point(x_up, y_up)

                        if self._is_genuine_text_selection(
                            x_down, y_down, x_up, y_up,
                            dx, dy, duration, now,
                            self._down_ctrl_class, self._down_root_class, self._down_hit, self._down_cursor,
                            up_ctrl_class, up_root_class, up_hit, up_cursor
                        ):
                            self.selection_detected.emit(x_up, y_up)

                        self._last_click_time = now
                        self._last_click_pt = (x_up, y_up)

                elif wParam in (WM_RBUTTONDOWN, WM_MBUTTONDOWN):
                    if self._selection_mode_active:
                        self.selection_cancelled.emit()

            except Exception:
                pass

        return user32.CallNextHookEx(self.mouse_hook_id, nCode, wParam, lParam)

    def _is_genuine_text_selection(
        self,
        x_down: int, y_down: int, x_up: int, y_up: int,
        dx: int, dy: int, duration: float, now: float,
        down_ctrl: str, down_root: str, down_hit: int, down_cursor: int,
        up_ctrl: str, up_root: str, up_hit: int, up_cursor: int
    ) -> bool:
        """
        Validates that mouse activity corresponds strictly to genuine text selection,
        filtering out file dragging, scrollbars, context menus, and non-text clicking.
        """
        # 1. Non-Client Chrome Exclusion (Scrollbars, Window Captions, Min/Max/Close, Resize Borders)
        # Any interaction with a scrollbar, titlebar, or border is NEVER text selection.
        if down_hit != HTCLIENT or up_hit != HTCLIENT:
            return False

        # 2. Desktop, Taskbar & Shell System Windows Exclusion
        # Desktop (Progman, WorkerW) and Taskbar (Shell_TrayWnd) never contain selectable text.
        if down_root in EXCLUDED_ROOT_CLASSES or up_root in EXCLUDED_ROOT_CLASSES:
            return False

        # 3. Non-Text Control Classes Exclusion (Scrollbars, Popup Menus #32768, Buttons, Sliders)
        if down_ctrl in EXCLUDED_CONTROL_CLASSES or up_ctrl in EXCLUDED_CONTROL_CLASSES:
            return False

        # 4. File Explorer Exclusion:
        # In File Explorer (CabinetWClass, ExploreWClass), users drag files, marquee-select files, or double-click to open folders.
        # Text selection ONLY occurs when actively renaming or typing in an Edit control (e.g. Address bar, search box, inline rename).
        if down_root in EXPLORER_ROOT_CLASSES or up_root in EXPLORER_ROOT_CLASSES:
            if "edit" not in down_ctrl and "edit" not in up_ctrl:
                return False

        # 5. Cursor checks (if cursor query succeeded)
        # If cursor was a window resize handle or OLE drop-not-allowed cursor:
        if down_cursor in _h_resize or up_cursor in _h_resize:
            return False
        if (_h_no and (down_cursor == _h_no or up_cursor == _h_no)):
            return False

        # 6. Check for Double-Click Selection (Selecting a single word)
        dt = now - self._last_click_time
        dist_from_last = abs(x_up - self._last_click_pt[0]) + abs(y_up - self._last_click_pt[1])
        is_double_click = (dt < 0.42 and dist_from_last < 8 and dx < 6 and dy < 6)

        if is_double_click:
            # Double-clicking on buttons, tabs, or non-text UI elements is never word selection
            if "button" in down_ctrl or "button" in up_ctrl:
                return False
            # If cursor handle is known and is standard arrow (IDC_ARROW), user double-clicked an icon, file, or empty space
            if _h_arrow and (down_cursor == _h_arrow or up_cursor == _h_arrow):
                return False
            return True

        # 7. Drag Selection Validation
        # A. Scrollbar and Vertical Menu Scroll Rejection:
        # Scrolling a scrollbar or scrolling a list is almost purely vertical (tiny dx, large dy).
        # Text is written horizontally, so a drag with dx <= 8 and dy >= 12 is a scroll gesture, NOT text selection!
        if dx <= 8 and dy >= 12:
            return False

        # B. Horizontal Scrollbar Rejection:
        if dy <= 4 and dx >= 35 and (down_ctrl == "scrollbar" or up_ctrl == "scrollbar"):
            return False

        # C. Minimum distance for text selection:
        # Single-line text drag requires at least 14px horizontally (approx 2-3 characters).
        # Multi-line text drag requires at least 10px horizontally and 12px vertically.
        if dx < 14 and not (dx >= 10 and dy >= 12):
            return False

        # D. Duration validation:
        # Intentional text drag takes between 0.07s and 3.5s.
        # Reject instant click jitter (< 0.07s) and long file drags / button holds (> 3.5s).
        if duration < 0.07 or duration > 3.5:
            return False

        return True

    def _run_hook(self):
        self._thread_id = kernel32.GetCurrentThreadId()
        self._hook_proc_ref = HOOKPROC(self._low_level_keyboard_handler)
        self._mouse_hook_proc_ref = HOOKPROC(self._low_level_mouse_handler)

        self.hook_id = user32.SetWindowsHookExW(
            WH_KEYBOARD_LL,
            self._hook_proc_ref,
            None,
            0
        )
        self.mouse_hook_id = user32.SetWindowsHookExW(
            WH_MOUSE_LL,
            self._mouse_hook_proc_ref,
            None,
            0
        )

        if not self.hook_id:
            err = kernel32.GetLastError()
            print(f"[Hotkey] Failed to install keyboard hook! Error: {err}")

        msg = wintypes.MSG()
        while self._running:
            res = user32.GetMessageW(ctypes.byref(msg), None, 0, 0)
            if res <= 0:
                break
            user32.TranslateMessage(ctypes.byref(msg))
            user32.DispatchMessageW(ctypes.byref(msg))

        if self.hook_id:
            user32.UnhookWindowsHookEx(self.hook_id)
            self.hook_id = None
        if self.mouse_hook_id:
            user32.UnhookWindowsHookEx(self.mouse_hook_id)
            self.mouse_hook_id = None
