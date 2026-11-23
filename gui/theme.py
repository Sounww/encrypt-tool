"""浅色简约主题：颜色常量 + 全局 QSS。"""

from pathlib import Path

from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QApplication

ASSETS = Path(__file__).parent / "assets"

BG = "#F4F6FA"
SURFACE = "#FFFFFF"
SURFACE_MUTED = "#F1F3F8"
BORDER = "#E3E7EE"
BORDER_STRONG = "#D5DAE3"
INPUT_BG = "#FAFBFC"
READONLY_BG = "#F7F8FA"

TEXT = "#1E2433"
TEXT_SECONDARY = "#6B7385"
TEXT_MUTED = "#9AA1B2"

PRIMARY = "#3B5BDB"
PRIMARY_HOVER = "#3049B8"
PRIMARY_PRESSED = "#263B96"
PRIMARY_SOFT = "#EDF2FF"
PRIMARY_SOFT_HOVER = "#DBE4FF"
PRIMARY_BORDER = "#BAC8FF"
PRIMARY_DISABLED = "#A5B4EC"

SUCCESS = "#2F9E44"
SUCCESS_SOFT = "#EBFBEE"
SUCCESS_BORDER = "#B2F2BB"
DANGER = "#E03131"
DANGER_SOFT = "#FFF5F5"
DANGER_BORDER = "#FFC9C9"

UI_FONT = "Microsoft YaHei UI"
MONO_FONT = "Consolas"


