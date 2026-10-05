# Mistus Copy Pasta

A fast, private, and modern Windows clipboard manager with built-in 2FA TOTP authenticator.

---

## Features

- **Win + V Flyout**: Replaces default Windows clipboard with a fast dark Fluent UI, real-time search, and auto-paste.
- **Quick Copy on Selection**: Select text anywhere and press **`C`** to copy without pressing `Ctrl + C`.
- **10 Pinned Slots**: Keep critical snippets permanently locked to top numbered slots.
- **2FA TOTP Authenticator**: Auto-detects 2FA keys, generates live codes, and encrypts secrets with Windows DPAPI.
- **Desktop Floating Bar**: Minimal edge-docked acrylic pill for one-click snippet pasting.

---

## Shortcuts

| Shortcut | Action |
| :--- | :--- |
| **`Win + V`** | Open Clipboard Manager flyout |
| **`Ctrl + Shift + V`** | Secondary shortcut to open flyout |
| **`C`** | Copy selected text (when selection badge is active) |
| **`Esc`** | Close flyout window |

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
