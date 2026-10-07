## 📋 Release Notes - Mistus Copy Pasta (v1.3.20)

### ⚡ Streamlined Setup & Clean Installation Experience
- **Removed Redundant Setup Information Page**: Eliminated the intermediary feature/information page from the Windows installer wizard, creating a fast, friction-free installation flow.
- **Clean Post-Install Finish Screen**: Removed the "View Readme" checkbox from the setup completion screen so users are only presented with the direct "Launch Mistus Copy Pasta" action.
- **Updated Comprehensive Documentation**:
  - Fully refreshed `INFO.txt` and `README.md` reflecting the latest features: Lightshot-style screenshot capture suite (`PrintScreen`), multi-format image clipboard copy/paste, desktop dynamic island & compact pill with 1-click minimize to tray, selection quick copy ('C'), and contextual system tray activation.

## 📋 Release Notes - Mistus Copy Pasta (v1.3.19)

### 🖱️ Contextual System Tray Activation
- **Smart System Tray Icon Click**:
  - When the Desktop Pill Bar is minimized to the system tray, clicking (or double-clicking) the system tray icon immediately **restores the Pill Bar** to the desktop at its exact saved coordinates.
  - When the Desktop Pill Bar is active and visible on screen, clicking the system tray icon **opens / restores the Full Detailed Manager** (`Win + V` flyout) to the foreground.
- **Flawless Focus & Window Restoration**: Brings the Detailed Manager directly to the front if backgrounded, or toggles it cleanly when clicked while in focus.
- **Seamless State Sync**: Restoring the Pill Bar via the system tray icon automatically updates all tray menus, database settings, and settings tab toggles.

## 📋 Release Notes - Mistus Copy Pasta (v1.3.18)

### 📥 Minimize Compact Pill Display to System Tray
- **Dedicated Minimize to Tray Button**: Added a dedicated minimize button (`-` minus icon) directly on the compact pill display and floating bar, allowing instant 1-click minimization to the Windows system tray.
- **Persistent Mode Memory**: Remembers whether the floating bar was collapsed into the compact pill or expanded to the full bar, seamlessly restoring in the preferred mode.
- **Right-Click Context Menu Options**: Right-clicking the compact pill or floating bar provides direct options to "Minimize to System Tray" as well as toggle between "Collapse to Compact Pill" and "Expand to Floating Bar".
- **Dynamic System Tray Context Menu**:
  - Automatically reflects state: dynamically shows **"Minimize Desktop Bar to Tray"** when visible, and **"Show Desktop Bar / Island"** when minimized.
  - One-click restoration from system tray icon context menu anytime.
- **Friendly Windows Tray Notification**: Displays a desktop notification upon minimization confirming that the island is safely residing in the system tray and showing how to restore it.
- **Settings Tab Synchronization**: Opening the Settings tab automatically syncs the "Show desktop floating bar" checkbox with the live state.

## 📋 Release Notes - Mistus Copy Pasta (v1.3.17)

### 📸 Screenshot Direct Clipboard History Integration & UI Polish
- **Instant Clipboard Entry on Copy**: Capturing a screenshot via the **Copy** button (or `Enter` / `Ctrl + C` / double-click) instantly adds the screenshot directly into the clipboard manager history as a regular entry with a thumbnail preview, dimensions (`W × H px`), and format tag.
- **Copy Button Prominently Positioned Beside Save**: The Lightshot-style floating action bar features a prominent Cyber-Emerald **Copy** button placed right beside **Save**, with clear vector icons and tooltips.
- **Save to History on Save**: Saving a screenshot to a file now also automatically registers it in CopyPasta's history for effortless instant re-pasting.
- **Omnipresent Screenshot Shortcuts**:
  - Dedicated global **PrintScreen** (`PrtScn`) key interception.
  - New **"Snipping"** camera button in the Detailed Window header.
  - New **"Take Screenshot (PrtScn)"** action in Desktop Floating Bar right-click menu.
  - Quick action in System Tray menu.

