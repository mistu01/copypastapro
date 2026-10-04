"""
Active foreground window tracker and reliable simulated paste injector.
Continuously tracks the user's active application window and directly inserts
text into whatever input field was selected.
"""

import time
import os
import threading
import ctypes
from typing import Optional

try:
    import win32gui
    import win32process
    import win32clipboard
    import win32con
    HAS_WIN32 = True
except ImportError:
    HAS_WIN32 = False

user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32

VK_LWIN = 0x5B
VK_RWIN = 0x5C
VK_CONTROL = 0x11
VK_SHIFT = 0x10
VK_MENU = 0x12  # Alt
VK_V = 0x56
KEYEVENTF_KEYUP = 0x0002
SW_RESTORE = 9
SW_SHOW = 5


class PasteHelper:
    def __init__(self):
        self.last_foreground_hwnd: Optional[int] = None
        self.our_pid = os.getpid()
        self._running = True
        self._tracker_thread = threading.Thread(target=self._track_foreground, daemon=True)
        self._tracker_thread.start()

    def _track_foreground(self):
        """Continuously monitor active foreground window in background."""
        while self._running:
            try:
                if HAS_WIN32:
                    hwnd = win32gui.GetForegroundWindow()
                    if hwnd and win32gui.IsWindow(hwnd):
                        _, pid = win32process.GetWindowThreadProcessId(hwnd)
                        # Only record external windows (not our own)
                        if pid != self.our_pid:
                            self.last_foreground_hwnd = hwnd
            except Exception:
                pass
            time.sleep(0.06)

    def capture_foreground_window(self) -> Optional[int]:
        """Explicit snapshot of current external foreground window."""
        if HAS_WIN32:
            try:
                hwnd = win32gui.GetForegroundWindow()
                if hwnd and win32gui.IsWindow(hwnd):
                    _, pid = win32process.GetWindowThreadProcessId(hwnd)
                    if pid != self.our_pid:
                        self.last_foreground_hwnd = hwnd
                        return hwnd
            except Exception:
                pass
        return self.last_foreground_hwnd

    def set_clipboard_text(self, text: str):
        """
        Set clipboard text safely. Uses Qt clipboard when available,
        or Win32 direct API as fallback without racing or clearing.
        """
        self.last_copied_text = text

        # 1. Update via Qt clipboard if available
        try:
            from PySide6.QtWidgets import QApplication
            from PySide6.QtGui import QClipboard
            app = QApplication.instance()
            if app:
                clip = app.clipboard()
                if clip:
                    clip.setText(text, QClipboard.Clipboard)
                    return
        except Exception:
            pass

        # 2. Update via Win32 direct API fallback
        if HAS_WIN32:
            for _ in range(5):
                try:
                    win32clipboard.OpenClipboard()
                    win32clipboard.EmptyClipboard()
                    win32clipboard.SetClipboardText(text, win32con.CF_UNICODETEXT)
                    win32clipboard.CloseClipboard()
                    break
                except Exception:
                    time.sleep(0.01)

    def restore_focus_and_paste(self, target_hwnd: Optional[int] = None):
        """
        Restore focus to the target window with the selected input field
        and directly insert text via Ctrl+V.
        """
        hwnd_to_restore = target_hwnd or self.last_foreground_hwnd
        threading.Thread(
            target=self._do_restore_and_paste,
            args=(hwnd_to_restore,),
            daemon=True
        ).start()

    def _do_restore_and_paste(self, target_hwnd: Optional[int]):
        # Brief pause to allow the flyout to finish hiding if called from DetailedWindow
        time.sleep(0.04)

        current_fore = user32.GetForegroundWindow()
        hwnd_to_use = target_hwnd or current_fore or self.last_foreground_hwnd

        # Only bring to foreground if target is not already the foreground window
        if hwnd_to_use and HAS_WIN32 and win32gui.IsWindow(hwnd_to_use):
            if current_fore != hwnd_to_use:
                self._force_window_to_foreground(hwnd_to_use)
                time.sleep(0.05)

        # Send simulated Ctrl+V with hardware scan codes
        self._simulate_ctrl_v()

    def _force_window_to_foreground(self, target_hwnd: int):
        """
        Clean Win32 foreground activation that preserves input cursor focus.
        Uses AttachThreadInput without synthesizing any Alt keystrokes,
        preventing Firefox, WhatsApp, or other apps from entering the menu bar.
        """
        try:
            if not target_hwnd or not win32gui.IsWindow(target_hwnd):
                return

            fore_hwnd = user32.GetForegroundWindow()
            if fore_hwnd == target_hwnd:
                return

            if user32.IsIconic(target_hwnd):
                user32.ShowWindow(target_hwnd, SW_RESTORE)

            cur_thread = kernel32.GetCurrentThreadId()
            fore_thread = user32.GetWindowThreadProcessId(fore_hwnd, None) if fore_hwnd else 0
            target_thread = user32.GetWindowThreadProcessId(target_hwnd, None)

            # Temporarily attach thread inputs to gain foreground permission cleanly
            if fore_thread and fore_thread != cur_thread:
                user32.AttachThreadInput(cur_thread, fore_thread, True)
            if target_thread and target_thread != cur_thread:
                user32.AttachThreadInput(cur_thread, target_thread, True)

            user32.AllowSetForegroundWindow(-1)
            user32.BringWindowToTop(target_hwnd)
            user32.SetForegroundWindow(target_hwnd)

            # Detach thread input
            if target_thread and target_thread != cur_thread:
                user32.AttachThreadInput(cur_thread, target_thread, False)
            if fore_thread and fore_thread != cur_thread:
                user32.AttachThreadInput(cur_thread, fore_thread, False)
        except Exception as e:
            print(f"[PasteHelper] Error forcing foreground: {e}")

    def _simulate_ctrl_v(self):
        """Send simulated Ctrl+V keystroke with OEM hardware scan codes into input field."""
        try:
            # Release modifier keys ONLY if they are physically held down
            for vk in (VK_LWIN, VK_RWIN, VK_SHIFT, VK_MENU):
                if user32.GetAsyncKeyState(vk) & 0x8000:
                    user32.keybd_event(vk, 0, KEYEVENTF_KEYUP, 0)

            time.sleep(0.01)

            scan_ctrl = user32.MapVirtualKeyW(VK_CONTROL, 0)
            scan_v = user32.MapVirtualKeyW(VK_V, 0)

            # Press Ctrl
            user32.keybd_event(VK_CONTROL, scan_ctrl, 0, 0)
            time.sleep(0.015)

            # Press V
            user32.keybd_event(VK_V, scan_v, 0, 0)
            time.sleep(0.02)

            # Release V
            user32.keybd_event(VK_V, scan_v, KEYEVENTF_KEYUP, 0)
            time.sleep(0.015)

            # Release Ctrl
            user32.keybd_event(VK_CONTROL, scan_ctrl, KEYEVENTF_KEYUP, 0)
        except Exception as e:
            print(f"[PasteHelper] Error simulating Ctrl+V: {e}")
