# Mistus Copy Pasta

A fast, private, and modern Windows clipboard manager, Lightshot-style screenshot capture suite, and 2FA TOTP authenticator.

---

## Features

- **Win + V Flyout**: Replaces default Windows clipboard with a fast dark Fluent UI, real-time search, and auto-paste.
- **📸 Lightshot-Style Screenshot Suite**: Dedicated `PrintScreen` (PrtScn) key capture with interactive rectangle selection, pen/arrow/rectangle/text/highlighter annotations, and instant copy directly to clipboard & history.
- **🖼️ Multi-Format Image Support**: Full copy & paste support for all image formats (`.png`, `.jpg`, `.bmp`, `.gif`, `.webp`, `.tiff`, `.ico`, etc.) with thumbnail previews, dimensions badges, and file metadata.
- **⚡ Quick Copy on Selection**: Select text anywhere and press **`C`** to copy without pressing `Ctrl + C`.
- **📌 10 Pinned Slots**: Keep critical snippets and images permanently locked to top numbered slots.
- **🔑 2FA TOTP Authenticator**: Auto-detects 2FA keys, generates live codes, and encrypts secrets with Windows DPAPI.
- **🚀 Desktop Floating Island & Compact Pill**: Minimal edge-docked acrylic pill for one-click snippet pasting, live 2FA counter, and 1-click minimize to system tray.
- **🖱️ Smart System Tray Integration**: Click tray icon to restore the pill bar when minimized, or open the full clipboard manager when active.

---

## Shortcuts

| Shortcut | Action |
| :--- | :--- |
| **`Win + V`** | Open Clipboard Manager flyout |
| **`Ctrl + Shift + V`** | Secondary shortcut to open flyout |
| **`PrintScreen`** (`PrtScn`) | Take screenshot with annotation & copy suite |
| **`C`** | Copy selected text (when selection badge is active) |
| **`Esc`** | Close flyout window or screenshot overlay |

---

## Download & Installation

Download the latest installer from [GitHub Releases](https://github.com/mistu01/copypastapro/releases).

---

## Development

```bash
git clone https://github.com/mistu01/copypastapro.git
cd copypastapro
pip install -r requirements.txt
python main.py
```

---

## Code Signing

Free code signing provided by [SignPath.io](https://signpath.io), certificate by [SignPath Foundation](https://signpath.org). See [Code Signing Policy](CODE_SIGNING_POLICY.md).

## License

[MIT License](LICENSE.txt)
