## 📋 Release Notes - Mistus Copy Pasta (v1.3.31)

### ⌨️ Native Windows Clipboard (Win + V) Instant Restoration
- **Zero Registry Tampering**:
  - Eliminated the registry modification anti-pattern (`DisabledHotkeys = "V"` and `EnableClipboardHistory = 0`). CopyPasta now intercepts `Win + V` strictly in-memory using low-level keyboard hooks (`WH_KEYBOARD_LL`).
  - Because Windows Explorer's registered hotkeys are never disabled in the registry, native Windows Clipboard (`Win + V`) works immediately without lag, reboots, or explorer restarts the instant CopyPasta exits or is uninstalled.
- **Automatic Repair of Existing Systems**:
  - Automatically cleans up any leftover `"V"` in `DisabledHotkeys` and ensures `EnableClipboardHistory = 1` across Windows 10 and 11.
- **Clean Installer & Uninstaller Lifecycle**:
  - Enhanced installer and uninstaller to cleanly terminate any running instances prior to install/uninstall, ensuring all keyboard hooks are instantly released and native clipboard functionality is 100% active.
