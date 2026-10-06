"""
Detailed Clipboard Manager Flyout Window for CopyPasta.
Windows 11 Fluent dark flyout with Real-time Search, 5-Slot Pinning,
Live Auto-Detected 2FA TOTP Generator Hero Card, Vector Icons, and Reliable Win+V Focus.
"""

import time
import ctypes
from typing import Optional, List, Dict, Any
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QScrollArea, QFrame, QStackedWidget,
    QProgressBar, QMessageBox, QSlider, QCheckBox, QComboBox,
    QGraphicsDropShadowEffect, QApplication
)
from PySide6.QtCore import Qt, QTimer, Signal, QPoint, QSize
from PySide6.QtGui import QColor, QKeySequence, QShortcut

from app.database import Database
from app.totp_manager import TOTPManager
from app.paste_helper import PasteHelper
from app.icons import AppIcons
from app.ui.toast import Toast
from app.ui.totp_dialog import AddTotpDialog
from app.styles import DARK_THEME_QSS
from app.version import APP_NAME, APP_VERSION

user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32


class DetailedWindow(QWidget):
    # Signals
    item_selected = Signal(str)
    settings_changed = Signal()
    pinned_changed = Signal()

    def __init__(self, db: Database, paste_helper: PasteHelper, parent=None):
        super().__init__(parent)
        self.db = db
        self.paste_helper = paste_helper
        self.keep_open = False
        self._ignore_focus_change = False

        self._init_window()
        self._init_ui()
        self._setup_totp_timer()

    def _init_window(self):
        self.setObjectName("DetailedWindow")
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.resize(560, 680)
        self.setStyleSheet(DARK_THEME_QSS)

        # Drop Shadow
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(32)
        shadow.setColor(QColor(0, 0, 0, 210))
        shadow.setOffset(0, 10)
        self.setGraphicsEffect(shadow)

        # Escape shortcut closes
        esc_shortcut = QShortcut(QKeySequence(Qt.Key_Escape), self)
        esc_shortcut.activated.connect(self.hide_window)

    def _init_ui(self):
        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(10, 10, 10, 10)

        # Main background container
        self.container = QFrame()
        self.container.setObjectName("FlyoutContainer")
        container_layout = QVBoxLayout(self.container)
        container_layout.setContentsMargins(16, 14, 16, 14)
        container_layout.setSpacing(10)

        # Top Bar: Brand, Pin Window Toggle, Close
        header = QHBoxLayout()
        header.setContentsMargins(2, 0, 2, 0)

        title_icon = QLabel()
        title_icon.setPixmap(AppIcons.clipboard(20, "#00f59b").pixmap(20, 20))
        header.addWidget(title_icon)

        self.title_label = QLabel(APP_NAME)
        self.title_label.setStyleSheet("font-size: 15px; font-weight: 800; color: #ffffff; letter-spacing: 0.5px;")
        header.addWidget(self.title_label)

        header.addStretch()

        self.pin_window_btn = QPushButton(" Keep Open")
        self.pin_window_btn.setIcon(AppIcons.pin_icon(15, "#94a3b8"))
        self.pin_window_btn.setIconSize(QSize(15, 15))
        self.pin_window_btn.setProperty("class", "NavTab")
        self.pin_window_btn.setCheckable(True)
        self.pin_window_btn.setToolTip("Keep flyout open when switching apps")
        self.pin_window_btn.clicked.connect(self._toggle_keep_open)
        header.addWidget(self.pin_window_btn)

        close_btn = QPushButton()
        close_btn.setIcon(AppIcons.close_cross(16, "#94a3b8"))
        close_btn.setIconSize(QSize(16, 16))
        close_btn.setProperty("class", "IconButton")
        close_btn.setFixedSize(26, 26)
        close_btn.setToolTip("Close (Esc)")
        close_btn.clicked.connect(self.hide_window)
        header.addWidget(close_btn)

        container_layout.addLayout(header)

        # Search Bar with clear button & leading search icon
        search_box = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setObjectName("SearchBar")
        self.search_input.setPlaceholderText("Search clippings, tags, or 2FA accounts...")
        self.search_input.setClearButtonEnabled(True)
        self.search_input.addAction(AppIcons.search(15, "#94a3b8"), QLineEdit.LeadingPosition)
        self.search_input.textChanged.connect(self._on_search_changed)
        search_box.addWidget(self.search_input)
        container_layout.addLayout(search_box)

        # Segmented Tab Bar
        tab_container = QFrame()
        tab_container.setObjectName("TabBarContainer")
        tab_nav = QHBoxLayout(tab_container)
        tab_nav.setContentsMargins(3, 3, 3, 3)
        tab_nav.setSpacing(4)

        self.tab_btn_all = QPushButton("Clipboard")
        self.tab_btn_all.setIcon(AppIcons.clipboard(15, "#ffffff"))
        self.tab_btn_all.setProperty("class", "NavTab")
        self.tab_btn_all.setCheckable(True)
        self.tab_btn_all.setChecked(True)
        self.tab_btn_all.clicked.connect(lambda: self._switch_tab(0))
        tab_nav.addWidget(self.tab_btn_all)

        self.tab_btn_pinned = QPushButton("Pinned (0/10)")
        self.tab_btn_pinned.setIcon(AppIcons.pin_icon(15, "#f59e0b", filled=True))
        self.tab_btn_pinned.setIconSize(QSize(15, 15))
        self.tab_btn_pinned.setProperty("class", "NavTab")
        self.tab_btn_pinned.setCheckable(True)
        self.tab_btn_pinned.clicked.connect(lambda: self._switch_tab(1))
        tab_nav.addWidget(self.tab_btn_pinned)

        self.tab_btn_totp = QPushButton("Authenticator")
        self.tab_btn_totp.setIcon(AppIcons.shield_check(15, "#38bdf8"))
        self.tab_btn_totp.setProperty("class", "NavTab")
        self.tab_btn_totp.setCheckable(True)
        self.tab_btn_totp.clicked.connect(lambda: self._switch_tab(2))
        tab_nav.addWidget(self.tab_btn_totp)

        self.tab_btn_settings = QPushButton("Settings")
        self.tab_btn_settings.setIcon(AppIcons.settings(15, "#94a3b8"))
        self.tab_btn_settings.setProperty("class", "NavTab")
        self.tab_btn_settings.setCheckable(True)
        self.tab_btn_settings.clicked.connect(lambda: self._switch_tab(3))
        tab_nav.addWidget(self.tab_btn_settings)

        container_layout.addWidget(tab_container)

        # Stacked Pages
        self.stack = QStackedWidget()

        # Page 0: All History (Pinned on top + recent history)
        self.page_all = self._create_scrollable_list_page()
        self.stack.addWidget(self.page_all)

        # Page 1: Pinned Entries Only
        self.page_pinned = self._create_scrollable_list_page()
        self.stack.addWidget(self.page_pinned)

        # Page 2: 2FA TOTP (Active Hero Card + Manual Input + Saved Accounts)
        self.page_totp = self._create_totp_page()
        self.stack.addWidget(self.page_totp)

        # Page 3: Settings
        self.page_settings = self._create_settings_page()
        self.stack.addWidget(self.page_settings)

        container_layout.addWidget(self.stack)
        outer_layout.addWidget(self.container)

        # Toast overlay for user feedback
        self.toast = Toast(self)

        # Initial data load
        self.refresh_clipboard_items()

    def _create_scrollable_list_page(self) -> QWidget:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        content_widget = QWidget()
        list_layout = QVBoxLayout(content_widget)
        list_layout.setContentsMargins(2, 2, 2, 2)
        list_layout.setSpacing(8)
        list_layout.addStretch()
        scroll.setWidget(content_widget)
        return scroll

    # ================= 2FA TOTP Page =================
    def _create_totp_page(self) -> QWidget:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(12)

        # Section 1: Active Live 2FA Hero Card (Persistent Two-Frame Architecture)
        self.hero_card = QFrame()
        self.hero_card.setObjectName("ActiveTotpHeroCard")
        self.hero_layout = QVBoxLayout(self.hero_card)
        self.hero_layout.setContentsMargins(14, 12, 14, 12)
        self.hero_layout.setSpacing(8)

        # Frame A: Guidance Frame (Shown when no active 2FA key)
        self.hero_guidance_frame = QFrame(self.hero_card)
        g_layout = QVBoxLayout(self.hero_guidance_frame)
        g_layout.setContentsMargins(4, 4, 4, 4)
        g_layout.setSpacing(8)

        g_hdr = QHBoxLayout()
        g_hdr.setSpacing(8)
        g_icon = QLabel()
        g_icon.setPixmap(AppIcons.pixmap("shield_check", 16, "#38bdf8"))
        g_hdr.addWidget(g_icon)
        g_title = QLabel("Ready to Auto-Detect 2FA Keys")
        g_title.setStyleSheet("color: #38bdf8; font-weight: 700; font-size: 13px;")
        g_hdr.addWidget(g_title)
        g_hdr.addStretch()
        g_layout.addLayout(g_hdr)

        g_body = QLabel(
            f"Whenever you copy any 2FA Secret Key (from Google, GitHub, Amazon, Discord, etc.), "
            f"{APP_NAME} auto-detects it and begins generating codes every 30s cycle right here!\n\n"
            f"You can also paste a secret key manually in the field below."
        )
        g_body.setStyleSheet("color: #94a3b8; font-size: 12px; line-height: 1.5;")
        g_body.setWordWrap(True)
        g_layout.addWidget(g_body)
        self.hero_layout.addWidget(self.hero_guidance_frame)

        # Frame B: Active Live 2FA Frame (Shown when active key is present)
        self.hero_active_frame = QFrame(self.hero_card)
        a_layout = QVBoxLayout(self.hero_active_frame)
        a_layout.setContentsMargins(2, 2, 2, 2)
        a_layout.setSpacing(8)

        # Row 1: Header Row
        header_row = QHBoxLayout()
        header_row.setContentsMargins(0, 0, 0, 0)
        header_row.setSpacing(8)

        badge_icon = QLabel()
        badge_icon.setPixmap(AppIcons.pixmap("shield_check", 14, "#38bdf8"))
        header_row.addWidget(badge_icon)

        badge = QLabel("LIVE ACTIVE 2FA KEY")
        badge.setStyleSheet("color: #38bdf8; font-weight: 800; font-size: 11px; letter-spacing: 0.8px;")
        header_row.addWidget(badge)

        self.hero_source_lbl = QLabel("Source: Auto-detected")
        self.hero_source_lbl.setStyleSheet("color: #94a3b8; font-size: 11px;")
        header_row.addWidget(self.hero_source_lbl)

        header_row.addStretch()

        self.hero_timer_lbl = QLabel("30s")
        self.hero_timer_lbl.setStyleSheet("""
            background: rgba(56, 189, 248, 0.15);
            color: #38bdf8;
            border: 1px solid rgba(56, 189, 248, 0.35);
            border-radius: 6px;
            padding: 2px 8px;
            font-weight: 700;
            font-size: 11px;
            font-family: 'Segoe UI', Arial, sans-serif;
        """)
        header_row.addWidget(self.hero_timer_lbl)

        clear_btn = QPushButton(" Clear")
        clear_btn.setIcon(AppIcons.close_cross(12, "#94a3b8"))
        clear_btn.setProperty("class", "IconButton")
        clear_btn.setToolTip("Dismiss current active key")
        clear_btn.clicked.connect(self._clear_active_totp)
        header_row.addWidget(clear_btn)

        a_layout.addLayout(header_row)

        # Row 2: Large code display
        code_box = QHBoxLayout()
        code_box.setContentsMargins(0, 2, 0, 2)

        self.hero_code_lbl = QLabel("------")
        self.hero_code_lbl.setAlignment(Qt.AlignCenter)
        self.hero_code_lbl.setStyleSheet("""
            font-family: 'Segoe UI', Arial, sans-serif;
            font-size: 28px;
            font-weight: 700;
            color: #38bdf8;
            letter-spacing: 5px;
            padding: 4px 0;
        """)
        self.hero_code_lbl.setCursor(Qt.PointingHandCursor)
        self.hero_code_lbl.setToolTip("Click to paste directly into active input field (Ctrl+V)")
        self.hero_code_lbl.mousePressEvent = lambda _: self._copy_active_totp_code(auto_paste=True)
        code_box.addWidget(self.hero_code_lbl)

        a_layout.addLayout(code_box)

        # Row 3: Progress Bar
        self.hero_progress = QProgressBar()
        self.hero_progress.setTextVisible(False)
        self.hero_progress.setMaximum(100)
        self.hero_progress.setFixedHeight(4)
        self.hero_progress.setStyleSheet("""
            QProgressBar { border: none; background: rgba(255, 255, 255, 0.08); border-radius: 2px; }
            QProgressBar::chunk { background: #10b981; border-radius: 2px; }
        """)
        a_layout.addWidget(self.hero_progress)

        # Row 4: Action Buttons
        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)

        hero_paste_btn = QPushButton(" Paste to App")
        hero_paste_btn.setIcon(AppIcons.zap(15, "#ffffff"))
        hero_paste_btn.setProperty("class", "SuccessButton")
        hero_paste_btn.setToolTip("Directly insert 2FA code into active input field")
        hero_paste_btn.clicked.connect(lambda: self._copy_active_totp_code(auto_paste=True))
        btn_row.addWidget(hero_paste_btn)

        self.hero_copy_btn = QPushButton(" Copy Code")
        self.hero_copy_btn.setIcon(AppIcons.copy_icon(15, "#ffffff"))
        self.hero_copy_btn.setProperty("class", "PrimaryButton")
        self.hero_copy_btn.setToolTip("Copy 2FA code to clipboard")
        self.hero_copy_btn.clicked.connect(lambda: self._copy_active_totp_code(auto_paste=False))
        btn_row.addWidget(self.hero_copy_btn)

        a_layout.addLayout(btn_row)

        # Row 5: Footer Row
        footer_row = QHBoxLayout()
        footer_row.setContentsMargins(2, 2, 2, 0)

        self.hero_secret_lbl = QLabel("Secret: ••••••••")
        self.hero_secret_lbl.setStyleSheet("color: #64748b; font-size: 11px; font-family: 'Segoe UI', Arial, sans-serif;")
        footer_row.addWidget(self.hero_secret_lbl)

        footer_row.addStretch()

        save_acc_btn = QPushButton(" Save to Permanent Accounts")
        save_acc_btn.setIcon(AppIcons.plus(12, "#38bdf8"))
        save_acc_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                color: #38bdf8;
                font-size: 11px;
                font-weight: 600;
                text-align: right;
                padding: 2px 4px;
            }
            QPushButton:hover {
                color: #7dd3fc;
                text-decoration: underline;
            }
        """)
        save_acc_btn.setCursor(Qt.PointingHandCursor)
        save_acc_btn.clicked.connect(self._save_current_active_to_permanent)
        footer_row.addWidget(save_acc_btn)

        a_layout.addLayout(footer_row)

        self.hero_layout.addWidget(self.hero_active_frame)
        self.hero_active_frame.hide()

        layout.addWidget(self.hero_card)

        # Section 2: Manual Key Input Bar
        manual_box = QFrame()
        manual_box.setStyleSheet("""
            QFrame {
                background: rgba(255, 255, 255, 0.03);
                border: 1px dashed rgba(255, 255, 255, 0.12);
                border-radius: 9px;
                padding: 6px;
            }
        """)
        m_layout = QHBoxLayout(manual_box)
        m_layout.setContentsMargins(6, 4, 6, 4)
        m_layout.setSpacing(6)

        self.manual_key_input = QLineEdit()
        self.manual_key_input.setPlaceholderText("Paste 2FA Secret Key or otpauth:// manually here...")
        self.manual_key_input.setStyleSheet("""
            QLineEdit {
                background: rgba(255, 255, 255, 0.06);
                border: 1px solid rgba(255, 255, 255, 0.12);
                border-radius: 6px;
                padding: 6px 10px;
                color: #ffffff;
                font-size: 12px;
            }
            QLineEdit:focus { border-color: #38bdf8; }
        """)
        m_layout.addWidget(self.manual_key_input)

        set_key_btn = QPushButton("Set Active")
        set_key_btn.setProperty("class", "PrimaryButton")
        set_key_btn.setToolTip("Set as active live 2FA key")
        set_key_btn.clicked.connect(self._on_manual_set_key)
        m_layout.addWidget(set_key_btn)

        layout.addWidget(manual_box)

        # Section 3: Saved Accounts Header
        saved_hdr = QHBoxLayout()
        saved_title = QLabel("PERMANENT SAVED ACCOUNTS")
        saved_title.setProperty("class", "SectionHeader")
        saved_hdr.addWidget(saved_title)
        saved_hdr.addStretch()

        add_btn = QPushButton(" Add Account")
        add_btn.setIcon(AppIcons.plus(12, "#38bdf8"))
        add_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 255, 255, 0.08);
                border: 1px solid rgba(255, 255, 255, 0.15);
                border-radius: 6px;
                color: #38bdf8;
                font-size: 11px;
                font-weight: 600;
                padding: 4px 10px;
            }
            QPushButton:hover {
                background-color: rgba(56, 189, 248, 0.2);
                border-color: #38bdf8;
                color: #ffffff;
            }
        """)
        add_btn.setCursor(Qt.PointingHandCursor)
        add_btn.clicked.connect(self._show_add_totp_dialog)
        saved_hdr.addWidget(add_btn)
        layout.addLayout(saved_hdr)

        # Container for Saved Accounts Cards
        self.saved_accounts_container = QWidget()
        self.saved_accounts_layout = QVBoxLayout(self.saved_accounts_container)
        self.saved_accounts_layout.setContentsMargins(0, 0, 0, 0)
        self.saved_accounts_layout.setSpacing(8)
        self.saved_accounts_layout.addStretch()
        layout.addWidget(self.saved_accounts_container)

        layout.addStretch()
        scroll.setWidget(page)
        return scroll

    # ================= Settings Page =================
    def _create_settings_page(self) -> QWidget:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(8, 6, 12, 10)
        layout.setSpacing(11)

        sec1 = QLabel("SHORTCUTS & INTERCEPTION")
        sec1.setProperty("class", "SectionHeader")
        layout.addWidget(sec1)

        box_win_v = QVBoxLayout()
        box_win_v.setSpacing(2)
        self.chk_win_v = QCheckBox("Intercept Windows Key + V")
        self.chk_win_v.setChecked(self.db.get_bool_setting("intercept_win_v", True))
        self.chk_win_v.stateChanged.connect(self._save_settings)
        box_win_v.addWidget(self.chk_win_v)
        sub_win_v = QLabel("Replaces the default Windows clipboard flyout with Mistus Copy Pasta (automatically disables Windows' native clipboard flyout).")
        sub_win_v.setStyleSheet("color: #6ee7b7; font-size: 12px; margin-left: 24px;")
        sub_win_v.setWordWrap(True)
        box_win_v.addWidget(sub_win_v)

        win_cfg_btn = QPushButton(" Open Windows Clipboard Settings")
        win_cfg_btn.setIcon(AppIcons.settings(13, "#00f59b"))
        win_cfg_btn.setStyleSheet("""
            QPushButton {
                background: rgba(0, 245, 155, 0.08);
                border: 1px solid rgba(0, 245, 155, 0.25);
                border-radius: 6px;
                color: #6ee7b7;
                font-size: 11px;
                padding: 4px 10px;
                margin-left: 24px;
                max-width: 250px;
                text-align: left;
            }
            QPushButton:hover {
                background: rgba(0, 245, 155, 0.16);
                color: #ffffff;
            }
        """)
        win_cfg_btn.setCursor(Qt.PointingHandCursor)
        win_cfg_btn.clicked.connect(self._open_windows_clipboard_settings)
        box_win_v.addWidget(win_cfg_btn)
        layout.addLayout(box_win_v)

        box_custom = QVBoxLayout()
        box_custom.setSpacing(2)
        self.chk_custom_hotkey = QCheckBox("Enable secondary shortcut (Ctrl + Shift + V)")
        self.chk_custom_hotkey.setChecked(self.db.get_bool_setting("custom_hotkey_enabled", True))
        self.chk_custom_hotkey.stateChanged.connect(self._save_settings)
        box_custom.addWidget(self.chk_custom_hotkey)
        sub_custom = QLabel("Alternative global shortcut to summon the clipboard manager.")
        sub_custom.setStyleSheet("color: #6ee7b7; font-size: 12px; margin-left: 24px;")
        sub_custom.setWordWrap(True)
        box_custom.addWidget(sub_custom)
        layout.addLayout(box_custom)

        sec2 = QLabel("DESKTOP FLOATING BAR")
        sec2.setProperty("class", "SectionHeader")
        layout.addWidget(sec2)

        box_bar = QVBoxLayout()
        box_bar.setSpacing(2)
        self.chk_floating_bar = QCheckBox("Show desktop floating bar")
        self.chk_floating_bar.setChecked(self.db.get_bool_setting("floating_bar_enabled", True))
        self.chk_floating_bar.stateChanged.connect(self._save_settings)
        box_bar.addWidget(self.chk_floating_bar)
        sub_bar = QLabel("Dockable edge acrylic bar with live 2FA chip and recent clippings.")
        sub_bar.setStyleSheet("color: #6ee7b7; font-size: 12px; margin-left: 24px;")
        sub_bar.setWordWrap(True)
        box_bar.addWidget(sub_bar)
        layout.addLayout(box_bar)

        op_box = QHBoxLayout()
        op_lbl = QLabel("Floating Bar Opacity:")
        op_lbl.setStyleSheet("color: #f0fdf4; font-size: 12px;")
        op_box.addWidget(op_lbl)
        self.opacity_slider = QSlider(Qt.Horizontal)
        self.opacity_slider.setRange(40, 100)
        current_op = int(float(self.db.get_setting("floating_bar_opacity", "0.95")) * 100)
        self.opacity_slider.setValue(current_op)
        self.opacity_val_lbl = QLabel(f"{current_op}%")
        self.opacity_val_lbl.setStyleSheet("color: #00f59b; font-weight: 700; font-size: 12px; min-width: 38px;")
        self.opacity_slider.valueChanged.connect(self._on_opacity_slider_changed)
        op_box.addWidget(self.opacity_slider)
        op_box.addWidget(self.opacity_val_lbl)
        layout.addLayout(op_box)

        bar_count_box = QHBoxLayout()
        bar_count_lbl = QLabel("Floating bar quick-paste entries:")
        bar_count_lbl.setStyleSheet("color: #f0fdf4; font-size: 12px;")
        bar_count_box.addWidget(bar_count_lbl)
        bar_count_box.addStretch()
        self.combo_bar_entries = QComboBox()
        self.combo_bar_entries.addItems([str(i) for i in range(1, 11)])
        self.combo_bar_entries.setCurrentText(self.db.get_setting("floating_bar_entry_count", "5"))
        self.combo_bar_entries.currentTextChanged.connect(self._save_settings)
        bar_count_box.addWidget(self.combo_bar_entries)
        layout.addLayout(bar_count_box)

        sec3 = QLabel("BEHAVIOR & PASTING")
        sec3.setProperty("class", "SectionHeader")
        layout.addWidget(sec3)

        box_paste = QVBoxLayout()
        box_paste.setSpacing(2)
        self.chk_auto_paste = QCheckBox("Auto-paste on selection")
        self.chk_auto_paste.setChecked(self.db.get_bool_setting("auto_paste_on_select", True))
        self.chk_auto_paste.stateChanged.connect(self._save_settings)
        box_paste.addWidget(self.chk_auto_paste)
        sub_paste = QLabel("Pastes directly into the active window when an item is selected.")
        sub_paste.setStyleSheet("color: #6ee7b7; font-size: 12px; margin-left: 24px;")
        sub_paste.setWordWrap(True)
        box_paste.addWidget(sub_paste)
        layout.addLayout(box_paste)

        box_c_copy = QVBoxLayout()
        box_c_copy.setSpacing(2)
        self.chk_c_copy = QCheckBox("Quick Copy on Selection (Press 'C')")
        self.chk_c_copy.setChecked(self.db.get_bool_setting("selection_c_copy_enabled", True))
        self.chk_c_copy.stateChanged.connect(self._save_settings)
        box_c_copy.addWidget(self.chk_c_copy)
        sub_c_copy = QLabel("When text is selected on screen, show interactive copy badge and press 'C' to copy directly instead of Ctrl + C.")
        sub_c_copy.setStyleSheet("color: #6ee7b7; font-size: 12px; margin-left: 24px;")
        sub_c_copy.setWordWrap(True)
        box_c_copy.addWidget(sub_c_copy)
        layout.addLayout(box_c_copy)

        hist_box = QHBoxLayout()
        hist_lbl = QLabel("Maximum clipboard history items:")
        hist_lbl.setStyleSheet("color: #f0fdf4; font-size: 12px;")
        hist_box.addWidget(hist_lbl)
        hist_box.addStretch()
        self.combo_max_history = QComboBox()
        self.combo_max_history.addItems(["50", "100", "200", "500", "1000"])
        self.combo_max_history.setCurrentText(self.db.get_setting("max_history_count", "500"))
        self.combo_max_history.currentTextChanged.connect(self._save_settings)
        hist_box.addWidget(self.combo_max_history)
        layout.addLayout(hist_box)

        sec4 = QLabel("STORAGE & MAINTENANCE")
        sec4.setProperty("class", "SectionHeader")
        layout.addWidget(sec4)

        box_clear = QVBoxLayout()
        box_clear.setSpacing(4)
        clear_btn = QPushButton("Clear Unpinned History")
        clear_btn.setIcon(AppIcons.trash(15, "#f43f5e"))
        clear_btn.setProperty("class", "SecondaryButton")
        clear_btn.clicked.connect(self._clear_unpinned_history)
        box_clear.addWidget(clear_btn)
        sub_clear = QLabel("Keeps your 10 pinned snippets safe while purging normal history items.")
        sub_clear.setStyleSheet("color: #94a3b8; font-size: 12px; margin-left: 2px;")
        sub_clear.setWordWrap(True)
        box_clear.addWidget(sub_clear)
        layout.addLayout(box_clear)

        footer = QLabel(f"{APP_NAME} — Fast, Private & Modern Clipboard Manager")
        footer.setStyleSheet("color: #64748b; font-size: 12px; padding: 14px 0 6px 0; background: transparent; border: none;")
        footer.setAlignment(Qt.AlignCenter)
        layout.addWidget(footer)

        layout.addStretch()
        scroll.setWidget(page)
        return scroll

    def _on_opacity_slider_changed(self, val: int):
        if hasattr(self, "opacity_val_lbl"):
            self.opacity_val_lbl.setText(f"{val}%")
        self._save_settings()

    def _switch_tab(self, index: int):
        self.tab_btn_all.setChecked(index == 0)
        self.tab_btn_pinned.setChecked(index == 1)
        self.tab_btn_totp.setChecked(index == 2)
        self.tab_btn_settings.setChecked(index == 3)
        self.stack.setCurrentIndex(index)

        if index in (0, 1):
            self.refresh_clipboard_items()
        elif index == 2:
            self.refresh_totp_accounts()

    def _toggle_keep_open(self):
        self.keep_open = self.pin_window_btn.isChecked()
        if self.keep_open:
            self.pin_window_btn.setText(" Window Pinned")
            self.pin_window_btn.setIcon(AppIcons.pin_icon(15, "#38bdf8", filled=True))
            self.toast.show_message("Window pinned: stays open across clicks")
        else:
            self.pin_window_btn.setText(" Keep Open")
            self.pin_window_btn.setIcon(AppIcons.pin_icon(15, "#94a3b8", filled=False))
            self.toast.show_message("Window unpinned: auto-hides on blur")

    def _save_settings(self):
        self.db.set_setting("intercept_win_v", str(self.chk_win_v.isChecked()).lower())
        self.db.set_setting("custom_hotkey_enabled", str(self.chk_custom_hotkey.isChecked()).lower())
        self.db.set_setting("floating_bar_enabled", str(self.chk_floating_bar.isChecked()).lower())
        self.db.set_setting("floating_bar_opacity", str(self.opacity_slider.value() / 100.0))
        if hasattr(self, "combo_bar_entries"):
            self.db.set_setting("floating_bar_entry_count", self.combo_bar_entries.currentText())
        self.db.set_setting("auto_paste_on_select", str(self.chk_auto_paste.isChecked()).lower())
        self.db.set_setting("selection_c_copy_enabled", str(self.chk_c_copy.isChecked()).lower())
        self.db.set_setting("max_history_count", self.combo_max_history.currentText())
        self.db.trim_history()
        self.settings_changed.emit()

    def _open_windows_clipboard_settings(self):
        import webbrowser
        try:
            webbrowser.open("ms-settings:clipboard")
        except Exception:
            pass

    def _clear_unpinned_history(self):
        reply = QMessageBox.question(
            self,
            "Clear History",
            "Clear all unpinned clipboard items? Pinned items will remain safe.",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            count = self.db.clear_unpinned_history()
            self.refresh_clipboard_items()
            self.toast.show_message(f"Cleared {count} unpinned items.")

    def _on_search_changed(self, text: str):
        idx = self.stack.currentIndex()
        if idx in (0, 1):
            self.refresh_clipboard_items()
        elif idx == 2:
            self.refresh_totp_accounts()

    # ================= Clipboard List Rendering =================
    def refresh_clipboard_items(self):
        search_query = self.search_input.text().strip()
        try:
            max_limit = int(self.db.get_setting("max_history_count", "500"))
        except ValueError:
            max_limit = 500

        items = self.db.get_history(search=search_query, limit=max_limit)
        pinned_items = self.db.get_pinned_items()

        self.tab_btn_pinned.setText(f"Pinned ({len(pinned_items)}/10)")
        self.tab_btn_all.setText(f"Clipboard ({len(items)})")

        if self.stack.currentIndex() == 1:
            target_scroll = self.page_pinned
            target_container = target_scroll.widget()
            layout = target_container.layout()
            self._render_pinned_slots_view(layout, pinned_items)
            return

        target_scroll = self.page_all
        target_container = target_scroll.widget()
        layout = target_container.layout()

        while layout.count() > 1:
            child = layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        if not items:
            empty_lbl = QLabel("No clipboard items found." if not search_query else f"No matches for '{search_query}'.")
            empty_lbl.setStyleSheet("color: #64748b; font-size: 13px; padding: 40px; text-align: center;")
            empty_lbl.setAlignment(Qt.AlignCenter)
            layout.insertWidget(0, empty_lbl)
            return

        pinned_list = [it for it in items if it["is_pinned"]]
        recent_list = [it for it in items if not it["is_pinned"]]

        insert_idx = 0
        if pinned_list:
            hdr_pinned = QLabel(f"PINNED CLIPPINGS ({len(pinned_list)}/10)")
            hdr_pinned.setProperty("class", "SectionHeader")
            layout.insertWidget(insert_idx, hdr_pinned)
            insert_idx += 1

            for item in pinned_list:
                card = self._build_item_card(item)
                layout.insertWidget(insert_idx, card)
                insert_idx += 1

        if recent_list:
            hdr_title = f"MATCHING CLIPPINGS ({len(recent_list)})" if search_query else f"RECENT CLIPPINGS ({len(recent_list)})"
            hdr_recent = QLabel(hdr_title)
            hdr_recent.setProperty("class", "SectionHeader")
            layout.insertWidget(insert_idx, hdr_recent)
            insert_idx += 1

            for idx, item in enumerate(recent_list, 1):
                card = self._build_item_card(item, index=idx)
                layout.insertWidget(insert_idx, card)
                insert_idx += 1

    def _render_pinned_slots_view(self, layout, pinned_items: List[Dict[str, Any]]):
        while layout.count() > 1:
            child = layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        hdr = QLabel(f"10 PINNED SLOTS ({len(pinned_items)} OF 10 USED)")
        hdr.setProperty("class", "SectionHeader")
        layout.insertWidget(0, hdr)

        pinned_by_slot = {it["pin_slot"]: it for it in pinned_items if it.get("pin_slot")}

        for slot_num in range(1, 11):
            if slot_num in pinned_by_slot:
                card = self._build_item_card(pinned_by_slot[slot_num], index=slot_num)
                layout.insertWidget(slot_num, card)
            else:
                placeholder = QFrame()
                placeholder.setObjectName(f"EmptySlotFrame_{slot_num}")
                placeholder.setStyleSheet(f"""
                    QFrame#EmptySlotFrame_{slot_num} {{
                        background: rgba(255, 255, 255, 0.02);
                        border: 1px dashed rgba(255, 255, 255, 0.12);
                        border-radius: 9px;
                    }}
                """)
                ph_layout = QHBoxLayout(placeholder)
                ph_layout.setContentsMargins(14, 10, 14, 10)
                ph_lbl = QLabel(f"Slot #{slot_num}: (Empty) \u2014 Click pin on any clipping to reserve here")
                ph_lbl.setStyleSheet("color: #94a3b8; font-size: 12px; background: transparent; border: none;")
                ph_layout.addWidget(ph_lbl)
                layout.insertWidget(slot_num, placeholder)

    def _build_item_card(self, item: Dict[str, Any], index: Optional[int] = None) -> QFrame:
        is_pinned = bool(item["is_pinned"])
        pin_slot = item.get("pin_slot")
        content_type = item.get("content_type", "text")

        card = QFrame()
        card.setProperty("class", "PinnedCard" if is_pinned else "ClipboardCard")
        card.setCursor(Qt.PointingHandCursor)

        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(14, 10, 14, 10)
        card_layout.setSpacing(6)

        # Meta Header
        meta_row = QHBoxLayout()
        meta_row.setSpacing(6)

        # 1. Leading Identity Badge: Pin Slot or Sequential Entry Number (#1, #2, ...)
        if is_pinned and pin_slot:
            pin_pill = QFrame()
            pin_pill.setProperty("class", "PinSlotBadge")
            pp_layout = QHBoxLayout(pin_pill)
            pp_layout.setContentsMargins(6, 2, 7, 2)
            pp_layout.setSpacing(4)
            s_icon = QLabel()
            s_icon.setPixmap(AppIcons.pixmap("star", 10, "#ffffff"))
            pp_layout.addWidget(s_icon)
            s_lbl = QLabel(f"PIN #{pin_slot}")
            s_lbl.setStyleSheet("color: #ffffff; font-weight: 700; font-size: 10px; letter-spacing: 0.5px;")
            pp_layout.addWidget(s_lbl)
            meta_row.addWidget(pin_pill)
        elif is_pinned:
            pin_pill = QFrame()
            pin_pill.setProperty("class", "PinSlotBadge")
            pp_layout = QHBoxLayout(pin_pill)
            pp_layout.setContentsMargins(6, 2, 7, 2)
            pp_layout.setSpacing(4)
            s_icon = QLabel()
            s_icon.setPixmap(AppIcons.pixmap("star", 10, "#ffffff"))
            pp_layout.addWidget(s_icon)
            s_lbl = QLabel("PIN")
            s_lbl.setStyleSheet("color: #ffffff; font-weight: 700; font-size: 10px; letter-spacing: 0.5px;")
            pp_layout.addWidget(s_lbl)
            meta_row.addWidget(pin_pill)
        elif index is not None:
            num_pill = QFrame()
            num_pill.setProperty("class", "EntryIndexBadge")
            np_layout = QHBoxLayout(num_pill)
            np_layout.setContentsMargins(6, 2, 6, 2)
            np_layout.setSpacing(0)
            num_lbl = QLabel(f"#{index}")
            num_lbl.setStyleSheet("font-size: 10px; font-weight: 700; color: #38bdf8;")
            np_layout.addWidget(num_lbl)
            meta_row.addWidget(num_pill)

        # 2. Type Badge Pill with crisp Lucide vector icon
        type_class_map = {
            "url": ("TypeBadgeUrl", "LINK", AppIcons.pixmap("link", 11, "#38bdf8")),
            "code": ("TypeBadgeCode", "CODE", AppIcons.pixmap("code", 11, "#c084fc")),
            "email": ("TypeBadgeEmail", "EMAIL", AppIcons.pixmap("mail", 11, "#f59e0b")),
            "text": ("TypeBadgeText", "TEXT", AppIcons.pixmap("file_text", 11, "#94a3b8"))
        }
        badge_class, badge_text, badge_pix = type_class_map.get(
            content_type, ("TypeBadgeText", "TEXT", AppIcons.pixmap("file_text", 11, "#94a3b8"))
        )

        type_pill = QFrame()
        type_pill.setProperty("class", badge_class)
        tp_layout = QHBoxLayout(type_pill)
        tp_layout.setContentsMargins(6, 2, 7, 2)
        tp_layout.setSpacing(4)
        t_icon = QLabel()
        t_icon.setPixmap(badge_pix)
        tp_layout.addWidget(t_icon)
        t_lbl = QLabel(badge_text)
        t_lbl.setStyleSheet("font-size: 10px; font-weight: 700; color: inherit;")
        tp_layout.addWidget(t_lbl)
        meta_row.addWidget(type_pill)

        char_lbl = QLabel(f"{item['char_count']} chars")
        char_lbl.setStyleSheet("color: #64748b; font-size: 11px;")
        meta_row.addWidget(char_lbl)

        now = time.time()
        diff = now - (item.get("last_used_at") or item.get("created_at") or now)
        if diff < 60:
            time_str = "Just now"
        elif diff < 3600:
            time_str = f"{int(diff // 60)}m ago"
        elif diff < 86400:
            time_str = f"{int(diff // 3600)}h ago"
        else:
            time_str = f"{int(diff // 86400)}d ago"

        time_lbl = QLabel(time_str)
        time_lbl.setStyleSheet("color: #64748b; font-size: 11px;")
        meta_row.addWidget(time_lbl)

        meta_row.addStretch()

        # Pin / Unpin button
        pin_btn = QPushButton()
        pin_btn.setIcon(AppIcons.pin_icon(16, "#f59e0b" if is_pinned else "#94a3b8", filled=is_pinned))
        pin_btn.setIconSize(QSize(16, 16))
        pin_btn.setProperty("class", "IconButton")
        pin_btn.setFixedSize(26, 26)
        pin_btn.setToolTip("Unpin from top" if is_pinned else "Pin to top (max 10)")
        pin_btn.clicked.connect(lambda _, it=item: self._toggle_pin(it))
        meta_row.addWidget(pin_btn)

        # Delete button
        del_btn = QPushButton()
        del_btn.setIcon(AppIcons.trash(16, "#f43f5e"))
        del_btn.setIconSize(QSize(16, 16))
        del_btn.setProperty("class", "IconButton")
        del_btn.setFixedSize(26, 26)
        del_btn.setToolTip("Delete clipping")
        del_btn.clicked.connect(lambda _, it_id=item["id"]: self._delete_item(it_id))
        meta_row.addWidget(del_btn)

        card_layout.addLayout(meta_row)

        # Content text
        content_lbl = QLabel()
        preview = item["content"].strip()
        lines = preview.splitlines()
        if len(lines) > 3:
            preview = "\n".join(lines[:3]) + "..."
        if len(preview) > 160:
            preview = preview[:160] + "..."
        content_lbl.setText(preview)
        content_lbl.setStyleSheet("color: #f1f5f9; font-size: 13px; line-height: 1.45;")
        content_lbl.setWordWrap(True)
        card_layout.addWidget(content_lbl)

        # Ensure clicking anywhere on the card (text, badges, metadata) triggers direct paste
        for child in card.findChildren(QWidget):
            if not isinstance(child, QPushButton):
                child.setAttribute(Qt.WA_TransparentForMouseEvents, True)

        def _on_card_clicked(event, c=item["content"], i=item["id"]):
            if event.button() == Qt.LeftButton:
                self._select_and_paste(c, i)

        card.mousePressEvent = _on_card_clicked
        return card

    def _toggle_pin(self, item: Dict[str, Any]):
        item_id = item["id"]
        if item["is_pinned"]:
            self.db.unpin_item(item_id)
            self.toast.show_message("Clipping unpinned")
        else:
            success, msg = self.db.pin_item(item_id)
            self.toast.show_message(msg)

        QTimer.singleShot(60, self.refresh_clipboard_items)
        self.pinned_changed.emit()

    def _delete_item(self, item_id: int):
        self.db.delete_item(item_id)
        QTimer.singleShot(60, self.refresh_clipboard_items)
        self.toast.show_message("Clipping deleted")
        self.pinned_changed.emit()

    def _select_and_paste(self, content: str, item_id: int):
        self.db.touch_item(item_id)
        self.paste_helper.set_clipboard_text(content)

        auto_paste = self.db.get_bool_setting("auto_paste_on_select", True)
        if not self.keep_open:
            self.hide()

        if auto_paste:
            self.toast.show_message("Pasting into active window...")
            self.paste_helper.restore_focus_and_paste()
        else:
            self.toast.show_message("Copied to clipboard!")

        self.item_selected.emit(content)

    # ================= 2FA TOTP Rendering & Auto-Cycle =================
    def _setup_totp_timer(self):
        self.totp_timer = QTimer(self)
        self.totp_timer.setInterval(850)
        self.totp_timer.timeout.connect(self._update_all_totp_ticks)
        self.totp_timer.start()

    def refresh_totp_accounts(self):
        self._render_active_totp_hero()

        while self.saved_accounts_layout.count() > 1:
            child = self.saved_accounts_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        accounts = self.db.get_totp_accounts()
        search_query = self.search_input.text().strip().lower()
        if search_query:
            accounts = [
                acc for acc in accounts
                if search_query in acc["issuer"].lower() or search_query in acc["account_name"].lower()
            ]

        if not accounts:
            empty = QLabel("No permanent accounts saved yet.\nClick '＋ Add Account' or use 'Save to Permanent Accounts' on the active key.")
            empty.setStyleSheet("color: #64748b; font-size: 12px; padding: 20px; text-align: center;")
            empty.setAlignment(Qt.AlignCenter)
            self.saved_accounts_layout.insertWidget(0, empty)
            return

        for idx, acc in enumerate(accounts):
            card = self._build_saved_totp_card(acc)
            self.saved_accounts_layout.insertWidget(idx, card)

    def _render_active_totp_hero(self):
        active = self.db.get_active_totp()
        if not active or not active.get("secret"):
            self.hero_card.setProperty("secret", "")
            self.hero_active_frame.hide()
            self.hero_guidance_frame.show()
            return

        # Active Key Present: update values on persistent active frame
        self.hero_source_lbl.setText(f"Source: {active.get('issuer', 'Auto-detected')}")
        masked = TOTPManager.mask_secret(active["secret"])
        self.hero_secret_lbl.setText(f"Secret: {masked}")

        self.hero_card.setProperty("secret", active["secret"])
        self.hero_card.setProperty("digits", active.get("digits", 6))
        self.hero_card.setProperty("period", active.get("period", 30))

        self.hero_guidance_frame.hide()
        self.hero_active_frame.show()
        self._update_hero_tick()

    def _update_hero_tick(self):
        secret = self.hero_card.property("secret")
        if not secret:
            return

        digits = self.hero_card.property("digits") or 6
        period = self.hero_card.property("period") or 30

        try:
            _, formatted, remaining, progress = TOTPManager.generate_code(secret, digits, period)
            if hasattr(self, "hero_code_lbl") and self.hero_code_lbl:
                self.hero_code_lbl.setText(formatted)
            if hasattr(self, "hero_timer_lbl") and self.hero_timer_lbl:
                self.hero_timer_lbl.setText(f"{remaining}s")
            if hasattr(self, "hero_progress") and self.hero_progress:
                self.hero_progress.setValue(int(progress * 100))
                color = "#ef4444" if remaining <= 5 else ("#f59e0b" if remaining <= 10 else "#10b981")
                self.hero_progress.setStyleSheet(f"""
                    QProgressBar {{ border: none; background: rgba(255, 255, 255, 0.08); border-radius: 2px; }}
                    QProgressBar::chunk {{ background: {color}; border-radius: 2px; }}
                """)
        except Exception:
            pass

    def _copy_active_totp_code(self, auto_paste: bool = False):
        active = self.db.get_active_totp()
        if not active or not active.get("secret"):
            return

        try:
            raw, formatted, _, _ = TOTPManager.generate_code(
                active["secret"], active.get("digits", 6), active.get("period", 30)
            )
            self.paste_helper.set_clipboard_text(raw)

            if not self.keep_open and auto_paste:
                self.hide()

            if auto_paste:
                self.toast.show_message(f"Pasting 2FA code: {formatted}")
                self.paste_helper.restore_focus_and_paste()
            else:
                self.toast.show_message(f"Copied 2FA code: {formatted}")
                if hasattr(self, "hero_copy_btn") and self.hero_copy_btn:
                    self.hero_copy_btn.setText("✓ Copied!")
                    QTimer.singleShot(1200, lambda: self.hero_copy_btn.setText(" Copy Code"))
        except Exception as e:
            self.toast.show_message(f"Error: {e}")

    def _clear_active_totp(self):
        self.db.clear_active_totp()
        self.hero_card.setProperty("secret", "")
        self.hero_active_frame.hide()
        self.hero_guidance_frame.show()
        self.pinned_changed.emit()
        self.toast.show_message("Active 2FA key cleared")

    def _save_current_active_to_permanent(self):
        active = self.db.get_active_totp()
        if active and active.get("secret"):
            self._save_active_to_permanent(active)

    def _save_active_to_permanent(self, active: Dict[str, Any]):
        dlg = AddTotpDialog(self)
        dlg.issuer_input.setText(active.get("issuer", "Service"))
        dlg.account_input.setText(active.get("account_name", "Account"))
        dlg.secret_input.setText(active.get("secret", ""))
        if dlg.exec():
            data = dlg.get_data()
            self.db.add_totp_account(
                issuer=data["issuer"],
                account_name=data["account_name"],
                secret=data["secret"],
                digits=data["digits"],
                period=data["period"]
            )
            self.refresh_totp_accounts()
            self.toast.show_message(f"Saved account: {data['issuer']}")

    def _on_manual_set_key(self):
        text = self.manual_key_input.text().strip()
        if not text:
            return

        detected = TOTPManager.detect_totp_key(text)
        if not detected:
            if TOTPManager.validate_secret(text):
                detected = {
                    "secret": TOTPManager.clean_secret(text),
                    "issuer": "Manual Entry",
                    "account_name": "Key"
                }

        if detected:
            self.db.set_active_totp(detected["secret"], detected.get("issuer", "Manual Entry"), detected.get("account_name", "Key"))
            self.manual_key_input.clear()
            self.refresh_totp_accounts()
            self.pinned_changed.emit()
            self.toast.show_message("✓ Active 2FA key updated!")
        else:
            QMessageBox.warning(self, "Invalid Key", "The entered text does not appear to be a valid 2FA Base32 secret key.")

    def _update_all_totp_ticks(self):
        if self.stack.currentIndex() != 2:
            return

        self._update_hero_tick()
        for i in range(self.saved_accounts_layout.count()):
            item = self.saved_accounts_layout.itemAt(i)
            if item and item.widget() and isinstance(item.widget(), QFrame):
                self._update_single_saved_totp(item.widget())

    def _build_saved_totp_card(self, acc: Dict[str, Any]) -> QFrame:
        card = QFrame()
        card.setProperty("class", "TotpCard")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(14, 11, 14, 11)
        layout.setSpacing(6)

        top = QHBoxLayout()
        title_lbl = QLabel(f"{acc['issuer']} ({acc['account_name']})")
        title_lbl.setStyleSheet("font-size: 13px; font-weight: 700; color: #ffffff;")
        top.addWidget(title_lbl)
        top.addStretch()

        del_btn = QPushButton()
        del_btn.setIcon(AppIcons.trash(15, "#f43f5e"))
        del_btn.setIconSize(QSize(15, 15))
        del_btn.setProperty("class", "IconButton")
        del_btn.setFixedSize(24, 24)
        del_btn.setToolTip("Delete account")
        del_btn.clicked.connect(lambda _, a_id=acc["id"]: self._delete_totp_account(a_id))
        top.addWidget(del_btn)
        layout.addLayout(top)

        mid = QHBoxLayout()
        code_lbl = QLabel("------")
        code_lbl.setStyleSheet("font-family: 'Segoe UI', Arial, sans-serif; font-size: 19px; font-weight: 700; color: #67e8f9; letter-spacing: 2px;")
        code_lbl.setProperty("class", "TotpCodeLabel")
        code_lbl.setCursor(Qt.PointingHandCursor)
        code_lbl.setToolTip("Click to paste directly into active input field")
        code_lbl.mousePressEvent = lambda _, a=acc: self._copy_totp_code(a, auto_paste=True)
        mid.addWidget(code_lbl)
        mid.addStretch()

        copy_btn = QPushButton(" Copy")
        copy_btn.setIcon(AppIcons.copy_icon(13, "#ffffff"))
        copy_btn.setProperty("class", "SecondaryButton")
        copy_btn.setFixedWidth(74)
        copy_btn.clicked.connect(lambda _, a=acc: self._copy_totp_code(a, auto_paste=False))
        mid.addWidget(copy_btn)

        paste_btn = QPushButton(" Paste")
        paste_btn.setIcon(AppIcons.zap(13, "#ffffff"))
        paste_btn.setProperty("class", "SuccessButton")
        paste_btn.setFixedWidth(74)
        paste_btn.clicked.connect(lambda _, a=acc: self._copy_totp_code(a, auto_paste=True))
        mid.addWidget(paste_btn)
        layout.addLayout(mid)

        p_bar = QProgressBar()
        p_bar.setTextVisible(False)
        p_bar.setMaximum(100)
        p_bar.setFixedHeight(3)
        layout.addWidget(p_bar)

        card.setProperty("secret", acc["secret"])
        card.setProperty("digits", acc.get("digits", 6))
        card.setProperty("period", acc.get("period", 30))

        self._update_single_saved_totp(card)
        return card

    def _update_single_saved_totp(self, card: QFrame):
        secret = card.property("secret")
        if not secret:
            return
        digits = card.property("digits") or 6
        period = card.property("period") or 30

        try:
            _, formatted, remaining, progress = TOTPManager.generate_code(secret, digits, period)
            for lbl in card.findChildren(QLabel):
                if "TotpCodeLabel" in lbl.property("class"):
                    lbl.setText(formatted)
                    break
            p_bar = card.findChild(QProgressBar)
            if p_bar:
                p_bar.setValue(int(progress * 100))
                color = "#ef4444" if remaining <= 5 else ("#f59e0b" if remaining <= 10 else "#10b981")
                p_bar.setStyleSheet(f"""
                    QProgressBar {{ border: none; background: rgba(255, 255, 255, 0.08); border-radius: 2px; }}
                    QProgressBar::chunk {{ background: {color}; border-radius: 2px; }}
                """)
        except Exception:
            pass

    def _copy_totp_code(self, acc: Dict[str, Any], auto_paste: bool = False):
        try:
            raw, formatted, _, _ = TOTPManager.generate_code(acc["secret"])
            self.paste_helper.set_clipboard_text(raw)
            if not self.keep_open and auto_paste:
                self.hide()
            if auto_paste:
                self.toast.show_message(f"Pasting: {formatted}")
                self.paste_helper.restore_focus_and_paste()
            else:
                self.toast.show_message(f"Copied: {formatted}")
        except Exception as e:
            self.toast.show_message(f"Error: {e}")

    def _show_add_totp_dialog(self):
        dlg = AddTotpDialog(self)
        if dlg.exec():
            data = dlg.get_data()
            try:
                self.db.add_totp_account(
                    issuer=data["issuer"],
                    account_name=data["account_name"],
                    secret=data["secret"],
                    digits=data["digits"],
                    period=data["period"],
                    algorithm=data["algorithm"]
                )
                self.refresh_totp_accounts()
                self.toast.show_message(f"Added: {data['issuer']}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to save account: {e}")

    def _delete_totp_account(self, account_id: int):
        reply = QMessageBox.question(
            self,
            "Delete 2FA Account",
            "Remove this permanent 2FA account?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.db.delete_totp_account(account_id)
            self.refresh_totp_accounts()
            self.toast.show_message("2FA account removed")

    # ================= Reliable Win+V Show & Focus Management =================
    def show_flyout(self, target_pos: Optional[QPoint] = None):
        self.paste_helper.capture_foreground_window()
        self.search_input.clear()
        self.refresh_clipboard_items()
        self.refresh_totp_accounts()

        # Screen clamping
        screen = QApplication.primaryScreen().availableGeometry()
        if target_pos:
            x = target_pos.x()
            y = target_pos.y()
        else:
            x = screen.right() - self.width() - 16
            y = screen.bottom() - self.height() - 16

        x = max(screen.left() + 10, min(x, screen.right() - self.width() - 10))
        y = max(screen.top() + 10, min(y, screen.bottom() - self.height() - 10))
        self.move(x, y)

        # Ignore focus changes for 800ms so Win key release does not prematurely auto-hide
        self._ignore_focus_change = True
        QTimer.singleShot(800, self._enable_focus_tracking)

        self.show()
        self.raise_()
        self.activateWindow()

        # Force Windows foreground activation
        hwnd = int(self.winId())
        if hwnd:
            try:
                cur_thread = kernel32.GetCurrentThreadId()
                fore_hwnd = user32.GetForegroundWindow()
                fore_thread = user32.GetWindowThreadProcessId(fore_hwnd, None)
                if cur_thread != fore_thread:
                    user32.AttachThreadInput(cur_thread, fore_thread, True)
                    user32.SetForegroundWindow(hwnd)
                    user32.BringWindowToTop(hwnd)
                    user32.AttachThreadInput(cur_thread, fore_thread, False)
                else:
                    user32.SetForegroundWindow(hwnd)
                    user32.BringWindowToTop(hwnd)
            except Exception as e:
                print(f"[DetailedWindow] Focus activation note: {e}")

        self.search_input.setFocus()

    def _enable_focus_tracking(self):
        self._ignore_focus_change = False

    def hide_window(self):
        self.hide()

    def changeEvent(self, event):
        if event.type() == event.Type.ActivationChange:
            if not self._ignore_focus_change and not self.isActiveWindow() and not self.keep_open and self.isVisible():
                QTimer.singleShot(250, self._check_focus_and_hide)
        super().changeEvent(event)

    def _check_focus_and_hide(self):
        if not self._ignore_focus_change and not self.isActiveWindow() and not self.keep_open and self.isVisible():
            active_popup = QApplication.activePopupWidget() or QApplication.activeModalWidget()
            if not active_popup:
                self.hide()
