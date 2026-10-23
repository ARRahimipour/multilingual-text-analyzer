"""Qt desktop interface with native bidirectional text layout."""
from pathlib import Path
from dataclasses import replace
import sys
from PySide6.QtCore import Qt, QTimer, QSignalBlocker
from PySide6.QtGui import QFont, QFontDatabase, QTextCursor, QKeySequence, QShortcut
from PySide6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QCheckBox, QTextEdit, QTableWidget, QTableWidgetItem,
    QHeaderView, QSplitter, QFileDialog, QMessageBox, QAbstractItemView,
    QComboBox, QGroupBox, QGridLayout, QInputDialog)
from .core import AnalysisOptions, analyze
from .dataset import clean_dataset
from .preprocessing import PRESET_NAMES, preset
from .direction import text_direction
from .reports import render_report
from .identity import AUTHOR_LINES, AUTHOR_EMAIL, AUTHOR_WEBSITE


class AnalyzerWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.input_path = None
        self.result = None
        self.font_size = 15
        self.setWindowTitle('NLP Text Analyzer v2.0 | ARRahimipour')
        self.resize(1260, 950)
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
        layout.addWidget(QLabel('NLP / SESSIONS 01–02 · Text cleaning, Unicode and frequency analysis'))
        toolbar = QHBoxLayout(); layout.addLayout(toolbar)
        for name, callback in [('Open text', self.open_file), ('Load sample', self.load_sample),
                               ('Clean dataset', self.clean_dataset_file),
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
        cleaning_box = QGroupBox('Session 2 · task-dependent cleaning (raw input is never changed)')
        cleaning_grid = QGridLayout(cleaning_box)
        self.clean_preset = QComboBox()
        self.clean_preset.addItems(['Raw (no cleaning)'] + [name.capitalize() for name in PRESET_NAMES])
        self.emoji_mode = QComboBox(); self.emoji_mode.addItems(['keep', 'remove', 'label'])
        self.punctuation_mode = QComboBox(); self.punctuation_mode.addItems(['keep', 'normalize', 'remove'])
        self.number_mode = QComboBox(); self.number_mode.addItems(['keep', 'remove', 'placeholder'])
        self.digit_style = QComboBox(); self.digit_style.addItems(['keep', 'ascii', 'persian'])
        self.invisible_mode = QComboBox(); self.invisible_mode.addItems(['none', 'safe', 'controls'])
        combos = [('Preset', self.clean_preset), ('Emoji', self.emoji_mode),
                  ('Punctuation', self.punctuation_mode), ('Numbers', self.number_mode),
                  ('Digits', self.digit_style), ('Invisibles', self.invisible_mode)]
        for index, (name, widget) in enumerate(combos):
            cleaning_grid.addWidget(QLabel(name), 0, index)
            cleaning_grid.addWidget(widget, 1, index)
        self.mask_pii = QCheckBox('Mask PII')
        self.keep_urls = QCheckBox('Keep URLs')
        self.keep_mentions = QCheckBox('Keep mentions')
        self.keep_hashtags = QCheckBox('Keep #')
        self.remove_diacritics = QCheckBox('Remove diacritics')
        self.join_lines = QCheckBox('Fix PDF line breaks')
        self.collapse_punct = QCheckBox('Collapse !!!!')
        self.reduce_elongations = QCheckBox('Reduce long letters')
        self.remove_retweets = QCheckBox('Remove RT marker')
        self.advanced = [self.emoji_mode, self.punctuation_mode, self.number_mode,
                         self.digit_style, self.invisible_mode, self.mask_pii,
                         self.keep_urls, self.keep_mentions, self.keep_hashtags,
                         self.remove_diacritics, self.join_lines, self.collapse_punct,
                         self.reduce_elongations, self.remove_retweets]
        for index, widget in enumerate(self.advanced[5:]):
            cleaning_grid.addWidget(widget, 2 + index // 7, index % 7)
        layout.addWidget(cleaning_box)
        self.clean_preset.currentIndexChanged.connect(self.change_preset)
        for widget in self.advanced:
            if isinstance(widget, QComboBox): widget.currentIndexChanged.connect(self.refresh)
            else: widget.toggled.connect(self.refresh)
        self.change_preset()
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
        left_layout.addWidget(QLabel('CLEANED PREVIEW · original text stays editable above'))
        self.clean_preview = QTextEdit()
        self.clean_preview.setReadOnly(True)
        self.clean_preview.setMaximumHeight(125)
        self.clean_preview.setPlaceholderText('Choose a cleaning preset to inspect the result.')
        left_layout.addWidget(self.clean_preview)
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
        layout.addWidget(QLabel('Offline analysis · Cleaning is opt-in · Sentence detection occurs before punctuation removal.'))
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
        self.editor.setFont(font); self.table.setFont(font); self.clean_preview.setFont(font)
        self.table.verticalHeader().setDefaultSectionSize(max(42, self.table.fontMetrics().height() + 18))

    def change_preset(self):
        active = self.clean_preset.currentIndex() > 0
        for widget in self.advanced: widget.setEnabled(active)
        if active:
            settings = preset(PRESET_NAMES[self.clean_preset.currentIndex() - 1])
            for combo, value in ((self.emoji_mode, settings.emoji_mode),
                                 (self.punctuation_mode, settings.punctuation_mode),
                                 (self.number_mode, settings.number_mode),
                                 (self.digit_style, settings.digit_style),
                                 (self.invisible_mode, settings.invisible_mode)):
                combo.blockSignals(True); combo.setCurrentText(value); combo.blockSignals(False)
            for checkbox, value in ((self.mask_pii, settings.mask_pii),
                                    (self.keep_urls, not settings.remove_urls),
                                    (self.keep_mentions, not settings.remove_mentions),
                                    (self.keep_hashtags, not settings.strip_hashtags),
                                    (self.remove_diacritics, settings.remove_diacritics),
                                    (self.join_lines, settings.join_broken_lines),
                                    (self.collapse_punct, settings.collapse_repeated_punctuation),
                                    (self.reduce_elongations, settings.reduce_elongations),
                                    (self.remove_retweets, settings.remove_retweet_marker)):
                checkbox.blockSignals(True); checkbox.setChecked(value); checkbox.blockSignals(False)
        if hasattr(self, 'timer'):
            self.refresh()

    def preprocessing_options(self):
        if self.clean_preset.currentIndex() == 0:
            return None
        settings = preset(PRESET_NAMES[self.clean_preset.currentIndex() - 1])
        return replace(settings, emoji_mode=self.emoji_mode.currentText(),
                       punctuation_mode=self.punctuation_mode.currentText(),
                       number_mode=self.number_mode.currentText(),
                       digit_style=self.digit_style.currentText(),
                       invisible_mode=self.invisible_mode.currentText(),
                       mask_pii=self.mask_pii.isChecked(), remove_urls=not self.keep_urls.isChecked(),
                       remove_mentions=not self.keep_mentions.isChecked(),
                       strip_hashtags=not self.keep_hashtags.isChecked(),
                       remove_diacritics=self.remove_diacritics.isChecked(),
                       join_broken_lines=self.join_lines.isChecked(),
                       collapse_repeated_punctuation=self.collapse_punct.isChecked(),
                       reduce_elongations=self.reduce_elongations.isChecked(),
                       remove_retweet_marker=self.remove_retweets.isChecked())

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
            # Use physical edges: Qt otherwise mirrors AlignRight in RTL blocks.
            alignment |= Qt.AlignmentFlag.AlignAbsolute
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
            include_numbers=self.numbers.isChecked(), preprocessing=self.preprocessing_options()))
        preview = self.result.cleaned_text if self.preprocessing_options() is not None else ''
        self.clean_preview.setPlainText(preview)
        self.clean_preview.setLayoutDirection(Qt.LayoutDirection.RightToLeft
            if text_direction(preview) == 'rtl' else Qt.LayoutDirection.LeftToRight)
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
                    alignment |= Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignAbsolute
                item.setTextAlignment(alignment); self.table.setItem(index, column, item)
        changes = self.result.cleaning_statistics
        cleaned_status = (f' · {changes["characters_before"]} → {changes["characters_after"]} characters'
                          if changes else ' · raw mode')
        self.status.setText('Analysis complete · No word-count limit' + cleaned_status +
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

    def clean_dataset_file(self):
        source, _ = QFileDialog.getOpenFileName(self, 'Open dataset', '',
            'Datasets (*.csv *.tsv *.jsonl)')
        if not source: return
        column, okay = QInputDialog.getText(self, 'Text column', 'Text field / column:', text='text')
        if not okay or not column.strip(): return
        original = Path(source)
        destination, _ = QFileDialog.getSaveFileName(self, 'Save cleaned dataset',
            str(original.with_name(original.stem + '_cleaned' + original.suffix)),
            'Datasets (*.csv *.tsv *.jsonl)')
        if not destination: return
        try:
            settings = self.preprocessing_options() or preset('general')
            summary = clean_dataset(source, destination, settings, text_column=column.strip())
            QMessageBox.information(self, 'Dataset cleaned',
                f'Kept {summary["kept"]} / {summary["input"]} rows.\n'
                f'Removed: {summary["reasons"]}\nOutput: {destination}\n'
                'Script ratio is heuristic; names and other columns are not automatically anonymized.')
        except (OSError, ValueError, UnicodeError) as exc:
            QMessageBox.critical(self, 'Cannot clean dataset', str(exc))

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