def build_qss() -> str:
    chevron = (ASSETS / "chevron-down.svg").as_posix()
    check = (ASSETS / "check.svg").as_posix()
    return f"""
* {{
    font-family: "{UI_FONT}", "Segoe UI", sans-serif;
    font-size: 13px;
    color: {TEXT};
}}
QMainWindow, QWidget#root, QWidget#pageBody, QStackedWidget#content {{
    background: {BG};
}}
QScrollArea#pageScroll {{ background: {BG}; border: none; }}
QScrollArea#pageScroll > QWidget {{ background: {BG}; }}
QDialog {{ background: {SURFACE}; }}
QToolTip {{
    background: {TEXT}; color: {SURFACE}; border: none;
    border-radius: 6px; padding: 6px 8px;
}}

/* ---------- 侧边栏 ---------- */
QFrame#sidebar {{ background: {SURFACE}; border-right: 1px solid {BORDER}; }}
QLabel#brandTitle {{ font-size: 17px; font-weight: bold; }}
QLabel#brandSubtitle {{ font-size: 12px; color: {TEXT_SECONDARY}; }}
QLabel#navGroup {{
    font-size: 11px; font-weight: bold; color: {TEXT_MUTED};
    padding: 0 0 0 12px;
}}
QFrame#navItem {{ background: transparent; border: none; border-radius: 10px; }}
QFrame#navItem:hover {{ background: {SURFACE_MUTED}; }}
QFrame#navItem[active="true"], QFrame#navItem[active="true"]:hover {{ background: {PRIMARY_SOFT}; }}
QFrame#navBar {{ background: transparent; border-radius: 1px; }}
QFrame#navBar[active="true"] {{ background: {PRIMARY}; }}
QLabel#navIcon {{
    background: {SURFACE_MUTED}; color: {TEXT_SECONDARY};
    border-radius: 9px; font-size: 14px; font-weight: bold;
}}
QLabel#navIcon[active="true"] {{ background: {PRIMARY}; color: {SURFACE}; }}
QLabel#navTitle {{ font-size: 14px; font-weight: bold; background: transparent; }}
QLabel#navTitle[active="true"] {{ color: {PRIMARY}; }}
QLabel#navDesc {{ font-size: 11px; color: {TEXT_SECONDARY}; background: transparent; }}
QLabel#sidebarFooter {{ font-size: 11px; color: {TEXT_MUTED}; padding-left: 12px; }}

/* ---------- 页面与卡片 ---------- */
QLabel#pageTitle {{ font-size: 24px; font-weight: bold; }}
QLabel#pageSubtitle {{ font-size: 13px; color: {TEXT_SECONDARY}; }}
QLabel[role="tag"] {{
    background: {PRIMARY_SOFT}; color: {PRIMARY};
    border-radius: 10px; padding: 3px 10px;
    font-size: 11px; font-weight: bold;
}}
QFrame#card {{ background: {SURFACE}; border: 1px solid {BORDER}; border-radius: 14px; }}
QLabel#cardTitle {{ font-size: 15px; font-weight: bold; }}
QLabel#cardHint {{ font-size: 12px; color: {TEXT_SECONDARY}; }}
QLabel#fieldLabel {{ font-size: 12px; font-weight: bold; color: {TEXT_SECONDARY}; }}
QLabel#metaText {{ font-size: 12px; color: {TEXT_MUTED}; }}

/* ---------- 输入控件 ---------- */
QLineEdit, QPlainTextEdit, QComboBox {{
    background: {INPUT_BG};
    border: 1px solid {BORDER_STRONG};
    border-radius: 8px;
    padding: 7px 10px;
    selection-background-color: {PRIMARY_SOFT_HOVER};
    selection-color: {TEXT};
}}
QLineEdit:hover, QPlainTextEdit:hover, QComboBox:hover {{ border-color: {PRIMARY_BORDER}; }}
QLineEdit:focus, QPlainTextEdit:focus, QComboBox:focus {{
    border: 1px solid {PRIMARY}; background: {SURFACE};
}}
QLineEdit:read-only, QPlainTextEdit[readOnly="true"] {{ background: {READONLY_BG}; }}
QLineEdit[mono="true"], QPlainTextEdit[mono="true"] {{
    font-family: "{MONO_FONT}", "Cascadia Mono", monospace;
    font-size: 13px;
}}
QPlainTextEdit[mono="true"][pem="true"] {{ font-size: 12px; }}
QPushButton#pwToggle {{
    background: transparent; border: none; border-radius: 6px;
    color: {PRIMARY}; font-size: 12px; font-weight: normal; padding: 3px 7px;
}}
QPushButton#pwToggle:hover {{ background: {PRIMARY_SOFT}; }}

QComboBox {{ padding: 6px 10px; min-width: 96px; }}
QComboBox::drop-down {{ border: none; width: 28px; }}
QComboBox::down-arrow {{ image: url("{chevron}"); width: 12px; height: 12px; }}
QComboBox QAbstractItemView {{
    background: {SURFACE}; border: 1px solid {BORDER};
    padding: 4px; outline: none;
    selection-background-color: {PRIMARY_SOFT}; selection-color: {PRIMARY};
}}

QCheckBox {{ spacing: 8px; color: {TEXT_SECONDARY}; }}
QCheckBox::indicator {{
    width: 16px; height: 16px; border-radius: 4px;
    border: 1px solid {BORDER_STRONG}; background: {SURFACE};
}}
QCheckBox::indicator:hover {{ border-color: {PRIMARY}; }}
QCheckBox::indicator:checked {{
    background: {PRIMARY}; border-color: {PRIMARY}; image: url("{check}");
}}

QSlider::groove:horizontal {{ height: 6px; background: #E6E9F2; border-radius: 3px; }}
QSlider::sub-page:horizontal {{ background: {PRIMARY}; border-radius: 3px; }}
QSlider::handle:horizontal {{
    width: 16px; height: 16px; margin: -6px 0;
    background: {SURFACE}; border: 2px solid {PRIMARY}; border-radius: 9px;
}}
QSlider::handle:horizontal:hover {{ background: {PRIMARY_SOFT}; }}

/* ---------- 按钮 ---------- */
QPushButton {{
    border-radius: 8px; padding: 8px 18px;
    font-size: 13px; font-weight: bold;
}}
QPushButton:focus {{ outline: none; }}
QPushButton[variant="primary"] {{
    background: {PRIMARY}; color: {SURFACE}; border: 1px solid {PRIMARY};
}}
QPushButton[variant="primary"]:hover {{ background: {PRIMARY_HOVER}; border-color: {PRIMARY_HOVER}; }}
QPushButton[variant="primary"]:pressed {{ background: {PRIMARY_PRESSED}; border-color: {PRIMARY_PRESSED}; }}
QPushButton[variant="primary"]:disabled {{
    background: {PRIMARY_DISABLED}; border-color: {PRIMARY_DISABLED}; color: {PRIMARY_SOFT};
}}
QPushButton[variant="secondary"] {{
    background: {SURFACE}; color: {PRIMARY}; border: 1px solid {PRIMARY_BORDER};
}}
QPushButton[variant="secondary"]:hover {{ background: {PRIMARY_SOFT}; border-color: {PRIMARY}; }}
QPushButton[variant="secondary"]:pressed {{ background: {PRIMARY_SOFT_HOVER}; }}
QPushButton[variant="secondary"]:disabled {{ color: {TEXT_MUTED}; border-color: {BORDER}; }}
QPushButton[variant="ghost"] {{
    background: transparent; color: {TEXT_SECONDARY}; border: 1px solid transparent;
}}
QPushButton[variant="ghost"]:hover {{ background: {SURFACE_MUTED}; color: {TEXT}; }}
QPushButton[variant="ghost"]:pressed {{ background: {BORDER}; }}
QPushButton[variant="ghost"]:disabled {{ color: {TEXT_MUTED}; }}
QPushButton[variant="mini"] {{
    background: transparent; color: {PRIMARY}; border: none;
    border-radius: 6px; padding: 3px 10px; font-size: 12px; min-width: 36px;
}}
QPushButton[variant="mini"]:hover {{ background: {PRIMARY_SOFT}; }}
QPushButton[variant="mini"]:pressed {{ background: {PRIMARY_SOFT_HOVER}; }}

/* ---------- 反馈 ---------- */
QLabel#toast {{
    border-radius: 10px; padding: 10px 18px;
    font-size: 13px; font-weight: bold;
}}
QLabel#toast[kind="success"] {{ background: {SUCCESS_SOFT}; color: {SUCCESS}; border: 1px solid {SUCCESS_BORDER}; }}
QLabel#toast[kind="error"] {{ background: {DANGER_SOFT}; color: {DANGER}; border: 1px solid {DANGER_BORDER}; }}
QLabel#toast[kind="info"] {{ background: {PRIMARY_SOFT}; color: {PRIMARY}; border: 1px solid {PRIMARY_BORDER}; }}

QLabel#resultBadge {{
    border-radius: 10px; padding: 12px 16px;
    font-size: 15px; font-weight: bold;
}}
QLabel#resultBadge[state="idle"] {{
    background: {SURFACE_MUTED}; color: {TEXT_MUTED}; border: 1px dashed {BORDER_STRONG};
    font-size: 13px; font-weight: normal;
}}
QLabel#resultBadge[state="match"] {{ background: {SUCCESS_SOFT}; color: {SUCCESS}; border: 1px solid {SUCCESS_BORDER}; }}
QLabel#resultBadge[state="mismatch"] {{ background: {DANGER_SOFT}; color: {DANGER}; border: 1px solid {DANGER_BORDER}; }}

/* ---------- 滚动条与菜单 ---------- */
QScrollBar:vertical {{ background: transparent; width: 10px; margin: 2px; }}
QScrollBar:horizontal {{ background: transparent; height: 10px; margin: 2px; }}
QScrollBar::handle:vertical {{ background: #CDD3DE; border-radius: 3px; min-height: 30px; }}
QScrollBar::handle:horizontal {{ background: #CDD3DE; border-radius: 3px; min-width: 30px; }}
QScrollBar::handle:hover {{ background: #AEB6C5; }}
QScrollBar::add-line, QScrollBar::sub-line {{ width: 0; height: 0; }}
QScrollBar::add-page, QScrollBar::sub-page {{ background: transparent; }}

QMenu {{ background: {SURFACE}; border: 1px solid {BORDER}; padding: 4px; }}
QMenu::item {{ padding: 6px 22px; border-radius: 6px; }}
QMenu::item:selected {{ background: {PRIMARY_SOFT}; color: {PRIMARY}; }}
QMenu::item:disabled {{ color: {TEXT_MUTED}; }}
QMenu::separator {{ height: 1px; background: {BORDER}; margin: 4px 8px; }}
"""


def apply_theme(app: QApplication) -> None:
    app.setStyle("Fusion")
    app.setFont(QFont(UI_FONT, 10))
    app.setStyleSheet(build_qss())
