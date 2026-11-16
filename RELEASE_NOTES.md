## 📋 Release Notes - Mistus Copy Pasta (v1.3.34)

### 📌 Dynamic Clipboard History Movement on Paste
- **Pasted Entries Move to Latest in Detailed Clipboard**:
  - Whenever an entry is pasted into any target input box (from the detailed flyout window or desktop pill bar), it immediately moves to the latest (top) position in the main detailed clipboard (`Win + V`).
  - The desktop pill bar maintains its existing chip sequence during paste operations, preventing chips from shifting under the user's cursor while pasting multiple snippets.

### ⚡ Instant Top Positioning on Re-Copy
- **Existing Entries Move to Top of Detailed Menu & Pill Bar on Re-Copy**:
  - If any entry already stored in clipboard history is copied again (text selection, image, or file), its position dynamically updates so that it immediately appears at the top of the main detailed menu AND the desktop pill bar menu.
  - Features intelligent debounce logic to filter rapid duplicate OS notifications while recognizing deliberate re-copies of existing clippings.

### 🛡️ Rock-Solid Always-On-Top Floating Pill Bar (Windows 10 & 11)
- **Zero Hidden Pill Bar on Windows 10**:
  - Solved an issue where the desktop floating pill bar could sometimes slip underneath other application windows without being minimized.
  - Implemented Win32 `HWND_TOPMOST` z-order enforcement using `SetWindowPos` and `WS_EX_TOPMOST` / `WS_EX_NOACTIVATE` extended styles with `SWP_FRAMECHANGED`.
  - Added an active topmost watchdog to ensure the pill bar stays reliably floating above all other windows unless explicitly minimized to the system tray.

---

## 📋 Release Notes - Mistus Copy Pasta (v1.3.33)

### 📸 Optimized Screenshot Quality & Lightweight Output (Default Restored)
- **Restored Standard Original Quality by Default**:
  - Screenshot capture defaults to **Standard Quality** (1:1 native screen resolution with native display DPI and lightweight file compression).
  - Screenshots are now compact (~100 KB – 400 KB PNG) and can be shared instantly across Discord, Slack, email, web browsers, and chat without hitting file size limits.
- **Optimized High Quality (300 DPI Compact Mode)**:
  - Preserves exact 1:1 pixel dimensions while embedding standard 300 DPI density metadata (`11,811 dots per meter`).
  - Delivers true 300 DPI density for print, PDFs, and publishing without the massive file size explosion caused by previous supersampling.
- **Controlled Ultra HD Mode (1.5x Supersampling)**:
  - For 4K monitors and high-resolution presentation graphics, provides an optimized 1.5x supersampling factor with bicubic filtering while keeping file sizes lightweight (~1–2 MB).

### 🎛️ User-Friendly Quality Controls in Screenshot Frame & Settings
- **Action Bar Quick-Selector Button**:
  - Added a dedicated Quality indicator button directly on the screenshot action bar:
    - `⚡ Standard` (Emerald green): Fast sharing, compact file size *(Default)*.
    - `💎 High (300 DPI)` (Sky blue): 1:1 screen resolution with embedded 300 DPI print metadata.
    - `🚀 Ultra HD` (Amber): 1.5x supersampled graphics for high-resolution displays.
  - **Single Click**: Seamlessly cycles between Standard, High, and Ultra HD.
  - **Right-Click Context Menu**: Choose directly from a sleek Fluent popup menu with radio checks.
  - **Keyboard Shortcuts**: Press **`Q`** or **`D`** while taking a screenshot to immediately toggle quality modes.
  - **On-Screen Toast Badge**: Shows visual confirmation of the active mode and resolution description.
- **Detailed Settings Control**:
  - Added a new `Screenshot Quality` dropdown under Settings > Screen Capture with clear descriptions for all three modes.
  - Preferences persist across app restarts and automatically synchronize with the screenshot overlay.
