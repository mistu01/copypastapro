## 📋 Release Notes - Mistus Copy Pasta (v1.3.23)

### 📌 Independent Main Window (Up to 20) & Pill Bar Pinning
- **Main Window Pinning Up to 20**:
  - Expanded the main detailed window pinning capacity to support up to **20 pinned items** (configurable from 1 to 20 in Settings, default: 20).
  - Main window pinned slots and display comfortably hold up to 20 clippings with dedicated numbered slot tracking (`Slot #1` through `Slot #20`).
- **Completely Independent Pill Bar Display Pinning**:
  - Pill bar display pinning operates as a dedicated pinning mechanism (`is_pill_pinned`), completely separated from the main window's 20 slots.
  - **5+ Entries Enabled in Pill Bar** (`floating_bar_entry_count >= 5`): Allows pinning and displaying up to **2 items** directly in the pill bar.
  - **Less than 5 Entries Enabled in Pill Bar** (`floating_bar_entry_count < 5`): Allows pinning and displaying up to **1 item** directly in the pill bar.
  - Right-click any chip in the pill bar to Pin or Unpin directly.
  - Right-click any card in the main detailed window to Pin/Unpin from Main Window or Pin/Unpin from Pill Bar.
- **Static Entry Positioning on Paste**:
  - Selecting an entry from the pill bar to paste into any input field leaves chip positions 100% static and will never shuffle or jump.
