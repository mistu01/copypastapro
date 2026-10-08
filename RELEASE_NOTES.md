## 📋 Release Notes - Mistus Copy Pasta (v1.3.24)

### 📌 Fixed Pill Bar Entry Context Menu & Pin Options
- **Direct Chip Right-Click Handling**:
  - Resolved an event-bubbling issue where right-clicking an entry in the desktop pill bar was opening the general floating bar context menu instead of the clipping's action menu.
  - Right-clicking any chip button in the pill bar now directly and reliably displays the clipping context menu with:
    - 📌 **Pin to Pill Bar** / **Unpin from Pill Bar**
    - 📌 **Pin to Main Window (up to 20)** / **Unpin from Main Window**
    - 📋 **Copy & Paste**
    - 🗑️ **Delete Clipping**
- **Independent Pinning Rules Enforced**:
  - **5+ Entries Enabled in Pill Bar** (`floating_bar_entry_count >= 5`): Allows pinning up to **2 items** directly in the pill bar.
  - **Less than 5 Entries Enabled in Pill Bar** (`floating_bar_entry_count < 5`): Allows pinning up to **1 item** directly in the pill bar.
  - Main window pinned clippings support up to **20 slots** independently.
- **Static Positions on Paste**:
  - Selecting an entry from the pill bar to paste into any input field keeps chip positions 100% static and will never shuffle or jump.
