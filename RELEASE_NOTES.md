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
