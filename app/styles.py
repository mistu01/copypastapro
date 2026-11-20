"""
Neobrutalist Design System for Mistus Copy Pasta.
Features high-contrast geometry, bold 2px/2.5px solid black borders,
chunky hard-edged drop shadows, tactile physical button presses,
vibrant electric accents (Lemon Yellow #FFE600, Neon Mint #00F59B,
Cyber Cyan #38BDF8, Hot Coral #FF4757), and clean crisp typography.
"""

DARK_THEME_QSS = """
/* Global Window & Font Settings */
QWidget {
    font-family: "Segoe UI", -apple-system, BlinkMacSystemFont, "Inter", system-ui, sans-serif;
    color: #F8FAFC;
    background-color: transparent;
    font-size: 13px;
    selection-background-color: #FFE600;
    selection-color: #000000;
}

/* Detailed Flyout Window Background */
#DetailedWindow, #FlyoutContainer {
    background-color: #121316;
    border: 2.5px solid #000000;
    border-radius: 12px;
}

/* Floating Bar Container - Chunky Neobrutalist Pill */
#FloatingBarContainer {
    background-color: #121316;
    border: 2.5px solid #000000;
    border-bottom: 4px solid #000000;
    border-right: 4px solid #000000;
    border-radius: 14px;
}

#FloatingBarContainer:hover {
    background-color: #17181D;
    border-color: #000000;
    border-bottom: 4.5px solid #000000;
    border-right: 4.5px solid #000000;
}

/* Minimized Floating Island Container */
#MinimizedFloatingContainer {
    background-color: #121316;
    border: 2.5px solid #000000;
    border-bottom: 4px solid #000000;
    border-right: 4px solid #000000;
    border-radius: 14px;
}

/* Header Area */
#HeaderBar {
    border-bottom: 2.5px solid #000000;
    padding: 2px 4px 8px 4px;
}

/* Search Bar - Neobrutalist Inset Input */
QLineEdit#SearchBar {
    background-color: #18191F;
    border: 2px solid #000000;
    border-bottom: 4px solid #000000;
    border-right: 4px solid #000000;
    border-radius: 8px;
    padding: 8px 14px;
    color: #FFFFFF;
    font-size: 13px;
    font-weight: 600;
}

QLineEdit#SearchBar:hover {
    background-color: #1E2028;
    border-color: #000000;
}

QLineEdit#SearchBar:focus {
    background-color: #22252E;
    border: 2px solid #FFE600;
    border-bottom: 4px solid #FFE600;
    border-right: 4px solid #FFE600;
    color: #FFFFFF;
}

/* Segmented Tab Bar Container */
#TabBarContainer {
    background-color: #16171D;
    border: 2px solid #000000;
    border-radius: 9px;
    padding: 4px;
}

/* Neobrutalist Segmented Nav Tabs */
QPushButton.NavTab {
    background-color: #1E2027;
    border: 1.5px solid #000000;
    border-bottom: 3px solid #000000;
    border-right: 3px solid #000000;
    border-radius: 6px;
    padding: 6px 10px;
    color: #CBD5E1;
    font-weight: 700;
    font-size: 12px;
}

QPushButton.NavTab:hover {
    background-color: #282B35;
    color: #FFFFFF;
    border-bottom: 3.5px solid #000000;
    border-right: 3.5px solid #000000;
}

QPushButton.NavTab:checked {
    background-color: #FFE600;
    border: 2px solid #000000;
    border-bottom: 3.5px solid #000000;
    border-right: 3.5px solid #000000;
    color: #000000;
    font-weight: 800;
}

/* Action Icon Buttons - Chunky & Tactile */
QPushButton.IconButton {
    background-color: #1E2027;
    border: 1.5px solid #000000;
    border-bottom: 2.5px solid #000000;
    border-right: 2.5px solid #000000;
    border-radius: 6px;
    padding: 4px;
    color: #CBD5E1;
}

QPushButton.IconButton:hover {
    background-color: #2C303B;
    color: #FFE600;
    border-color: #000000;
    border-bottom: 3px solid #000000;
    border-right: 3px solid #000000;
}

QPushButton.IconButton:pressed {
    background-color: #FFE600;
    color: #000000;
    border: 1.5px solid #000000;
    margin-top: 1px;
    margin-left: 1px;
}

/* Primary Action Button - Electric Lemon Yellow */
QPushButton.PrimaryButton, QPushButton[class="PrimaryButton"] {
    background-color: #FFE600;
    border: 2px solid #000000;
    border-bottom: 4px solid #000000;
    border-right: 4px solid #000000;
    border-radius: 7px;
    color: #000000;
    font-weight: 800;
    padding: 7px 16px;
    font-size: 12px;
    letter-spacing: 0.3px;
}

QPushButton.PrimaryButton:hover, QPushButton[class="PrimaryButton"]:hover {
    background-color: #FFF04D;
    border-bottom: 5px solid #000000;
    border-right: 5px solid #000000;
    color: #000000;
}

QPushButton.PrimaryButton:pressed, QPushButton[class="PrimaryButton"]:pressed {
    border: 2px solid #000000;
    margin-top: 2px;
    margin-left: 2px;
}

/* Success Button - Neon Mint Green */
QPushButton.SuccessButton, QPushButton[class="SuccessButton"] {
    background-color: #00F59B;
    border: 2px solid #000000;
    border-bottom: 4px solid #000000;
    border-right: 4px solid #000000;
    border-radius: 7px;
    color: #000000;
    font-weight: 800;
    padding: 7px 16px;
    font-size: 12px;
    letter-spacing: 0.3px;
}

QPushButton.SuccessButton:hover, QPushButton[class="SuccessButton"]:hover {
    background-color: #38FFB4;
    border-bottom: 5px solid #000000;
    border-right: 5px solid #000000;
    color: #000000;
}

QPushButton.SuccessButton:pressed, QPushButton[class="SuccessButton"]:pressed {
    border: 2px solid #000000;
    margin-top: 2px;
    margin-left: 2px;
}

/* Secondary Button - Brutalist Slate */
QPushButton.SecondaryButton, QPushButton[class="SecondaryButton"] {
    background-color: #242731;
    border: 2px solid #000000;
    border-bottom: 3.5px solid #000000;
    border-right: 3.5px solid #000000;
    border-radius: 7px;
    color: #F8FAFC;
    padding: 7px 14px;
    font-size: 12px;
    font-weight: 700;
}

QPushButton.SecondaryButton:hover, QPushButton[class="SecondaryButton"]:hover {
    background-color: #2F3340;
    color: #FFFFFF;
    border-bottom: 4.5px solid #000000;
    border-right: 4.5px solid #000000;
}

QPushButton.SecondaryButton:pressed, QPushButton[class="SecondaryButton"]:pressed {
    border: 2px solid #000000;
    margin-top: 2px;
    margin-left: 2px;
}

/* Danger Button - Hot Coral Red */
QPushButton.DangerButton, QPushButton[class="DangerButton"] {
    background-color: #FF4757;
    border: 2px solid #000000;
    border-bottom: 4px solid #000000;
    border-right: 4px solid #000000;
    border-radius: 7px;
    color: #FFFFFF;
    font-weight: 800;
    padding: 7px 14px;
    font-size: 12px;
}

QPushButton.DangerButton:hover {
    background-color: #FF6B81;
}

QPushButton.DangerButton:pressed {
    border: 2px solid #000000;
    margin-top: 2px;
    margin-left: 2px;
}

/* Clipboard History Card - High Contrast Neobrutalist Block */
QFrame.ClipboardCard {
    background-color: #1A1C23;
    border: 2px solid #000000;
    border-bottom: 4px solid #000000;
    border-right: 4px solid #000000;
    border-radius: 8px;
}

QFrame.ClipboardCard:hover {
    background-color: #22252E;
    border-color: #000000;
    border-bottom: 5px solid #000000;
    border-right: 5px solid #000000;
}

/* Pinned Clipboard Card - High-Contrast Neobrutalist Block with Lemon Yellow Accent */
QFrame.PinnedCard {
    background-color: #211F16;
    border: 2px solid #000000;
    border-bottom: 4px solid #000000;
    border-right: 4px solid #000000;
    border-left: 5px solid #FFE600;
    border-radius: 8px;
}

QFrame.PinnedCard:hover {
    background-color: #2A271B;
    border: 2px solid #000000;
    border-bottom: 5px solid #000000;
    border-right: 5px solid #000000;
    border-left: 5px solid #FFF04D;
}

/* Empty Pinned Slot Drop Frame */
QFrame.EmptySlotFrame {
    background-color: #16171D;
    border: 2px dashed #3E4352;
    border-radius: 8px;
}

/* Badges - Bold High-Contrast Neobrutalist Tags with Solid Black Borders */
.PinSlotBadge, QFrame.PinSlotBadge, QLabel.PinSlotBadge {
    background-color: #FFE600;
    color: #000000;
    font-weight: 800;
    font-size: 10px;
    border: 1.5px solid #000000;
    border-radius: 4px;
    padding: 2px 7px;
    letter-spacing: 0.5px;
}

.EntryIndexBadge, QFrame.EntryIndexBadge, QLabel.EntryIndexBadge {
    background-color: #38BDF8;
    color: #000000;
    font-weight: 800;
    font-size: 10px;
    border: 1.5px solid #000000;
    border-radius: 4px;
    padding: 2px 6px;
    letter-spacing: 0.3px;
}

/* Content Type Pill Badges */
.TypeBadgeUrl, QFrame.TypeBadgeUrl, QLabel.TypeBadgeUrl {
    background-color: #00F59B;
    border: 1.5px solid #000000;
    color: #000000;
    font-weight: 800;
    font-size: 10px;
    border-radius: 4px;
    padding: 2px 6px;
}

.TypeBadgeCode, QFrame.TypeBadgeCode, QLabel.TypeBadgeCode {
    background-color: #C084FC;
    border: 1.5px solid #000000;
    color: #000000;
    font-weight: 800;
    font-size: 10px;
    border-radius: 4px;
    padding: 2px 6px;
}

.TypeBadgeEmail, QFrame.TypeBadgeEmail, QLabel.TypeBadgeEmail {
    background-color: #FB923C;
    border: 1.5px solid #000000;
    color: #000000;
    font-weight: 800;
    font-size: 10px;
    border-radius: 4px;
    padding: 2px 6px;
}

.TypeBadgeText, QFrame.TypeBadgeText, QLabel.TypeBadgeText {
    background-color: #E2E8F0;
    border: 1.5px solid #000000;
    color: #000000;
    font-weight: 800;
    font-size: 10px;
    border-radius: 4px;
    padding: 2px 6px;
}

.TypeBadgeImage, QFrame.TypeBadgeImage, QLabel.TypeBadgeImage {
    background-color: #38BDF8;
    border: 1.5px solid #000000;
    color: #000000;
    font-weight: 800;
    font-size: 10px;
    border-radius: 4px;
    padding: 2px 6px;
}

QLabel.ImageThumbnail {
    border: 2px solid #000000;
    border-radius: 6px;
    background-color: #121316;
    padding: 2px;
}

/* Active 2FA Hero Card */
QFrame#ActiveTotpHeroCard {
    background-color: #161A24;
    border: 2.5px solid #000000;
    border-bottom: 5px solid #000000;
    border-right: 5px solid #000000;
    border-radius: 10px;
    padding: 14px 16px;
}

/* 2FA Code Display */
QLabel.TotpCodeHero {
    font-family: "Segoe UI", Arial, sans-serif;
    font-size: 28px;
    font-weight: 800;
    color: #FFE600;
    letter-spacing: 5px;
    padding: 4px 0;
}

QLabel.TotpCodeLabel {
    font-family: "Segoe UI", Arial, sans-serif;
    font-size: 20px;
    font-weight: 800;
    color: #00F59B;
    letter-spacing: 2px;
}

/* Section Header Labels */
QLabel.SectionHeader {
    color: #FFE600;
    font-size: 11px;
    font-weight: 800;
    letter-spacing: 1.2px;
    text-transform: uppercase;
    padding: 6px 2px 4px 2px;
}

/* Floating Bar Snippet Chips - Tactile Neobrutalist Buttons */
QPushButton.FloatingChip {
    background-color: #1E2027;
    border: 1.5px solid #000000;
    border-bottom: 3px solid #000000;
    border-right: 3px solid #000000;
    border-radius: 6px;
    color: #F8FAFC;
    font-size: 12px;
    font-weight: 600;
    padding: 4px 11px;
    text-align: left;
}

QPushButton.FloatingChip:hover {
    background-color: #292D38;
    color: #FFE600;
    border-bottom: 3.5px solid #000000;
    border-right: 3.5px solid #000000;
}

QPushButton.FloatingChip:pressed {
    border: 1.5px solid #000000;
    margin-top: 1px;
    margin-left: 1px;
}

QPushButton.FloatingChipPinned {
    background-color: #FFE600;
    border: 1.5px solid #000000;
    border-bottom: 3px solid #000000;
    border-right: 3px solid #000000;
    border-radius: 6px;
    color: #000000;
    font-size: 12px;
    font-weight: 800;
    padding: 4px 11px;
    text-align: left;
}

QPushButton.FloatingChipPinned:hover {
    background-color: #FFF04D;
    border-bottom: 3.5px solid #000000;
    border-right: 3.5px solid #000000;
}

QPushButton.FloatingChipPinned:pressed {
    border: 1.5px solid #000000;
    margin-top: 1px;
    margin-left: 1px;
}

/* Floating Bar 2FA Live Chip Container */
QFrame#FloatingTotpContainer {
    background-color: #00F59B;
    border: 1.5px solid #000000;
    border-bottom: 3px solid #000000;
    border-right: 3px solid #000000;
    border-radius: 6px;
}

QPushButton#FloatingTotpInnerBtn {
    background: transparent;
    border: none;
    color: #000000;
    font-family: "Segoe UI", Arial, sans-serif;
    font-size: 12px;
    font-weight: 800;
    padding: 3px 4px 3px 6px;
    text-align: left;
}

QPushButton#FloatingTotpInnerBtn:hover {
    color: #121316;
}

QPushButton#FloatingTotpDismissBtn {
    background: transparent;
    border: none;
    border-radius: 4px;
    padding: 1px;
    margin-right: 3px;
}

QPushButton#FloatingTotpDismissBtn:hover {
    background-color: #FF4757;
    color: #FFFFFF;
}

QPushButton.DragGripBtn {
    background: transparent;
    border: none;
    padding: 2px 4px;
    color: #FFE600;
}

QPushButton.DragGripBtn:hover {
    color: #FFF04D;
}

/* Chunky Neobrutalist Scrollbars */
QScrollArea {
    border: none;
    background: transparent;
}

QScrollBar:vertical {
    border: 1.5px solid #000000;
    background: #141519;
    width: 12px;
    margin: 2px 2px 2px 0px;
    border-radius: 6px;
}

QScrollBar::handle:vertical {
    background: #FFE600;
    border: 1.5px solid #000000;
    min-height: 28px;
    border-radius: 4px;
}

QScrollBar::handle:vertical:hover {
    background: #FFF04D;
}

QScrollBar::handle:vertical:pressed {
    background: #E6CE00;
}

QScrollBar:horizontal {
    height: 0px;
    width: 0px;
    border: none;
    background: transparent;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    border: none;
    background: none;
    height: 0px;
}

QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
    background: none;
}

/* Settings Combos & Inputs */
QComboBox, QComboBox.SettingsCombo, QComboBox[class="SettingsCombo"] {
    background-color: #1E2027;
    border: 2px solid #000000;
    border-bottom: 3.5px solid #000000;
    border-right: 3.5px solid #000000;
    border-radius: 6px;
    padding: 6px 12px;
    color: #FFFFFF;
    font-size: 12px;
    font-weight: 600;
    min-width: 180px;
}

QComboBox:hover, QComboBox[class="SettingsCombo"]:hover {
    background-color: #272B35;
}

QComboBox::drop-down {
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 24px;
    border-left: 2px solid #000000;
}

QComboBox QAbstractItemView {
    background-color: #1E2027;
    border: 2px solid #000000;
    color: #FFFFFF;
    selection-background-color: #FFE600;
    selection-color: #000000;
    padding: 4px;
}

/* Neobrutalist Checkbox */
QCheckBox {
    spacing: 8px;
    color: #F8FAFC;
    font-size: 13px;
    font-weight: 600;
}

QCheckBox::indicator {
    width: 18px;
    height: 18px;
    border: 2px solid #000000;
    border-radius: 4px;
    background-color: #1E2027;
}

QCheckBox::indicator:hover {
    background-color: #2A2E39;
}

QCheckBox::indicator:checked {
    background-color: #FFE600;
    border: 2px solid #000000;
}

/* Sliders */
QSlider::groove:horizontal {
    border: 1.5px solid #000000;
    height: 8px;
    background: #1E2027;
    border-radius: 4px;
}

QSlider::sub-page:horizontal {
    background: #FFE600;
    border: 1.5px solid #000000;
    border-radius: 4px;
}

QSlider::handle:horizontal {
    background: #FFFFFF;
    border: 2px solid #000000;
    width: 18px;
    margin-top: -6px;
    margin-bottom: -6px;
    border-radius: 5px;
}

QSlider::handle:horizontal:hover {
    background: #FFE600;
}

/* Global Neobrutalist Tooltips */
QToolTip {
    background-color: #FFE600;
    color: #000000;
    border: 2px solid #000000;
    border-radius: 5px;
    padding: 4px 8px;
    font-size: 11px;
    font-weight: 800;
}

/* Global Neobrutalist Context Menus */
QMenu {
    background-color: #121316;
    border: 2.5px solid #000000;
    border-bottom: 4px solid #000000;
    border-right: 4px solid #000000;
    border-radius: 8px;
    padding: 5px;
    color: #F8FAFC;
    font-weight: 700;
}

QMenu::item {
    padding: 6px 18px;
    border-radius: 4px;
    font-size: 12px;
    font-weight: 700;
}

QMenu::item:selected {
    background-color: #FFE600;
    color: #000000;
    font-weight: 800;
}

QMenu::separator {
    height: 2px;
    background-color: #000000;
    margin: 4px 6px;
}
"""
