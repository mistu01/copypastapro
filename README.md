# 📋 Mistus Copy Pasta (v1.3.6) - Next-Gen Windows Clipboard Manager & 2FA Authenticator

**Mistus Copy Pasta** is a modern Windows 11-styled software with a stunning **ZeBeyond Cyber-Emerald Midnight** dark theme designed to replace the default Windows Clipboard history (`Win + V`) with advanced productivity features:

- 🟢 **ZeBeyond Cyber-Emerald Theme**: Ultra-sleek obsidian and neon mint/emerald UI design inspired by top-tier modern SaaS interfaces.
- 🎯 **Input Field Quick Paste Dot (Hover Auto-Expand)**: When clicked into any input box or upon pressing `Alt + V`, a subtle dot menu appears. Simply **hover** over the dot to auto-expand the compact floating row of recent pastable clips without clicking; click any clip to directly paste it!
- ⌨️ **Caret Hotkey (`Alt + V` / `Ctrl + Alt + V`)**: Instantly summons the quick paste menu right at the active text caret/cursor in any application.
- 📌 **10 Pinned Entries on Top**: Pin up to 10 critical snippets with dedicated numbered slot badges (`#1` to `#10`), persistent across reboots and immune to history clearing.
- 🔑 **Built-in 2FA TOTP Authenticator**: Native time-based 2FA code generator secured with **Windows DPAPI** (hardware/user-account encryption), live countdown progress meters, and one-click paste into active apps.
- 🚀 **Desktop Floating Bar**: A sleek, draggable, translucent acrylic pill docked at your screen edge showing your recent clips as interactive quick chips, expandable to the detailed flyout with a single click.
- 🗖 **Detailed Flyout Window**: Compact Windows 11 Fluent flyout (similar to the native `Win + V` flyout, but with live search, 4 dedicated tabs, auto-paste, and flyout pin lock).
- ⌨️ **Global Shortcut Interceptor**: Intercepts `Win + V`, `Ctrl + Shift + V`, and `Alt + V` directly at the OS level.

---

## 📸 Key Features & Capabilities

### 1. Input Box Quick Paste Dot & Floating Row (v1.3.0)
- **Automatic Input Detection**: Detects clicks in editable text fields across Windows (Win32, Chromium, Firefox, Electron, WPF, and modern apps).
- **Subtle Floating Dot**: Appears right at the active input field without stealing focus or interrupting your typing.
- **Hover Auto-Expansion**: Hovering over the dot instantly expands the compact pastable entries menu without needing to click!
- **Compact & Sized Perfectly**: Slim, elegant horizontal pill (never overly big or intrusive) displaying the top 3-4 clips with clean preview text.
- **Instant Insertion**: Click any clip in the row to directly paste it into the active input box!
- **Caret Hotkey (`Alt + V`)**: Press `Alt + V` (or `Ctrl + Alt + V`) to summon the menu directly at your cursor anywhere in Windows.

### 2. Windows Key + V Interception & Custom Hotkeys
- **Native Hook (`WH_KEYBOARD_LL`)**: Intercepts `Win + V` directly at the OS level so Windows' built-in flyout is suppressed.
- **Secondary Shortcut**: Press `Ctrl + Shift + V` or use the system tray icon anytime.
- **Settings Toggle**: Easily toggle `Win + V` interception or `Ctrl + Shift + V` on or off in the Settings tab.

### 3. 10 Pinned Slots on Top
- Pin up to **10 items** permanently.
- Each pinned item receives an assigned slot number (`PIN #1` through `PIN #10`).
- Pinned items always stay at the top of the **📋 All** tab and have a dedicated **📌 Pinned (0/10)** tab.
- Protected against accidental bulk clearing.

### 4. Built-in 2FA TOTP Generator
- **RFC 6238 / RFC 4226 Compliant**: Supports 6-digit and 8-digit codes with standard 30s/60s intervals.
- **Auto-Detection**: Automatically detects copied 2FA secret keys from clipboard.
- **Windows DPAPI Security**: All secret keys are encrypted using Windows Data Protection API (`CryptProtectData`), securely bound to your Windows user account.
- **Live Animated Timer**: Real-time progress bar with color shifts.
- **One-Click Paste**: Click **Paste** on any 2FA card to instantly inject the code into your active browser or login field.
- **Quick Import**: Paste any standard `otpauth://totp/Service:user?secret=...` URI to auto-populate all fields.

