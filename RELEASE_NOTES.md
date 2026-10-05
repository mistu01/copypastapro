## 📋 Release Notes - Mistus Copy Pasta

### ✨ Features Added
- **Quick Copy on Text Selection ('C' key)**: Select any text on screen using your mouse or keyboard, and press **'C'** to copy directly without needing `Ctrl + C`. A non-intrusive interactive indicator appears at the selection for single-key copying.
- **Settings Toggle**: Added toggle under **Settings** $\rightarrow$ **Behavior & Pasting** to enable or disable Quick Copy on Selection anytime.

### 🛠️ Fixes & Improvements
- **Native 64-bit Installation**: Configured Inno Setup in 64-bit mode (`ArchitecturesInstallIn64BitMode=x64compatible`) so the application installs into `C:\Program Files\Mistus Copy Pasta` rather than `Program Files (x86)`.
- **Eliminated Keyboard Freeze in Browsers**: Completely removed synthetic Alt (`VK_MENU`) key generation, preventing Firefox address bars, WhatsApp, and Electron chat inputs from getting trapped in application menu bar mode.
- **Hardware Scan Code Simulation**: Injected keystrokes now resolve genuine OEM scan codes via `MapVirtualKeyW`, ensuring instant recognition in modern browser engines.
- **Cleaned UI Versioning**: Removed version clutter across tray tooltips and documentation.

### 🗑️ Features Dropped
- Input field dot menu completely removed.
