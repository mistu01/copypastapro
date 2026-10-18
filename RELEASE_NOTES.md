## 📋 Release Notes - Mistus Copy Pasta (v1.3.27)

### 📌 Pinned Items Reordering (Pill Bar & Main Detailed Menu)
- **Reordering in Main Detailed Menu**:
  - Each pinned clipping card now features one-click **Up (`↑`)** and **Down (`↓`)** reordering buttons directly in the card action bar.
  - Right-click context menus on any pinned item now include **Move Up (Main Slot)** and **Move Down (Main Slot)** options for quick slot swapping.
- **Reordering in Floating Pill Bar**:
  - Pinned chips in the desktop floating bar can now be reordered via right-click context menu with **Move Left (earlier)** and **Move Right (later)** options.
  - Position changes update smoothly and immediately across both the pill bar and main detailed window.

### ⚡ Blazing-Fast Zero-Lag Performance
- **Zero-Lag Keyboard Hook**: Added a fast-path bypass for non-hotkey typing keys, eliminating Win32 kernel API round-trips for 99.9% of everyday keystrokes across the OS.
- **Batched UI Rendering**: Wrapped floating chip and clipboard card rebuilds in batched widget updates (`setUpdatesEnabled`), completely eliminating layout jitter and repainting overhead.
- **Optimized SQLite In-Memory Caching**: Enabled 8MB SQLite cache and in-memory temporary store pragmas for instantaneous history queries.
