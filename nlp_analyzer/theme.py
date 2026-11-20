"""Compact, accessible dark theme for the local research workstation.

No remote fonts, theme packages or images. All widgets remain native Qt.
"""

STYLE = r'''
QWidget, QDialog {
    background-color: #0B1220;
    color: #E9F0FC;
    font-family: "Segoe UI", "Tahoma", "Arial";
    font-size: 11pt;
}
QLabel { background: transparent; color: #D4DFEF; }
QLabel#eyebrow { color: #67E1D1; font-size: 10pt; font-weight: 700; }
QLabel#title { color: #F5FAFF; font-size: 27pt; font-weight: 750; }
QLabel#subtitle { color: #9CACCA; font-size: 10pt; }
QLabel#section { color: #DCE8FB; font-size: 11pt; font-weight: 700; }
QLabel#hint { color: #97AFC8; font-size: 10pt; }
QLabel#metric { color: #71E6D4; font-size: 23pt; font-weight: 700; }
QLabel#metricCaption { color: #9CACCA; font-size: 9pt; }
QLabel#status { color: #8FDCCF; font-size: 10pt; }
QFrame#card, QWidget#card { background-color: #142139; border: 1px solid #2A3A56; border-radius: 15px; }
QFrame#metricCard { background-color: #15253B; border: 1px solid #2B415E; border-radius: 13px; }
QFrame#hero { background-color: #101F36; border: 1px solid #29445C; border-radius: 17px; }
QFrame#line { background-color: #2A3852; max-height: 1px; }
QGroupBox {
    background: #111D30; border: 1px solid #2B3B54; border-radius: 12px;
    margin-top: 12px; padding: 17px 12px 12px 12px; font-weight: 650;
    color: #E2ECFD;
}
QGroupBox::title { subcontrol-origin: margin; left: 13px; padding: 0 6px; }
QPushButton {
    color: #E6F0FC; background: #1A2942; border: 1px solid #354763;
    border-radius: 9px; padding: 9px 14px; font-size: 10pt; font-weight: 600;
    min-height: 20px;
}
QPushButton:hover { background: #263A59; border-color: #597DA3; }
QPushButton:pressed { background: #0A3A4A; }
QPushButton:disabled { color: #70819C; background: #111A2B; }
QPushButton#primary { color: #071726; background: #67E1D1; border: 1px solid #67E1D1; font-weight: 750; }
QPushButton#primary:hover { background: #95F5E6; border-color: #95F5E6; }
QPushButton#secondary { color: #B7CFFF; background: #192C4A; border-color: #385A87; }
QPushButton#secondary:hover { background: #223F65; }
QPushButton#stageStep {
    background: #182C45; color: #C5D7EC; border: 1px solid #344D6D;
    padding: 7px 10px; font-size: 9.5pt; font-weight: 650;
    min-height: 24px;
}
QPushButton#stageStep:hover { background: #24435A; border-color: #68CFCB; }
QPushButton#stageStep:checked {
    color: #08202D; background: #78EBDB; border: 2px solid #A6FFF2;
    font-weight: 750;
}
QWidget#page { background-color: #0B1220; }
QScrollArea#pageScroll { background-color: #0B1220; border: none; }
QCheckBox { color: #D9E4F5; spacing: 7px; background: transparent; font-size: 10pt; }
QCheckBox::indicator { width: 16px; height: 16px; border: 1px solid #60728D; border-radius: 5px; background: #0C1729; }
QCheckBox::indicator:checked { background: #67E1D1; border-color: #67E1D1; image: none; }
QComboBox, QSpinBox, QLineEdit {
    color: #EAF2FF; background: #101B2F; border: 1px solid #32445F;
    border-radius: 8px; padding: 6px 10px; min-height: 24px;
    selection-background-color: #286E83;
}
QComboBox:hover, QSpinBox:hover { border-color: #64B2D6; }
QComboBox::drop-down { border: none; width: 22px; }
QComboBox QAbstractItemView { background: #182742; color: #EAF2FF; selection-background-color: #264F64; }
QTextEdit, QTextBrowser, QPlainTextEdit {
    background: #0E192B; color: #EFF7FF; border: 1px solid #34435F;
    border-radius: 10px; padding: 10px; selection-background-color: #247D88;
    font-family: "Segoe UI", "Tahoma", "Arial"; font-size: 11pt;
}
QTextEdit:focus, QPlainTextEdit:focus { border-color: #69C7D7; }
QTextEdit[readOnly="true"] { background: #12213A; }
QTableWidget { background: #102039; alternate-background-color: #172841;
    border: 1px solid #34435F; border-radius: 10px; color: #EAF2FF;
    gridline-color: #273A55; selection-background-color: #23515F; }
QHeaderView::section { background: #223550; color: #D7ECF8; border: 0; padding: 10px; font-weight: 700; }
QTabWidget::pane { border: 1px solid #2E415F; border-radius: 9px; top: -1px; }
QTabBar::tab { background: #13243B; color: #9BACCA; border: 1px solid #2B3C59;
    border-bottom: none; padding: 11px 15px; min-width: 75px; }
QTabBar::tab:selected { color: #7DF1DC; background: #1C2E4B; border-bottom: 2px solid #67E1D1; }
QTabBar::tab:hover { color: #EAF2FF; }
QListWidget { background: #101C31; color: #C2D3E8; border: 1px solid #2B3C59;
    border-radius: 10px; padding: 7px; outline: none; }
QListWidget::item { margin: 4px; padding: 13px 9px; border-radius: 8px; }
QListWidget::item:selected { color: #74F2DF; background: #1B3B50; border-left: 3px solid #67E1D1; }
QListWidget::item:hover { background: #233551; }
QSplitter::handle { background: #20304C; width: 5px; }
QScrollArea { border: 0; background: transparent; }
QScrollBar:vertical { background: #0B1526; width: 10px; margin: 2px; }
QScrollBar::handle:vertical { background: #344961; min-height: 26px; border-radius: 5px; }
QScrollBar:horizontal { background: #0B1526; height: 10px; }
QScrollBar::handle:horizontal { background: #344961; min-width: 26px; border-radius: 5px; }
QScrollBar::add-line, QScrollBar::sub-line { width: 0; height: 0; }
QMessageBox { background: #15243D; }
QToolTip { background: #213652; color: #F2F9FF; border: 1px solid #577B9A; padding: 8px; }
'''
