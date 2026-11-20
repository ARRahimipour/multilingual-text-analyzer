"""Qt desktop interface with native bidirectional text layout."""
from pathlib import Path
from dataclasses import replace
import sys
from PySide6.QtCore import Qt, QTimer, QSignalBlocker
from PySide6.QtGui import QFont, QFontDatabase, QTextCursor, QKeySequence, QShortcut, QGuiApplication
from PySide6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QCheckBox, QTextEdit, QTableWidget, QTableWidgetItem,
    QHeaderView, QSplitter, QFileDialog, QMessageBox, QAbstractItemView,
    QComboBox, QGroupBox, QGridLayout, QInputDialog, QFrame, QScrollArea)
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
        self.setWindowTitle('LEXIS Research Studio | NLP Text Analyzer')
        available = (QGuiApplication.primaryScreen().availableGeometry()
                     if QGuiApplication.primaryScreen() else None)
        self.setMinimumSize(530, 380)
        if available:
            w = min(1390, max(530, available.width() - 32))
            h = min(800, max(380, available.height() - 60))
            self.resize(w, h)
            self.move(available.x() + (available.width() - w)//2,
                      available.y() + (available.height() - h)//2)
        else:
            self.resize(1100, 700)
        families = {f.casefold(): f for f in QFontDatabase.families()}
        self.family = next((families[f.casefold()] for f in ('Tahoma', 'Segoe UI', 'Arial')
                            if f.casefold() in families), QApplication.font().family())
        from .theme import STYLE
        self.setStyleSheet(STYLE)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        outer.addWidget(scroll)
        page = QWidget()
        scroll.setWidget(page)
        layout = QVBoxLayout(page)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(8)
        layout.addWidget(QLabel('LEXIS  /  NLP RESEARCH WORKSPACE'))
        title = QLabel('Language, understood.'); title.setObjectName('title'); layout.addWidget(title)
        subtitle = QLabel('TEXT ANALYTICS  /  Six-stage preprocessing  /  Explainable, local experiments')
        subtitle.setObjectName('subtitle'); layout.addWidget(subtitle)
        toolbar = QGridLayout()
        toolbar.setSpacing(6)
        layout.addLayout(toolbar)
        actions = [('Open text', self.open_file), ('Load sample', self.load_sample),
                               ('Clean dataset', self.clean_dataset_file),
                               ('Course Lab', self.open_course_lab),
                               ('06  /  Six-stage pipeline', self.open_six_stage_pipeline),
                               ('Export report', self.export), ('Clear', self.clear)]
        for i, (name, callback) in enumerate(actions):
            button = QPushButton(name)
            button.clicked.connect(callback)
            toolbar.addWidget(button, i // 4, i % 4)
            if name.startswith('06  /'):
                button.setObjectName('primary')
        toolbar.addWidget(QLabel('Text size'), 1, 3)
        for i, (name, delta) in enumerate([('A+', 1), ('A−', -1)]):
            button = QPushButton(name)
            button.clicked.connect(lambda checked=False, d=delta: self.resize_text(d))
            toolbar.addWidget(button, 2, i)
        options = QGridLayout(); options.setSpacing(7); layout.addLayout(options)
        self.case = QCheckBox('Case sensitive')
        self.persian = QCheckBox('Persian letter normalization')
        self.numbers = QCheckBox('Include numbers')
        for i, option in enumerate((self.case, self.persian, self.numbers)):
            options.addWidget(option, 0, i)
            option.toggled.connect(self.refresh)
        self.toggle_cleaning = QPushButton('Advanced cleaning  ▾')
        self.toggle_cleaning.setCheckable(True)
        self.toggle_cleaning.setToolTip('Show task-dependent cleaning choices; the original input is always preserved.')
        self.toggle_cleaning.toggled.connect(self.toggle_advanced_cleaning)
        options.addWidget(self.toggle_cleaning, 1, 0, 1, 2)
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
            row, col = divmod(index, 3)
            cleaning_grid.addWidget(QLabel(name), row * 2, col)
            cleaning_grid.addWidget(widget, row * 2 + 1, col)
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
            cleaning_grid.addWidget(widget, 4 + index // 3, index % 3)
        layout.addWidget(cleaning_box)
        cleaning_box.setVisible(False)
        self.advanced_cleaning_box = cleaning_box
        self.clean_preset.currentIndexChanged.connect(self.change_preset)
        for widget in self.advanced:
            if isinstance(widget, QComboBox): widget.currentIndexChanged.connect(self.refresh)
            else: widget.toggled.connect(self.refresh)
        self.change_preset()
        metrics = QHBoxLayout(); metrics.setSpacing(11); layout.addLayout(metrics); self.metric_labels = []
        for name in ('Sentences', 'Words', 'Unique words', 'Appear once'):
            metric_card = QFrame(); metric_card.setObjectName('metricCard')
            box = QVBoxLayout(metric_card); box.setContentsMargins(18, 9, 18, 10); box.setSpacing(1)
            value = QLabel('0'); value.setObjectName('metric')
            caption = QLabel(name.upper()); caption.setObjectName('metricCaption')
            box.addWidget(value); box.addWidget(caption); metrics.addWidget(metric_card, 1)
            self.metric_labels.append(value)
        panels = QSplitter(Qt.Orientation.Horizontal)
        panels.setMinimumHeight(320)
        layout.addWidget(panels, 1)
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
        hint = QLabel('01  Paste text    →    02  Open Six-stage pipeline    →    03  Inspect every transformation and export the audit')
        hint.setObjectName('hint'); layout.addWidget(hint)
        author = QLabel('<b>' + AUTHOR_LINES[0] + '</b>  ·  ' + AUTHOR_LINES[1] +
                        f'  ·  <a href="https://{AUTHOR_WEBSITE}">{AUTHOR_WEBSITE}</a>')
        author.setOpenExternalLinks(True); author.setWordWrap(True); layout.addWidget(author)
        self.timer = QTimer(self); self.timer.setSingleShot(True); self.timer.setInterval(180)
        self.timer.timeout.connect(self.refresh)
        self.editor.textChanged.connect(lambda: self.timer.start())
        QShortcut(QKeySequence('Ctrl+O'), self, activated=self.open_file)
        QShortcut(QKeySequence('Ctrl+S'), self, activated=self.export)
        self.resize_text(0); self.refresh()

    def toggle_advanced_cleaning(self, enabled):
        self.advanced_cleaning_box.setVisible(enabled)
        self.toggle_cleaning.setText('Advanced cleaning  ▴' if enabled else 'Advanced cleaning  ▾')

    def open_six_stage_pipeline(self):
        from .six_stage_gui import SixStageStudio
        self.six_studio = SixStageStudio(self.editor.toPlainText(), self)
        self.six_studio.show()

    def open_course_lab(self):
        from .lab_gui import CourseLab
        self.course_lab = CourseLab(self.editor.toPlainText(), self)
        self.course_lab.show()

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