### 5. Draggable Desktop Floating Bar
- Translucent acrylic pill docked near the screen edge.
- Shows your latest clipboard snippets as clickable chips.
- Click any chip to copy (and auto-paste into your current application).
- Drag by the grip to reposition anywhere on your desktop.
- Click `⤢` to open the full detailed flyout, or `─` to collapse the pill into a minimal floating bubble.
- Right-click menu for instant docking to bottom-right or top-right.

### 6. Detailed Flyout Window
- **Real-Time Search**: Instant search filtering across clipboard history, pinned items, and 2FA accounts.
- **Auto-Paste Focus Restoration**: Automatically switches focus back to your previous active window and synthesizes `Ctrl + V`.
- **Flyout Pin Lock (`📌 Pin Flyout`)**: Toggle between auto-closing on blur (like native Windows) or staying open during multi-item workflow tasks.
- **System Tray Icon**: Lives quietly in your Windows taskbar notification area with quick actions.

---

## 🚀 Installation & Running

### 📦 Windows Setup Installer (Recommended)
Download the latest Windows Setup wizard installer directly from GitHub Releases:
- 👉 **[Download Mistus Copy Pasta Latest Release](https://github.com/mistu01/copypastapro/releases)**

Features of the setup wizard:
1. **Welcome Screen & Branding**: Professional wizard sidebar graphic and branding.
2. **License Agreement & Software Info**: Terms and feature overview.
3. **Custom Installation Directory**: Defaults to `C:\Program Files\Mistus Copy Pasta` (with full Browse support).
4. **Start Menu Group**: Creates a Start Menu folder with app and documentation links.
5. **Desktop & Startup Shortcuts**: Checkboxes to create a desktop shortcut and auto-start Mistus Copy Pasta on Windows boot.
6. **Windows Run (`Win + R`) Command**: Registers `MistusCopyPasta.exe` so you can launch it from the Windows Run prompt.
7. **Complete Windows Uninstaller**: Registered in Windows Settings $\rightarrow$ Installed Apps with full removal cleanup.

### 🤖 Automated GitHub Actions Builds
Binaries and installers are compiled automatically in the cloud via GitHub Actions on every push and release tag:
- Builds a standalone executable using **PyInstaller**.
- Packages the installer with **Inno Setup**.
- Automatically attaches the compiled installer to the **GitHub Release**.

### 🐍 Developer / Source Code Mode
To run from source:
```bash
git clone https://github.com/mistu01/copypastapro.git
cd copypastapro
pip install -r requirements.txt
python main.py
```
Or simply double-click [`run.bat`](file:///c:/Users/Admin/Desktop/CopyPasta/run.bat) or [`run_silent.vbs`](file:///c:/Users/Admin/Desktop/CopyPasta/run_silent.vbs).

---

## 🛠️ Project Structure

```
CopyPasta/
├── app/
│   ├── database.py         # SQLite storage with 10-slot pinning & settings
│   ├── security.py         # Windows DPAPI encryption for 2FA secrets
│   ├── totp_manager.py     # RFC 6238 TOTP engine & URI parser
│   ├── hotkey.py           # Low-level Windows keyboard hook (Win+V / Ctrl+Shift+V)
│   ├── paste_helper.py     # Active window focus tracking & simulated Ctrl+V
│   ├── styles.py           # Windows 11 Fluent dark theme stylesheets
│   └── ui/
│       ├── detailed_window.py # Compact clipboard flyout (4 tabs, search, 10 pins, 2FA)
│       ├── floating_bar.py    # Draggable translucent desktop pill widget
│       ├── quick_dot.py       # Input box Quick Paste Dot & floating clip row
│       ├── totp_dialog.py     # Add / Edit 2FA account modal
│       └── toast.py           # In-app feedback toast notification
├── main.py                 # Application entry point, tray icon, single-instance mutex
├── requirements.txt        # PySide6, pywin32, pyotp, cryptography
├── run.bat                 # Standard Windows batch launcher
├── run_silent.vbs          # Silent background launcher
└── README.md               # Documentation & usage guide
```

---

## ⚙️ Configuration & Settings

Open the detailed flyout (`Win + V` or click `⤢` on the floating bar) and navigate to the **⚙️ Settings** tab:
- **Intercept Windows Key + V**: Toggle overriding the native Windows clipboard panel.
- **Enable secondary shortcut**: Toggle `Ctrl + Shift + V`.
- **Show desktop floating bar**: Toggle the floating pill widget.
- **Floating Bar Opacity**: Customize transparency (40% to 100%).
- **Auto-paste on click**: Automatically send `Ctrl + V` to target application when an item is selected.
- **Maximum history items**: Set history retention limit (50, 100, 200, 500).
- **Clear Unpinned History**: Purge unpinned items with one click while keeping pinned items safe.
