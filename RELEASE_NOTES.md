## 📋 Release Notes - Mistus Copy Pasta (v1.3.30)

### 🛠️ Detailed Menu Rendering & Layout Overlap Fix
- **Eliminated Overlapping Cards Bug**:
  - Fixed an issue where dynamically repopulating clipboard entries while updates were suppressed caused Qt layout recalculations to be delayed until the user scrolled.
  - Replaced update suppression with clean explicit widget disconnection (`setParent(None)` & `hide()`), synchronous layout recalculation (`layout.activate()`), and immediate geometry flushing (`sendPostedEvents`).
  - Cards now display immediately in their neat, smoothly spaced grid upon opening or refreshing with zero stutter or overlapping.

### 📌 Stable History Positioning on Paste
- **Fixed Item Reordering on Paste**:
  - Selecting and pasting an entry from the detailed clipboard window now preserves its original position in the list instead of bumping it to the top.
  - History is consistently ordered by item creation (`id DESC`), ensuring that your clippings stay exactly where you expect them to be.
