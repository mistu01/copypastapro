"""
ZeBeyond Cyber-Emerald Midnight Theme styling for Mistus Copy Pasta.
Features deep obsidian green backgrounds, luminous neon mint/emerald accents,
translucent glassmorphic surfaces, and refined typography.
"""

DARK_THEME_QSS = """
/* Global Window & Font Settings */
QWidget {
    font-family: "Segoe UI", -apple-system, BlinkMacSystemFont, system-ui, sans-serif;
    color: #f0fdf4;
    background-color: transparent;
    font-size: 13px;
    selection-background-color: #059669;
    selection-color: #ffffff;
}

/* Detailed Flyout Window Background */
#DetailedWindow, #FlyoutContainer {
    background-color: #080d0a;
    border: 1px solid rgba(16, 185, 129, 0.25);
    border-radius: 16px;
}

/* Floating Bar Container */
#FloatingBarContainer {
    background-color: #09120e;
    border: 1px solid rgba(16, 185, 129, 0.35);
    border-radius: 20px;
}

#FloatingBarContainer:hover {
    border-color: rgba(0, 245, 155, 0.65);
    background-color: #0d1a14;
}

/* Minimized Floating Island Container */
#MinimizedFloatingContainer {
    background-color: #09120e;
    border: 1px solid rgba(0, 245, 155, 0.5);
    border-radius: 18px;
}

/* Header Area */
#HeaderBar {
    border-bottom: 1px solid rgba(16, 185, 129, 0.14);
    padding: 2px 4px 8px 4px;
}

/* Search Bar */
QLineEdit#SearchBar {
    background-color: rgba(16, 185, 129, 0.06);
    border: 1px solid rgba(16, 185, 129, 0.22);
    border-radius: 9px;
    padding: 8px 14px;
    color: #ffffff;
    font-size: 13px;
}

QLineEdit#SearchBar:hover {
    background-color: rgba(16, 185, 129, 0.1);
    border-color: rgba(0, 245, 155, 0.4);
}

QLineEdit#SearchBar:focus {
    background-color: rgba(16, 185, 129, 0.14);
    border: 1px solid #00f59b;
}

/* Segmented Tab Bar */
#TabBarContainer {
    background-color: rgba(16, 185, 129, 0.05);
    border: 1px solid rgba(16, 185, 129, 0.15);
    border-radius: 10px;
    padding: 3px;
}

QPushButton.NavTab {
    background-color: transparent;
    border: none;
    border-radius: 7px;
    padding: 6px 6px;
    color: #a7f3d0;
    font-weight: 500;
    font-size: 12px;
}

QPushButton.NavTab:hover {
    background-color: rgba(16, 185, 129, 0.12);
    color: #ffffff;
}

QPushButton.NavTab:checked {
    background-color: #059669;
    border: 1px solid #10b981;
    color: #ffffff;
    font-weight: 700;
}

/* Checkbox Modern Styling */
QCheckBox {
    spacing: 8px;
    color: #f0fdf4;
    font-size: 13px;
    font-weight: 500;
}

/* Action Icon Buttons */
QPushButton.IconButton {
    background-color: transparent;
    border: none;
    border-radius: 6px;
    padding: 4px;
    color: #a7f3d0;
}

QPushButton.IconButton:hover {
    background-color: rgba(16, 185, 129, 0.16);
    color: #00f59b;
}

QPushButton.IconButton:pressed {
    background-color: rgba(16, 185, 129, 0.25);
}

/* Primary Action Buttons (ZeBeyond Emerald / Mint) */
QPushButton.PrimaryButton, QPushButton[class="PrimaryButton"] {
    background-color: #059669;
    border: 1px solid #10b981;
    border-radius: 7px;
    color: #ffffff;
    font-weight: 600;
    padding: 7px 14px;
    font-size: 12px;
}

QPushButton.PrimaryButton:hover, QPushButton[class="PrimaryButton"]:hover {
    background-color: #10b981;
    border-color: #00f59b;
    color: #080d0a;
}

/* Success Emerald Button */
QPushButton.SuccessButton, QPushButton[class="SuccessButton"] {
    background-color: #059669;
    border: 1px solid #00f59b;
    border-radius: 7px;
    color: #ffffff;
    font-weight: 600;
    padding: 7px 14px;
    font-size: 12px;
}

QPushButton.SuccessButton:hover, QPushButton[class="SuccessButton"]:hover {
    background-color: #10b981;
    color: #080d0a;
}

/* Secondary Button */
QPushButton.SecondaryButton, QPushButton[class="SecondaryButton"] {
    background-color: rgba(16, 185, 129, 0.08);
    border: 1px solid rgba(16, 185, 129, 0.2);
    border-radius: 7px;
    color: #d1fae5;
    padding: 7px 12px;
    font-size: 12px;
    font-weight: 500;
}

QPushButton.SecondaryButton:hover, QPushButton[class="SecondaryButton"]:hover {
    background-color: rgba(16, 185, 129, 0.18);
    border-color: rgba(0, 245, 155, 0.45);
    color: #ffffff;
}

/* Clipboard History Card */
QFrame.ClipboardCard {
    background-color: rgba(13, 24, 19, 0.65);
    border: 1px solid rgba(16, 185, 129, 0.16);
    border-radius: 11px;
    padding: 10px 14px;
}

QFrame.ClipboardCard:hover {
    background-color: rgba(16, 185, 129, 0.12);
    border-color: rgba(0, 245, 155, 0.45);
}

/* Pinned Clipboard Card */
QFrame.PinnedCard {
    background-color: rgba(245, 158, 11, 0.09);
    border: 1px solid rgba(245, 158, 11, 0.38);
    border-radius: 11px;
    padding: 10px 14px;
}

QFrame.PinnedCard:hover {
    background-color: rgba(245, 158, 11, 0.15);
    border-color: rgba(245, 158, 11, 0.65);
}

/* Pin Slot Badge */
.PinSlotBadge, QFrame.PinSlotBadge, QLabel.PinSlotBadge {
    background-color: #d97706;
    color: #ffffff;
    font-weight: 700;
    font-size: 10px;
    border-radius: 5px;
    padding: 2px 6px;
    letter-spacing: 0.5px;
}

/* Entry Index Number Badge (#1, #2, ...) */
.EntryIndexBadge, QFrame.EntryIndexBadge, QLabel.EntryIndexBadge {
    background-color: rgba(56, 189, 248, 0.12);
    border: 1px solid rgba(56, 189, 248, 0.30);
    color: #38bdf8;
    font-weight: 700;
    font-size: 10px;
    border-radius: 5px;
    padding: 2px 6px;
    letter-spacing: 0.3px;
}

/* Type Pill Badges */
.TypeBadgeUrl, QFrame.TypeBadgeUrl, QLabel.TypeBadgeUrl {
    background-color: rgba(0, 245, 155, 0.14);
    border: 1px solid rgba(0, 245, 155, 0.35);
    color: #00f59b;
    font-weight: 700;
    font-size: 10px;
    border-radius: 5px;
    padding: 2px 6px;
}

.TypeBadgeCode, QFrame.TypeBadgeCode, QLabel.TypeBadgeCode {
    background-color: rgba(167, 139, 250, 0.14);
    border: 1px solid rgba(167, 139, 250, 0.35);
    color: #c4b5fd;
    font-weight: 700;
    font-size: 10px;
    border-radius: 5px;
    padding: 2px 6px;
}

.TypeBadgeEmail, QFrame.TypeBadgeEmail, QLabel.TypeBadgeEmail {
    background-color: rgba(245, 158, 11, 0.14);
    border: 1px solid rgba(245, 158, 11, 0.35);
    color: #f59e0b;
    font-weight: 700;
    font-size: 10px;
    border-radius: 5px;
    padding: 2px 6px;
}

.TypeBadgeText, QFrame.TypeBadgeText, QLabel.TypeBadgeText {
    background-color: rgba(16, 185, 129, 0.12);
    border: 1px solid rgba(16, 185, 129, 0.25);
    color: #6ee7b7;
    font-weight: 600;
    font-size: 10px;
    border-radius: 5px;
    padding: 2px 6px;
}

/* Active 2FA Hero Card - Solid clean dark obsidian emerald */
QFrame#ActiveTotpHeroCard {
    background-color: #061710;
    border: 1px solid rgba(0, 245, 155, 0.45);
    border-radius: 12px;
    padding: 14px 16px;
}

/* Clean Segoe UI 2FA Code Display */
QLabel.TotpCodeHero {
    font-family: "Segoe UI", Arial, sans-serif;
    font-size: 26px;
    font-weight: 700;
    color: #00f59b;
    letter-spacing: 4px;
    padding: 4px 0;
}

QLabel.TotpCodeLabel {
    font-family: "Segoe UI", Arial, sans-serif;
    font-size: 20px;
    font-weight: 700;
    color: #34d399;
    letter-spacing: 2px;
}

/* Section Header Labels */
QLabel.SectionHeader {
    color: #6ee7b7;
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 1px;
    text-transform: uppercase;
    padding: 4px 2px;
}

/* Floating Bar Snippet Chip */
QPushButton.FloatingChip {
    background-color: rgba(16, 185, 129, 0.08);
    border: 1px solid rgba(16, 185, 129, 0.2);
    border-radius: 12px;
    color: #ecfdf5;
    font-size: 12px;
    padding: 4px 11px;
    text-align: left;
}

QPushButton.FloatingChip:hover {
    background-color: rgba(16, 185, 129, 0.22);
    border-color: #00f59b;
    color: #ffffff;
}

/* Floating Bar 2FA Live Chip */
QPushButton.FloatingTotpChip {
    background-color: rgba(5, 150, 105, 0.22);
    border: 1px solid rgba(0, 245, 155, 0.55);
    border-radius: 12px;
    color: #00f59b;
    font-family: "Segoe UI", Arial, sans-serif;
    font-size: 12px;
    font-weight: 700;
    padding: 4px 12px;
}

QPushButton.FloatingTotpChip:hover {
    background-color: rgba(16, 185, 129, 0.35);
    border-color: #00f59b;
    color: #ffffff;
}

/* Drag Grip Button */
QPushButton.DragGripBtn {
    background: transparent;
    border: none;
    padding: 2px 4px;
    color: #6ee7b7;
}

QPushButton.DragGripBtn:hover {
    color: #00f59b;
}

/* Scroll Area Styling - Eliminate horizontal scrollbar completely */
QScrollArea {
    border: none;
    background: transparent;
}

QScrollBar:vertical {
    border: none;
    background: transparent;
    width: 6px;
    margin: 4px 4px 4px 0px;
    border-radius: 3px;
}

QScrollBar::handle:vertical {
    background: rgba(16, 185, 129, 0.25);
    min-height: 25px;
    border-radius: 3px;
}

QScrollBar::handle:vertical:hover {
    background: rgba(0, 245, 155, 0.45);
}

QScrollBar:horizontal {
    height: 0px;
    width: 0px;
    border: none;
    background: transparent;
}

QScrollBar::handle:horizontal, QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    width: 0px;
    height: 0px;
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
"""
