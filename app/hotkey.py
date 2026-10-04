"""
Global Hotkey Manager using Low-Level Windows Keyboard Hook (WH_KEYBOARD_LL).
Intercepts Win+V and/or custom hotkeys (e.g. Ctrl+Shift+V) reliably system-wide.
"""

import sys
import threading
import ctypes
from ctypes import wintypes
from PySide6.QtCore import QObject, Signal

user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32

WH_KEYBOARD_LL = 13
WM_KEYDOWN = 0x0100
WM_KEYUP = 0x0101
WM_SYSKEYDOWN = 0x0104
WM_SYSKEYUP = 0x0105
WM_QUIT = 0x0012

VK_LWIN = 0x5B
VK_RWIN = 0x5C
VK_CONTROL = 0x11
VK_SHIFT = 0x10
VK_MENU = 0x12  # Alt key
VK_V = 0x56

# Structure for low-level keyboard input
class KBDLLHOOKSTRUCT(ctypes.Structure):
    _fields_ = [
        ("vkCode", wintypes.DWORD),
        ("scanCode", wintypes.DWORD),
        ("flags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ctypes.c_size_t)
    ]

HOOKPROC = ctypes.WINFUNCTYPE(ctypes.c_long, ctypes.c_int, wintypes.WPARAM, wintypes.LPARAM)


class HotkeyListener(QObject):
    # Signal emitted when hotkey is triggered
    hotkey_triggered = Signal(str)
    # Signal emitted on general keyboard typing
    user_typing = Signal()

    def __init__(self, intercept_win_v: bool = True, custom_hotkey_enabled: bool = True):
        super().__init__()
        self.intercept_win_v = intercept_win_v
        self.custom_hotkey_enabled = custom_hotkey_enabled
        self.hook_id = None
        self._thread = None
        self._thread_id = None
        self._running = False
        self._hook_proc_ref = None
        self._win_down = False
        self._ctrl_down = False
        self._shift_down = False
        self._alt_down = False

    def update_settings(self, intercept_win_v: bool, custom_hotkey_enabled: bool):
        self.intercept_win_v = intercept_win_v
        self.custom_hotkey_enabled = custom_hotkey_enabled

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

    def _low_level_handler(self, nCode, wParam, lParam):
        if nCode >= 0:
            try:
                kb = KBDLLHOOKSTRUCT.from_address(lParam)
                is_down = wParam in (WM_KEYDOWN, WM_SYSKEYDOWN)
                is_up = wParam in (WM_KEYUP, WM_SYSKEYUP)

                # Track Windows key
                if kb.vkCode in (VK_LWIN, VK_RWIN):
                    if is_down:
                        self._win_down = True
                    elif is_up:
                        self._win_down = False

                # Track Ctrl
                if kb.vkCode in (VK_CONTROL, 0xA2, 0xA3):
                    if is_down:
                        self._ctrl_down = True
                    elif is_up:
                        self._ctrl_down = False

                # Track Shift
                if kb.vkCode in (VK_SHIFT, 0xA0, 0xA1):
                    if is_down:
                        self._shift_down = True
                    elif is_up:
                        self._shift_down = False

                # Track Alt
                if kb.vkCode in (VK_MENU, 0x12, 0xA4, 0xA5):
                    if is_down:
                        self._alt_down = True
                    elif is_up:
                        self._alt_down = False

                # Handle 'V' key press
                if is_down and kb.vkCode == VK_V:
                    # Check Windows Key state
                    win_active = self._win_down or bool(user32.GetAsyncKeyState(VK_LWIN) & 0x8000) or bool(user32.GetAsyncKeyState(VK_RWIN) & 0x8000)
                    ctrl_active = self._ctrl_down or bool(user32.GetAsyncKeyState(VK_CONTROL) & 0x8000)
                    shift_active = self._shift_down or bool(user32.GetAsyncKeyState(VK_SHIFT) & 0x8000)
                    alt_active = (
                        self._alt_down or
                        bool(kb.flags & 0x20) or
                        bool(user32.GetAsyncKeyState(VK_MENU) & 0x8000) or
                        bool(user32.GetAsyncKeyState(0xA4) & 0x8000) or
                        bool(user32.GetAsyncKeyState(0xA5) & 0x8000) or
                        wParam in (WM_SYSKEYDOWN, WM_SYSKEYUP)
                    )

                    # Win + V (without Ctrl or Shift or Alt)
                    if win_active and not ctrl_active and not shift_active and not alt_active:
                        if self.intercept_win_v:
                            self.hotkey_triggered.emit("Win+V")
                            return 1  # Suppress event from Windows shell

                    # Ctrl + Shift + V (without Win or Alt)
                    if ctrl_active and shift_active and not win_active and not alt_active:
                        if self.custom_hotkey_enabled:
                            self.hotkey_triggered.emit("Ctrl+Shift+V")
                            return 1  # Suppress event

                    # Alt + V or Ctrl + Alt + V -> Activate Input Box Quick Paste Dot & Row
                    if alt_active and not win_active and not shift_active:
                        self.hotkey_triggered.emit("QuickDot")
                        return 1  # Suppress event

                # Notify typing activity on non-modifier keys to dismiss floating dot
                if is_down and kb.vkCode not in (VK_LWIN, VK_RWIN, VK_CONTROL, 0xA2, 0xA3, VK_SHIFT, 0xA0, 0xA1, VK_MENU, 0x12, 0xA4, 0xA5):
                    self.user_typing.emit()
            except Exception as e:
                print(f"[Hotkey] Hook callback error: {e}")

        return user32.CallNextHookEx(self.hook_id, nCode, wParam, lParam)

    def _run_hook(self):
        self._thread_id = kernel32.GetCurrentThreadId()
        self._hook_proc_ref = HOOKPROC(self._low_level_handler)
        
        self.hook_id = user32.SetWindowsHookExW(
            WH_KEYBOARD_LL,
            self._hook_proc_ref,
            None,
            0
        )

        if not self.hook_id:
            err = kernel32.GetLastError()
            print(f"[Hotkey] Failed to install low-level keyboard hook! Error: {err}")
            return

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
