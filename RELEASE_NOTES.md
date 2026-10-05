## 📋 Release Notes - Mistus Copy Pasta (v1.3.11)

### 🛠️ Fixes & Improvements
- **Strict Text Selection Discrimination**: Filtered out false-positive quick copy toolbar popups during file drag-and-drop (File Explorer & Desktop), scrollbar interactions (Win32 & custom application scrollbars), context menu navigation, and non-text double-clicks.
- **Gesture & Chrome Verification**: Added multi-layer validation including non-client hit testing (`WM_NCHITTEST`), window control classification, and directional motion geometry to ensure the toolbar appears exclusively on genuine text selections.

### 🗑️ Features Dropped
- Input field dot menu completely removed.
