## 📋 Release Notes - Mistus Copy Pasta (v1.3.22)

### 📌 Dynamic Pinning in Desktop Pill Bar
- **Smart Capacity Rules**:
  - When **5+ entries** are enabled in the pill bar (`floating_bar_entry_count >= 5`), up to **2 pinned items** can be pinned and displayed directly at the front of the pill bar.
  - When **less than 5 entries** are enabled (`floating_bar_entry_count < 5`), up to **1 pinned item** can be pinned and displayed.
- **Right-Click Chip Context Menu**:
  - Right-click any chip in the desktop floating bar to access:
    - 📌 **Pin to Pill Bar** / **Unpin from Pill Bar**
    - 📋 **Copy & Paste**
    - 🗑️ **Delete Clipping**
  - Informative tooltips guide users if the pill bar pinning capacity for the current configuration has been reached.
- **Distinctive Visual Styling**:
  - Pinned items in the pill bar feature amber-gold glowing borders and badges (`FloatingChipPinned`) alongside the pin icon.

### 🔒 Stable Entry Positions on Paste
- **Static Chip Positioning**:
  - When an entry is selected from the pill bar to paste into any input field, its position in the pill bar remains 100% static and will **never shuffle or jump**.
  - Pill bar unpinned items are consistently ordered chronologically (`id DESC`), preserving exact user muscle memory while pasting.
