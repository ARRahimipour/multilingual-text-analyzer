"""Qt desktop interface with native bidirectional text layout."""
from pathlib import Path
import sys
from PySide6.QtCore import Qt, QTimer, QSignalBlocker
from PySide6.QtGui import QFont, QFontDatabase, QTextCursor, QKeySequence, QShortcut
from PySide6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QCheckBox, QTextEdit, QTableWidget, QTableWidgetItem,
    QHeaderView, QSplitter, QFileDialog, QMessageBox, QAbstractItemView)
from .core import AnalysisOptions, analyze
from .direction import text_direction
from .reports import render_report
from .identity import AUTHOR_LINES, AUTHOR_EMAIL, AUTHOR_WEBSITE


class AnalyzerWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.input_path = None
        self.result = None
        self.font_size = 15
        self.setWindowTitle('NLP Text Analyzer v1.3.1 | ARRahimipour')
        self.resize(1180, 880)
        self.setMinimumSize(850, 720)
        families = {f.casefold(): f for f in QFontDatabase.families()}
        self.family = next((families[f.casefold()] for f in ('Tahoma', 'Segoe UI', 'Arial')
                            if f.casefold() in families), QApplication.font().family())
        self.setStyleSheet('''
            QWidget { background:#f2f5f9; color:#192637; }
            QLabel#title { font-size:32px; font-weight:bold; }
            QLabel#metric { font-size:30px; font-weight:bold; color:#176b61; }
            QPushButton { padding:8px 12px; border:1px solid #ccd6e0; border-radius:5px; }
            QPushButton:hover { background:#e1eaeF; }
            QTextEdit, QTableWidget { background:white; border:1px solid #d7e0e8; }
            QTableWidget { alternate-background-color:#f2f6fa; }
            QHeaderView::section { padding:9px; background:#e6edf2; border:0; font-weight:bold; }
        ''')
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(12)
        title = QLabel('Language, counted.'); title.setObjectName('title'); layout.addWidget(title)
        layout.addWidget(QLabel('NLP / SESSION 01 · Sentence, word and frequency analysis'))
        toolbar = QHBoxLayout(); layout.addLayout(toolbar)
        for name, callback in [('Open text', self.open_file), ('Load sample', self.load_sample),
                               ('Export report', self.export), ('Clear', self.clear)]:
            button = QPushButton(name); button.clicked.connect(callback); toolbar.addWidget(button)
        toolbar.addStretch(); toolbar.addWidget(QLabel('Text size'))
        for name, delta in [('A+', 1), ('A−', -1)]:
            button = QPushButton(name); button.clicked.connect(lambda checked=False, d=delta: self.resize_text(d))
            toolbar.addWidget(button)
        options = QHBoxLayout(); layout.addLayout(options)
        self.case = QCheckBox('Case sensitive')
        self.persian = QCheckBox('Persian letter normalization')
        self.numbers = QCheckBox('Include numbers')
        for option in (self.case, self.persian, self.numbers):
            options.addWidget(option); option.toggled.connect(self.refresh)
        options.addStretch()
        metrics = QHBoxLayout(); layout.addLayout(metrics); self.metric_labels = []
        for name in ('Sentences', 'Words', 'Unique words', 'Appear once'):
            box = QVBoxLayout(); value = QLabel('0'); value.setObjectName('metric')
            box.addWidget(value); box.addWidget(QLabel(name)); metrics.addLayout(box, 1)
            self.metric_labels.append(value)
        panels = QSplitter(Qt.Orientation.Horizontal); layout.addWidget(panels, 1)
        left = QWidget(); left_layout = QVBoxLayout(left); left_layout.setContentsMargins(0, 0, 8, 0)
        left_layout.addWidget(QLabel('INPUT TEXT · UTF-8'))
        self.editor = QTextEdit()
        self.editor.setAcceptRichText(False)
        self.editor.setLineWrapMode(QTextEdit.LineWrapMode.WidgetWidth)
        self.editor.document().setDocumentMargin(20)
        self.editor.setPlaceholderText('Paste or type text in any language…')
        left_layout.addWidget(self.editor); panels.addWidget(left)
        right = QWidget(); right_layout = QVBoxLayout(right); right_layout.setContentsMargins(8, 0, 0, 0)
        right_layout.addWidget(QLabel('TOP 10 WORDS'))
        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(['Rank', 'Word', 'Count'])
        self.table.verticalHeader().hide(); self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setShowGrid(False)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(0, 65); self.table.setColumnWidth(2, 85)
        right_layout.addWidget(self.table); panels.addWidget(right); panels.setSizes([660, 420])
        self.status = QLabel(); self.status.setWordWrap(True); layout.addWidget(self.status)
        layout.addWidget(QLabel('Offline analysis · Numbers are excluded unless Include numbers is selected.'))
        author = QLabel('<b>' + AUTHOR_LINES[0] + '</b><br>' + '<br>'.join(AUTHOR_LINES[1:3]) +
                        f'<br><a href="mailto:{AUTHOR_EMAIL}">{AUTHOR_EMAIL}</a>' +
                        f'<br><a href="https://{AUTHOR_WEBSITE}">{AUTHOR_WEBSITE}</a>')
        author.setOpenExternalLinks(True); author.setWordWrap(True); layout.addWidget(author)
        self.timer = QTimer(self); self.timer.setSingleShot(True); self.timer.setInterval(180)
        self.timer.timeout.connect(self.refresh)
        self.editor.textChanged.connect(lambda: self.timer.start())
        QShortcut(QKeySequence('Ctrl+O'), self, activated=self.open_file)
        QShortcut(QKeySequence('Ctrl+S'), self, activated=self.export)
        self.resize_text(0); self.refresh()

    def resize_text(self, delta):
        self.font_size = max(11, min(24, self.font_size + delta))
        font = QFont(self.family, self.font_size)
        self.editor.setFont(font); self.table.setFont(font)
        self.table.verticalHeader().setDefaultSectionSize(max(42, self.table.fontMetrics().height() + 18))

    def apply_direction(self):
        """Set actual paragraph direction, preserving logical source and selection."""
        document = self.editor.document()
        dominant = text_direction(self.editor.toPlainText())
        changes = []
        block = document.begin()
        while block.isValid():
            text = block.text()
            rtl = (text_direction(text) if any(c.isalpha() for c in text) else dominant) == 'rtl'
            direction = Qt.LayoutDirection.RightToLeft if rtl else Qt.LayoutDirection.LeftToRight
            alignment = Qt.AlignmentFlag.AlignRight if rtl else Qt.AlignmentFlag.AlignLeft
            fmt = block.blockFormat()
            if fmt.layoutDirection() != direction or fmt.alignment() != alignment:
                fmt.setLayoutDirection(direction); fmt.setAlignment(alignment)
                fmt.setLeftMargin(6); fmt.setRightMargin(6)
                changes.append((block, fmt))
            block = block.next()
        if changes:
            # Formatting accompanies the preceding edit instead of adding an undo step.
            blocker = QSignalBlocker(self.editor)
            cursor = QTextCursor(document)
            cursor.joinPreviousEditBlock()
            for block, fmt in changes:
                cursor.setPosition(block.position()); cursor.setBlockFormat(fmt)
            cursor.endEditBlock()
            del blocker

    def refresh(self):
        self.timer.stop()
        self.apply_direction()
        self.result = analyze(self.editor.toPlainText(), AnalysisOptions(
            case_sensitive=self.case.isChecked(), persian_normalization=self.persian.isChecked(),
            include_numbers=self.numbers.isChecked()))
        values = (self.result.sentence_count, self.result.word_count,
                  self.result.unique_word_count, self.result.singleton_word_count)
        for label, value in zip(self.metric_labels, values): label.setText(str(value))
        self.table.setRowCount(len(self.result.top_words))
        for index, row in enumerate(self.result.top_words):
            for column, value in enumerate((index + 1, row['word'], row['count'])):
                item = QTableWidgetItem(str(value))
                alignment = Qt.AlignmentFlag.AlignCenter
                if column == 1:
                    alignment = Qt.AlignmentFlag.AlignRight if text_direction(str(value)) == 'rtl' else Qt.AlignmentFlag.AlignLeft
                    alignment |= Qt.AlignmentFlag.AlignVCenter
                item.setTextAlignment(alignment); self.table.setItem(index, column, item)
        self.status.setText('Analysis complete · No word-count limit' +
                            (' | ' + self.result.warnings[0] if self.result.warnings else ''))

    def set_text(self, text):
        self.editor.setPlainText(text); self.refresh()

    def open_file(self):
        path, _ = QFileDialog.getOpenFileName(self, 'Open text', '', 'Text files (*.txt);;All files (*)')
        if path: self.read_file(Path(path))

    def read_file(self, path):
        try:
            text = path.read_text(encoding='utf-8-sig')
            self.input_path = path.resolve(); self.set_text(text)
        except (OSError, UnicodeError) as exc: QMessageBox.critical(self, 'Cannot open file', str(exc))

    def load_sample(self):
        self.read_file(Path(__file__).resolve().parent.parent / 'examples' / 'english_300.txt')

    def clear(self):
        self.input_path = None; self.set_text('')

    def export(self):
        self.refresh()
        path, selected = QFileDialog.getSaveFileName(self, 'Save report', 'analysis.html',
            'HTML report (*.html);;JSON report (*.json);;CSV vocabulary (*.csv);;Text report (*.txt)')
        if not path: return
        destination = Path(path)
        if not destination.suffix:
            extension = selected.split('*.')[-1].split(')')[0]
            destination = destination.with_suffix('.' + extension)
        formats = {'.html': 'html', '.json': 'json', '.csv': 'csv', '.txt': 'text'}
        format = formats.get(destination.suffix.lower())
        if not format:
            QMessageBox.warning(self, 'Unsupported format', 'Choose .html, .json, .csv, or .txt.'); return
        if self.input_path == destination.resolve():
            QMessageBox.warning(self, 'Cannot overwrite input', 'Choose a different output filename.'); return
        try:
            destination.write_text(render_report(self.result, format), encoding='utf-8')
            QMessageBox.information(self, 'Report saved', str(destination))
        except OSError as exc: QMessageBox.critical(self, 'Cannot save report', str(exc))


def launch():
    app = QApplication.instance() or QApplication(sys.argv[:1])
    window = AnalyzerWindow(); window.show()
    app.exec()
