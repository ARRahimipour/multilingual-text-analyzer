"""Focused, English-language six-stage preprocessing laboratory.

The source is immutable during an experiment; the six-stage core is shared
with the CLI. All result panels and JSON exports come from that same core.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from html import escape

from PySide6.QtCore import Qt, QObject, QThread, Signal, Slot
from PySide6.QtGui import QFont, QFontDatabase, QGuiApplication
from PySide6.QtWidgets import (
    QCheckBox, QComboBox, QDialog, QFileDialog, QFrame, QGridLayout,
    QHBoxLayout, QLabel, QLineEdit, QMessageBox, QPushButton,
    QScrollArea, QSizePolicy, QSplitter, QTabWidget, QTextBrowser, QTextEdit, QVBoxLayout, QWidget,
)

from .direction import text_direction
from .six_stage_pipeline import run_six_stage_pipeline
from .spacing_inspection import visible_spaces, spacing_counts
from .demo_library import DEMO_CASES


STAGES = (
    ('01  Raw input', 'Untouched baseline',
     'Preserve the original source. No destructive processing takes place in this step.'),
    ('02  Cleaning', 'Remove unwanted noise',
     'Remove HTML and URLs. Emoji, punctuation and numbers follow the selected task profile.'),
    ('03  Normalization', 'Standardize Persian Unicode and spacing',
     'Unify Arabic/Persian letters and digits; repair spaces and ZWNJ. Repeating this step should not change the result.'),
    ('04  Tokenization', 'Split into sentences and lexical tokens',
     'Detect sentence boundaries before optional punctuation deletion; keep Persian half-spaces within words.'),
    ('05  Stopwords', 'Optional information filtering',
     'Remove frequent functional words only if the task benefits. Protect negations such as not and نیست.'),
    ('06  Stemming / Lemmatization', 'Reduce word forms to a base representation',
     'Choose stemming OR lemmatization, not both. Inspect every token-to-result mapping.'),
)


SAMPLE_FALLBACK = (
    'سلاااام! من امروز درباره‌ی پردازش زبان طبیعی صحبت می‌کنم.\n'
    'دانشجویان کتاب ها و كتاب‌هاي جدید را می خوانند. می‌روم، می روم و ميروم.\n'
    'این برنامه ۱۲۳ و 123 را بررسی می‌کند. <p>متن HTML</p> https://example.com 😊\n'
    'کتاب‌ها خوب هستند، اما بعضی متن‌ها خوب نیستند.'
)


def stage_audit(stage: dict) -> str:
    number = stage['number']
    lines = [f"STAGE {number:02d}  /  {stage['english'].upper()}",
             'The values below come from the actual pipeline execution.', '']
    if number == 1:
        lines.extend((f"Characters: {stage['characters']}", f"UTF-8 bytes: {stage['utf8_bytes']}",
                      'Source was preserved: yes'))
    if number == 2:
        lines.extend((f"Before: {stage['before_characters']} characters",
                      f"After: {stage['after_characters']} characters", '', 'Cleaning operations:'))
        for name, item in stage['cleaning_changes'].items():
            lines.append(f"  {'CHANGED' if item['changed'] else 'unchanged':9} {name}")
        lines.extend(('', 'Sentence-boundary snapshot is preserved in the full JSON.'))
    if number == 3:
        lines.extend((f"Idempotent (2nd pass unchanged): {'YES' if stage['idempotent'] else 'NO'}", '',
                      'Unicode and whitespace diagnostics (before → after):',
                      *(f"  {name}: {stage.get('spacing_before', {}).get(name, '?')} → {value}"
                        for name, value in stage.get('spacing_after', spacing_counts(stage['output'])).items()),
                      '', 'Normalization operations:'))
        for item in stage['normalization_changes']:
            lines.append(f"  {'CHANGED' if item['changed'] else 'unchanged':9} {item['stage']}")
        lines.extend(('', 'Inspection tip: enable “Show spaces & ZWNJ” to distinguish U+0020 from U+200C.'))
    if number >= 4:
        lines.extend((f"Tokens: {stage['token_count']}", f"Distinct terms: {stage['type_count']}",
                      f"Type-token ratio: {stage['type_token_ratio']:.3f}",
                      f"Singletons: {stage['singleton_count']}", '', 'Top 10 terms:'))
        lines.extend(f"  {item['word']}  ×  {item['count']}" for item in stage['top_10'])
    if number == 4:
        lines.extend(('', f"Tokenizer: {stage['backend']}", f"Sentences: {stage['sentence_count']}", '',
                      'Sentence boundaries:'))
        lines.extend(f'  {i}. {sentence}' for i, sentence in enumerate(stage['sentences'], 1))
    if number == 5:
        lines.extend(('', f"Stopword filter: {'enabled' if stage['enabled'] else 'disabled'}",
                      f"Method: {stage['mode']}", f"Removed: {stage['removed_count']}",
                      f"Preserve negations: {stage['preserve_negation']}",
                      'Removed terms: ' + (', '.join(stage['removed_tokens']) or '(none)')))
    if number == 6:
        lines.extend(('', f"Morphological method: {stage['method']}", f"Backend: {stage['backend']}", '',
                      'Token → output mappings:'))
        lines.extend(f"  {item['token']}  →  {item['result']}" + ('  [protected]' if item['protected'] else '')
                     for item in stage['mappings'])
        lines.append('')
        lines.append('Note: Stemming may produce non-dictionary roots; lemmas depend on the language model.')
    return '\n'.join(lines)


class PipelineWorker(QObject):
    complete = Signal(object)
    failed = Signal(str)
    finished = Signal()

    def __init__(self, source: str, settings: dict):
        super().__init__()
        self.source, self.settings = source, settings

    @Slot()
    def run(self):
        try:
            self.complete.emit(run_six_stage_pipeline(self.source, **self.settings))
        except Exception as exc:
            self.failed.emit(f'{type(exc).__name__}: {exc}')
        finally:
            self.finished.emit()


class SixStageStudio(QDialog):
    def __init__(self, text='', parent=None):
        super().__init__(parent)
        self.setWindowTitle('LEXIS Studio  |  Six-Stage NLP Pipeline')
        screen = parent.screen() if parent is not None else QGuiApplication.primaryScreen()
        available = screen.availableGeometry() if screen else None
        self.setMinimumSize(530, 380)
        if available:
            w = min(1370, max(530, available.width() - 32))
            h = min(820, max(380, available.height() - 60))
            self.resize(w, h)
            self.move(available.x() + (available.width() - w)//2,
                      available.y() + (available.height() - h)//2)
        else:
            self.resize(1100, 720)
        self.last_result = None
        self.results_dirty = False
        self.input_path = None
        self.worker_thread = None
        self._build(text)

    @staticmethod
    def _label(message, kind=None):
        widget = QLabel(message)
        if kind:
            widget.setObjectName(kind)
        widget.setWordWrap(True)
        return widget

    @staticmethod
    def _combo(items, tip=''):
        control = QComboBox()
        for label, value in items:
            control.addItem(label, value)
        control.setToolTip(tip)
        return control

    @staticmethod
    def _select(widget):
        return widget.currentData()

    def _build(self, initial_text):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        self.page_scroll = QScrollArea(self)
        self.page_scroll.setWidgetResizable(True)
        self.page_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.page_scroll.setObjectName('pageScroll')
        outer.addWidget(self.page_scroll)
        self.page = QWidget()
        self.page.setObjectName('page')
        self.page_scroll.setWidget(self.page)
        root = QVBoxLayout(self.page)
        root.setContentsMargins(16, 12, 16, 12)
        root.setSpacing(10)

        hero = QFrame(); hero.setObjectName('hero')
        hero_row = QHBoxLayout(hero); hero_row.setContentsMargins(19, 13, 19, 13)
        copy = QVBoxLayout(); copy.setSpacing(4)
        copy.addWidget(self._label('RESEARCH WORKSPACE  /  SESSION 02', 'eyebrow'))
        copy.addWidget(self._label('Six-stage text pipeline', 'title'))
        copy.addWidget(self._label('Reproducible preprocessing  ·  Persian + English  ·  Fully offline', 'subtitle'))
        hero_row.addLayout(copy, 1)
        self.run_button = QPushButton('▶  Run all 6 stages')
        self.run_button.setObjectName('primary')
        self.run_button.setToolTip('Execute all six stages in order without modifying the input.')
        self.run_button.clicked.connect(self.run_pipeline)
        hero_row.addWidget(self.run_button, alignment=Qt.AlignmentFlag.AlignBottom)
        root.addWidget(hero)

        action = QGridLayout()
        action.setHorizontalSpacing(8)
        action.setVerticalSpacing(6)
        action.addWidget(self._label('Test case', 'hint'), 0, 0)
        self.demo_selector = self._combo([(case['label'], key) for key, case in DEMO_CASES.items()],
                                          'Choose a documented Persian test or the English benchmark.')
        self.demo_selector.setMinimumWidth(140)
        action.addWidget(self.demo_selector, 0, 1, 1, 3)
        for i, (label, callback, name) in enumerate((
            ('Load case', self.load_demo, 'secondary'),
            ('Open TXT', self.open_text, ''),
            ('Export JSON', self.export_json, ''),
            ('Quick guide  ?', self.show_guide, ''),
        )):
            button = QPushButton(label)
            if name: button.setObjectName(name)
            button.clicked.connect(callback)
            action.addWidget(button, 1, i)
        root.addLayout(action)
        self.demo_hint = self._label('Select a case and click Load case. The description will appear here.', 'hint')
        root.addWidget(self.demo_hint)
        self.demo_selector.currentIndexChanged.connect(self._show_demo_hint)
        self._show_demo_hint()

        settings = QFrame(); settings.setObjectName('card')
        settings_layout = QVBoxLayout(settings); settings_layout.setContentsMargins(13, 11, 13, 12)
        settings_layout.setSpacing(9)
        settings_layout.addWidget(self._label('EXPERIMENT SETTINGS', 'eyebrow'))
        settings_grid = QGridLayout(); settings_grid.setHorizontalSpacing(11); settings_grid.setVerticalSpacing(6)
        self.language = self._combo([('Persian  /  fa', 'fa'), ('English  /  en', 'en')],
                                    'Select the source language; morphology and tokenizer adapt to it.')
        self.cleaning = self._combo([(v.title(), v) for v in ('general', 'sentiment', 'topic', 'ner', 'transformer', 'spam')],
                                    'General removes web noise; Sentiment keeps emojis; NER retains entities.')
        self.tokenizer = self._combo([('Automatic', 'auto'), ('Regex (no models)', 'regex'),
                                      ('Hazm (Persian)', 'hazm'), ('NLTK (English)', 'nltk')],
                                     'Automatic = Hazm for Persian, NLTK for English. Requires local packages.')
        self.spacing = self._combo([('Hazm • Persian', 'hazm'), ('Conservative • safe', 'conservative'),
                                    ('Off', 'none')],
                                   'Hazm supports richer Persian spacing; conservative only repairs well-defined patterns.')
        self.morph = self._combo([('Stem', 'stem'), ('Lemma', 'lemma'), ('None', 'none')],
                                 'Stemming returns word stems; lemmatization tries for canonical forms. Never both.')
        self.digits = self._combo([('ASCII  123', 'ascii'), ('Persian  ۱۲۳', 'persian'), ('Keep source', 'keep')],
                                  'Normalize Persian and Arabic digits consistently.')
        pairs = [
            ('Language', self.language), ('Cleaning profile', self.cleaning),
            ('Tokenizer', self.tokenizer), ('Persian spacing', self.spacing),
            ('Stage 6 • morphology', self.morph), ('Digit format', self.digits),
        ]
        self.setting_pairs = pairs
        self.settings_grid = settings_grid
        self.settings_labels = [self._label(label, 'hint') for label, _ in pairs]
        self._settings_columns = 0
        self._reflow_settings(3)
        settings_layout.addLayout(settings_grid)
        flags = QGridLayout()
        flags.setHorizontalSpacing(14)
        flags.setVerticalSpacing(6)
        self.stopwords = QCheckBox('Filter stopwords')
        self.stopwords.setChecked(True)
        self.stopwords.setToolTip('Optional stage 5. Disable for tasks where function words carry meaning.')
        self.negation = QCheckBox('Keep negation')
        self.negation.setChecked(True)
        self.negation.setToolTip('Protect not / never / نیست and other known negation words from removal.')
        self.diacritics = QCheckBox('Remove Arabic diacritics')
        self.diacritics.setChecked(True)
        self.diacritics.setToolTip('Remove vowel marks such as َ ِ ُ while preserving ZWNJ.')
        self.visible = QCheckBox('Show spaces & ZWNJ')
        self.visible.setToolTip('Display: · = space U+0020, ⟦ZWNJ⟧ = half-space U+200C. Does not alter text.')
        self.visible.toggled.connect(self.show_stage)
        for i, widget in enumerate((self.stopwords, self.negation, self.diacritics, self.visible)):
            flags.addWidget(widget, i // 2, i % 2)
        settings_layout.addLayout(flags)
        stopword_options = QGridLayout()
        stopword_options.setHorizontalSpacing(8)
        stopword_options.addWidget(self._label('Stopword source', 'hint'), 0, 0)
        self.stopword_source = self._combo([('Dictionary', 'dictionary'), ('Custom list', 'custom')],
                'Dictionary uses Hazm for Persian; Custom uses only the comma-separated terms you provide.')
        stopword_options.addWidget(self.stopword_source, 0, 1)
        self.custom_stopwords = QLineEdit()
        self.custom_stopwords.setPlaceholderText('Custom stopwords, e.g. از, به, و')
        self.custom_stopwords.setToolTip('Used when Stopword source = Custom list; separate terms with commas.')
        self.custom_stopwords.setEnabled(False)
        self.stopword_source.currentIndexChanged.connect(
            lambda: self.custom_stopwords.setEnabled(self._select(self.stopword_source) == 'custom'))
        stopword_options.addWidget(self.custom_stopwords, 1, 0, 1, 2)
        self.protected_words = QLineEdit()
        self.protected_words.setPlaceholderText('Protected terms, e.g. NLP, Python')
        self.protected_words.setToolTip('Always keep these words during stopword filtering and stemming.')
        stopword_options.addWidget(self.protected_words, 2, 0, 1, 2)
        settings_layout.addLayout(stopword_options)
        root.addWidget(settings)

        scores = QHBoxLayout(); scores.setSpacing(10)
        self.metrics = {}
        for key, caption in (('sentences', 'SENTENCES'), ('words', 'TOKENS BEFORE FILTER'),
                             ('final', 'FINAL TOKENS'), ('zwnj', 'ZWNJ / HALF-SPACES')):
            card = QFrame(); card.setObjectName('metricCard')
            box = QVBoxLayout(card); box.setContentsMargins(15, 9, 15, 10); box.setSpacing(2)
            value = self._label('—', 'metric')
            box.addWidget(value); box.addWidget(self._label(caption, 'metricCaption'))
            scores.addWidget(card, 1)
            self.metrics[key] = value
        root.addLayout(scores)

        work = QSplitter(Qt.Orientation.Horizontal); work.setChildrenCollapsible(False)
        left = QWidget(); l = QVBoxLayout(left); l.setContentsMargins(0, 0, 8, 0); l.setSpacing(8)
        l.addWidget(self._label('01  INPUT TEXT  ·  UTF-8', 'section'))
        self.editor = QTextEdit(); self.editor.setAcceptRichText(False)
        self.editor.setPlaceholderText('Paste Persian or English text here, or choose Load case…')
        self.editor.setPlainText(initial_text)
        self.editor.setToolTip('Raw source is never rewritten by running the pipeline.')
        self.editor.setMinimumWidth(250)
        l.addWidget(self.editor, 1)
        l.addWidget(self._label('Tip: “می روم”, “می‌روم”, “كتاب ها” and “کتاب‌ها” are useful spacing tests.', 'hint'))
        work.addWidget(left)

        result = QWidget()
        r = QVBoxLayout(result)
        r.setContentsMargins(8, 0, 0, 0)
        r.setSpacing(8)
        r.addWidget(self._label('02  EXPLORE THE SIX STAGES', 'section'))
        self.stage_grid = QGridLayout()
        self.stage_grid.setSpacing(7)
        self.stage_buttons = []
        self._stage_columns = 0
        for index, (label, _short, description) in enumerate(STAGES):
            button = QPushButton('06  Morphology' if index == 5 else label)
            button.setObjectName('stageStep')
            button.setCheckable(True)
            button.setMinimumHeight(39)
            button.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            button.setToolTip(description)
            button.clicked.connect(lambda checked=False, i=index: self.select_stage(i))
            self.stage_buttons.append(button)
        self._reflow_stages(3)
        r.addLayout(self.stage_grid)
        self.stage_title = self._label('Select a stage', 'section')
        self.stage_description = self._label('Run the pipeline to inspect every transformation.', 'hint')
        self.stage_meta = self._label('Awaiting input', 'eyebrow')
        r.addWidget(self.stage_title)
        r.addWidget(self.stage_description)
        r.addWidget(self.stage_meta)
        self.result_tabs = QTabWidget()
        self.output = QTextEdit(); self.output.setReadOnly(True)
        self.output.setPlaceholderText('Results appear here after you run the six stages.')
        self.audit = QTextEdit(); self.audit.setReadOnly(True)
        self.audit.setPlaceholderText('Operations, counts and mappings appear here.')
        self.full_json = QTextEdit(); self.full_json.setReadOnly(True)
        self.full_json.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)
        self.result_tabs.addTab(self.output, 'Stage output')
        self.result_tabs.addTab(self.audit, 'Audit & evidence')
        self.result_tabs.addTab(self.full_json, 'Reproducible JSON')
        self.result_tabs.setMinimumHeight(170)
        r.addWidget(self.result_tabs, 1)
        work.addWidget(result)
        self.work_splitter = work
        work.setStretchFactor(0, 4)
        work.setStretchFactor(1, 6)
        work.setSizes([440, 780])
        work.setMinimumHeight(390)
        root.addWidget(work, 1)
        self.status = self._label('Ready  ·  Paste text, choose your settings, then run all six stages.', 'status')
        root.addWidget(self.status)

        self.language.currentIndexChanged.connect(self._language_changed)
        self.editor.textChanged.connect(self._mark_dirty)
        for control in (self.language, self.cleaning, self.tokenizer, self.spacing, self.morph, self.digits):
            control.currentIndexChanged.connect(self._mark_dirty)
        for control in (self.stopwords, self.negation, self.diacritics):
            control.toggled.connect(self._mark_dirty)
        self.stopword_source.currentIndexChanged.connect(self._mark_dirty)
        self.custom_stopwords.textChanged.connect(self._mark_dirty)
        self.protected_words.textChanged.connect(self._mark_dirty)
        self.select_stage(0)
        self._language_changed()
        self._reflow_stages(3 if self.width() >= 1120 else 2)
        self._reflow_settings(3 if self.width() >= 880 else 2)

    def select_stage(self, index):
        self.current_stage = index
        for i, button in enumerate(self.stage_buttons):
            button.setChecked(i == index)
        self.show_stage()

    def _reflow_settings(self, columns):
        if columns == self._settings_columns:
            return
        self._settings_columns = columns
        for label, (_, combo) in zip(self.settings_labels, self.setting_pairs):
            self.settings_grid.removeWidget(label)
            self.settings_grid.removeWidget(combo)
        for i, (label, combo) in enumerate(zip(self.settings_labels, (v for _, v in self.setting_pairs))):
            row, col = divmod(i, columns)
            self.settings_grid.addWidget(label, 2 * row, col)
            self.settings_grid.addWidget(combo, 2 * row + 1, col)

    def _reflow_stages(self, columns):
        if columns == self._stage_columns:
            return
        self._stage_columns = columns
        for button in self.stage_buttons:
            self.stage_grid.removeWidget(button)
        for i, button in enumerate(self.stage_buttons):
            row, col = divmod(i, columns)
            self.stage_grid.addWidget(button, row, col)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, 'stage_buttons'):
            self._reflow_stages(3 if self.width() >= 1120 else 2)
        if hasattr(self, 'setting_pairs'):
            self._reflow_settings(3 if self.width() >= 880 else 2)
        if hasattr(self, 'work_splitter'):
            self.work_splitter.setOrientation(Qt.Orientation.Vertical if self.width() < 800
                                              else Qt.Orientation.Horizontal)

    def _mark_dirty(self, *args):
        if self.last_result is not None:
            self.results_dirty = True
            self.status.setText('●  Text or settings changed. Run again before exporting a report.')

    def _language_changed(self, *args):
        fa = self._select(self.language) == 'fa'
        self.spacing.setCurrentIndex(self.spacing.findData('hazm' if fa else 'none'))
        # Avoid a cross-language tokenizer mismatch when switching language.
        if self._select(self.tokenizer) in ('hazm', 'nltk'):
            self.tokenizer.setCurrentIndex(0)
        if self.last_result and self.last_result.get('language') != self._select(self.language):
            self.status.setText('Language was changed. Run again to update the results.')

    def _settings(self):
        return {
            'language': self._select(self.language),
            'cleaning_preset': self._select(self.cleaning),
            'tokenizer': self._select(self.tokenizer),
            'morph_method': self._select(self.morph),
            'remove_stopwords': self.stopwords.isChecked(),
            'preserve_negation': self.negation.isChecked(),
            'stopword_mode': self._select(self.stopword_source),
            'custom_stopwords': self._split_words(self.custom_stopwords.text()),
            'protected_words': self._split_words(self.protected_words.text()),
            'normalization': {'spacing': self._select(self.spacing),
                              'digit_style': self._select(self.digits),
                              'remove_marks': self.diacritics.isChecked()},
        }

    @staticmethod
    def _split_words(text):
        return [w.strip() for w in re.split(r'[,،;؛\n]+', text) if w.strip()]

    def run_pipeline(self):
        if self.worker_thread is not None and self.worker_thread.isRunning():
            return
        text = self.editor.toPlainText()
        if not text.strip():
            QMessageBox.information(self, 'No input', 'Paste text or select “Load case” first.')
            self.editor.setFocus()
            return
        self.run_button.setEnabled(False)
        self.status.setText('Running locally  ·  Preserving the original input…')
        self.worker_thread = QThread(self)
        self.worker = PipelineWorker(text, self._settings())
        self.worker.moveToThread(self.worker_thread)
        self.worker_thread.started.connect(self.worker.run)
        self.worker.complete.connect(self._on_complete)
        self.worker.failed.connect(self._on_failure)
        self.worker.finished.connect(self.worker_thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.worker_thread.finished.connect(self._finished)
        self.worker_thread.start()

    def _finished(self):
        self.run_button.setEnabled(True)

    @Slot(object)
    def _on_complete(self, result):
        self.last_result = result
        self.results_dirty = False
        s = result['statistics']
        for key, value in {
            'sentences': s['sentences'], 'words': s['words_before_stopwords'],
            'final': s['final_tokens'],
            'zwnj': result['stages'][2]['output'].count('\u200c'),
        }.items():
            self.metrics[key].setText(str(value))
        self.full_json.setPlainText(json.dumps(result, ensure_ascii=False, indent=2))
        self.show_stage()
        self.status.setText('✓  Completed  ·  6 / 6 snapshots ready  ·  Raw source unchanged  ·  Export available')

    @Slot(str)
    def _on_failure(self, message):
        self.status.setText('Processing failed. Check the requirement hints below.')
        extra = ('\n\nFor Persian automatic tokenization and morphology: '
                 'install Hazm with “python setup_env.py”. '
                 'To inspect normalization without Hazm, select Regex tokenizer, '
                 'Conservative spacing and Morphology: None.')
        QMessageBox.warning(self, 'Pipeline could not finish', message + extra)

    def show_stage(self, *args):
        index = self.current_stage
        self.stage_title.setText(STAGES[index][0])
        self.stage_description.setText(STAGES[index][2])
        if self.last_result is None:
            self.stage_meta.setText(STAGES[index][1])
            self.output.clear(); self.audit.clear()
            return
        stage = self.last_result['stages'][index]
        raw_output = stage['output']
        self.output.setPlainText(visible_spaces(raw_output) if self.visible.isChecked() else raw_output)
        source = raw_output
        self.output.setLayoutDirection(Qt.LayoutDirection.RightToLeft if text_direction(source) == 'rtl'
                                       else Qt.LayoutDirection.LeftToRight)
        self.audit.setPlainText(stage_audit(stage))
        self.audit.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
        meta = f"Stage {index + 1} of 6   ·   {len(raw_output):,} characters"
        if 'token_count' in stage:
            meta += f"   ·   {stage['token_count']} tokens"
        if index == 2:
            meta += '   ·   idempotent' if stage.get('idempotent') else '   ·   second pass differs'
        self.stage_meta.setText(meta)

    def _show_demo_hint(self, *args):
        key = self._select(self.demo_selector)
        if key in DEMO_CASES:
            self.demo_hint.setText('CASE STUDY  /  ' + DEMO_CASES[key]['description'])

    def load_demo(self):
        case = DEMO_CASES[self._select(self.demo_selector)]
        file = Path(__file__).resolve().parents[1] / 'examples' / 'academic_cases' / case['file']
        try:
            source = file.read_text(encoding='utf-8-sig')
        except (OSError, UnicodeError) as exc:
            QMessageBox.warning(self, 'Case unavailable', f'Unable to load {file.name}: {exc}')
            return
        self.language.setCurrentIndex(self.language.findData(case['language']))
        self.cleaning.setCurrentIndex(self.cleaning.findData(case['cleaning']))
        self.editor.setPlainText(source)
        self.input_path = None
        self.status.setText(f'Loaded {case["label"]}. Run all six stages to inspect the results.')

    def open_text(self):
        path, _ = QFileDialog.getOpenFileName(self, 'Open UTF-8 text', '', 'Text (*.txt);;All files (*)')
        if not path: return
        try:
            self.editor.setPlainText(Path(path).read_text(encoding='utf-8-sig'))
            self.input_path = Path(path).resolve()
            self.status.setText(f'Loaded: {Path(path).name}')
        except (OSError, UnicodeError) as exc:
            QMessageBox.warning(self, 'Cannot read text', str(exc))

    def export_json(self):
        if self.last_result is None or self.results_dirty:
            QMessageBox.information(self, 'Run required',
                                    'Run the pipeline with the current text and settings before exporting.')
            return
        filename, _ = QFileDialog.getSaveFileName(self, 'Export the six stages', 'six-stage-report.json', 'JSON (*.json)')
        if not filename: return
        destination = Path(filename)
        if self.input_path and destination.resolve() == self.input_path:
            QMessageBox.warning(self, 'Protected source', 'Please choose a different filename from the input.')
            return
        try:
            destination.write_text(json.dumps(self.last_result, ensure_ascii=False, indent=2), encoding='utf-8')
            self.status.setText(f'✓  Saved complete audit: {destination.name}')
        except OSError as exc:
            QMessageBox.warning(self, 'Export failed', str(exc))

    def show_guide(self):
        dialog = QDialog(self)
        dialog.setWindowTitle('LEXIS · Professor-friendly quick guide')
        available = (self.screen() or QGuiApplication.primaryScreen()).availableGeometry()
        dialog.resize(min(830, max(500, available.width() - 55)),
                      min(630, max(360, available.height() - 75)))
        layout = QVBoxLayout(dialog)
        title = self._label('HOW TO READ THE SIX-STAGE PIPELINE', 'title')
        layout.addWidget(title)
        view = QTextBrowser()
        sections = []
        for label, short, description in STAGES:
            sections.append(f'<h3>{escape(label)} — {escape(short)}</h3><p>{escape(description)}</p>')
        view.setHtml('''<html><body style="font-family:Segoe UI,Tahoma,sans-serif;"
                ><h3>3 actions to reproduce the experiment</h3>
                <p>1. Paste text (or use <b>Load case</b>). &nbsp;
                   2. Set language and processing profile. &nbsp;
                   3. Click <b>Run all 6 stages</b> and inspect each snapshot.</p>
                <p>Choose a named <b>Test case</b> to explore Persian Unicode, sentiment,
                   morphology, text frequency, noisy PDF extraction or mixed-language input.
                   The six stage buttons adapt to the window width; scroll down to see
                   any controls hidden by a small screen.</p>
                <h3>Every stage, in simple English</h3>''' + ''.join(sections) + '''
                <h3>Persian spaces: a crucial distinction</h3>
                <p><b>U+0020 SPACE</b> separates words. <b>U+200C ZWNJ</b> (half-space)
                   keeps Persian parts visually separate within a token, e.g. <b>می‌روم</b>
                   and <b>کتاب‌ها</b>. Enable <b>Show spaces &amp; ZWNJ</b> to inspect
                   the exact Unicode characters in the output. This is display-only.</p>
                <h3>Scientific caveats</h3>
                <p>Cleaning is task-dependent. Do not remove negation in sentiment analysis.
                   A conservative space fixer avoids many false edits but cannot resolve every
                   ambiguous Persian spelling. Hazm uses a specialized Persian normalizer.
                   Stems are not always dictionary words; lemmatization is language-dependent.</p>
                <h3>Reproducibility</h3>
                <p>All six intermediate outputs, transformation settings, counts and
                   morphological mappings are saved in the JSON export. No cloud API is used.</p>
                </body></html>''')
        layout.addWidget(view)
        button = QPushButton('Close')
        button.clicked.connect(dialog.accept)
        layout.addWidget(button)
        dialog.exec()

    def closeEvent(self, event):
        if self.worker_thread and self.worker_thread.isRunning():
            QMessageBox.information(self, 'Pipeline active',
                'The current local analysis must finish before closing the window.')
            event.ignore()
        else:
            event.accept()
