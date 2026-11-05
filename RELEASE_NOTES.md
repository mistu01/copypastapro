## 📋 Release Notes - Mistus Copy Pasta (v1.3.32)

### 📸 High-Definition Screenshot Engine (300 DPI)
- **High-Resolution 300 DPI Quality**:
  - All screenshots are captured and exported with a minimum of **300 DPI** metadata (`11,811 dots per meter`), meeting professional print and publishing density standards.
  - Added **300 DPI Ultra Mode** (super-sampled with bicubic smooth transformation) and **300 DPI Native Mode** (1:1 screen pixels with 300 DPI density).
  - Annotations (text, arrows, rectangles, pens) are scaled and rasterized vector-sharp directly on the high-DPI canvas.
  - Both PNG and JPEG formats are saved at 100% maximum quality with zero compression artifacts.
  - Quick toggle button on the screenshot action bar (`[✨ 300 DPI]`) and in Settings.

### ⏹️ Square / Rectangle Indicator Fill Option
- **Interactive Fill Modes**:
  - Added dedicated Fill option button directly on the annotation toolbar under the Square indicator.
  - Cycle through 3 fill modes via click, right-click, or pressing the **`F`** key:
    - **Outline Only**: Classic hollow rectangle border.
    - **Translucent Fill**: ~28% opacity tinted fill for highlighting text and interface elements.
    - **Solid Fill**: 100% opaque block for censoring, masking, or redacting sensitive data.
  - Live drawing preview immediately reflects the selected fill mode and active palette color.
  - Overlay status badges provide instant on-screen feedback when toggling fill modes or DPI settings.
