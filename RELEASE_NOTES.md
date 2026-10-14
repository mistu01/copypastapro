## 📋 Release Notes - Mistus Copy Pasta (v1.3.26)

### 🔄 Windows Native Clipboard Restoration (`Win + V`)
- **Restoration on Application Exit**: Exiting CopyPasta via system tray or closing the app automatically restores Windows 10/11 native `Win + V` clipboard history and broadcasts the update to Windows Explorer immediately.
- **Restoration on Uninstallation**: Uninstalling CopyPasta cleanly restores `EnableClipboardHistory` and removes any Explorer hotkey overrides, restoring Windows native clipboard functionality without requiring a reboot.

### 📌 Clean Tab Separation: Dedicated Pinned View
- The regular **Clipboard** tab now displays only recent unpinned clippings, removing duplicate pinned entries from the main view.
- Pinned clippings remain exclusively organized inside their dedicated **Pinned** tab (`Pinned (X/20)`).

### 🖥️ Windows 10 UI Clipping & Button Visibility Fix
- Fixed an issue where clipboard entries were clipped on Windows 10 causing Pin and Delete buttons to disappear.
- Action buttons are now anchored in a dedicated, fixed-width right-aligned container.
- Eliminated double layout padding and added soft-wrapping for long URLs and unbroken strings.

### ⚡ Performance, Stutter & Paste Stability
- **Lag-Free Mouse & Keyboard Hooks**: Replaced synchronous window hit-tests (`SendMessageTimeout`) in low-level hooks with instant non-blocking Win32 APIs, eliminating hook thread latency and mouse stutter.
- **Instant & Reliable Pasting**: Streamlined focus restoration with serialized paste execution, atomic modifier releases, and protected thread-input detaching across Windows 10 and Windows 11.