## 📋 Release Notes - Mistus Copy Pasta (v1.3.16)

### 🖼️ Full Image & Image File Clipboard Copy / Paste Support
- **Support for All Known Image Formats**: Seamlessly capture and paste all image formats supported by Windows Clipboard:
  - Raw clipboard image data: screenshots (Lightshot tool, Win+Shift+S, PrtScn), browser right-click "Copy Image", graphics apps (Paint, Photoshop, GIMP, etc.).
  - Copied image files in Windows Explorer: `.png`, `.jpg`, `.jpeg`, `.bmp`, `.gif`, `.webp`, `.tiff`, `.ico`, `.svg`, `.jfif`, `.avif`.
- **Rich Thumbnail Card in Detailed Window**:
  - Crisp High-DPI thumbnail preview with subtle rounded border and aspect ratio preservation.
  - Metadata badges: `IMAGE` pill, dimensions (`W × H px`), format tag, file size (`KB` / `MB`), and source file name.
  - Pinning support (up to 10 pinned image slots) and deletion with automatic media cleanup.
- **Full Windows App Paste Compatibility**:
  - Pasting an image entry populates **Native Image (CF_DIB / CF_DIBV5)**, **raw `image/png` MIME bytes**, and **File URLs**.
  - Flawlessly pastes into Discord, Slack, WhatsApp, Telegram, Microsoft Word/Office, Photoshop, Paint, Web Browsers, and Windows File Explorer.
- **Desktop Floating Bar Image Chips**:
  - Displays quick image chips with image icon, filename or dimensions, and dimensions tooltip.
  - Single-click quick paste directly from the floating bar.
- **Deterministic Hashing & Smart Media Cache**:
  - Image files cached safely in `%APPDATA%/CopyPasta/media/` with SHA-256 deduplication to prevent database bloat.
  - Automatic cleanup when history is trimmed or items are deleted.

## 📋 Release Notes - Mistus Copy Pasta (v1.3.15)

### 📸 Lightshot-Style Screenshot Capture Tool
- **Dedicated PrintScreen Key Interception**: Globally captures the `PrintScreen` (`PrtScn`) key, suppressing the default OS flash and launching the high-performance snipping overlay instantly.
- **Multi-Monitor Virtual Desktop Capture**: Seamlessly snapshots across single or multiple monitors at crisp High-DPI resolution.
- **Interactive Region Selection**: Drag to select any rectangle, with live `W × H px` dimensions badge and 8-point corner/edge resize handles. Drag inside the box to reposition.
- **Full Annotation Suite**:
  - ✏️ **Pen**: Smooth freehand drawing.
  - 🖌️ **Highlighter / Marker**: Semi-transparent color highlighting.
  - 📏 **Line & Arrow**: Straight guide lines and vector directional arrows with arrowheads.
  - 🔲 **Rectangle**: Crisp bounding box frames.
  - 🔤 **Text**: Click to place in-place typography boxes.
  - 🎨 **Palette & Undo**: Instant color cycling and `Ctrl + Z` undo support.
- **Instant Actions**:
  - **Copy to Clipboard** (`Enter`, `Ctrl + C`, or double-click selection) to copy with toast feedback.
  - **Save to File** (`Ctrl + S`) with timestamped filename.
  - **Cancel** (`Esc`).
- **Tray & Settings Integration**: Added "Take Screenshot (PrtScn)" in tray menu and a toggle in Settings.

### 🛠️ UI & Usability Enhancements
- **Thicker Scrollbar**: Widened the vertical scrollbar in the main detailed window to 10px with smooth rounded track and high-contrast Cyber-Emerald grips for easy mouse grabbing.
- **Movable Detailed Window**: Holding and dragging the top header title bar now smoothly moves the main detailed flyout window anywhere on your screen.
- **2FA Dismiss Cross in Minimized Pill**: Added a dismiss cross (`×`) button in the minimized floating island 2FA chip display to quickly dismiss the active 2FA code without opening the full flyout.
