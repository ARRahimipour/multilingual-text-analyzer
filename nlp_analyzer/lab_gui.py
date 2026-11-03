"""Interactive course lab with background execution and inspectable outputs."""
import json
from pathlib import Path
from PySide6.QtCore import Qt, QObject, QThread, Signal, Slot
from PySide6.QtGui import QTextCursor
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel,
    QPushButton, QComboBox, QSpinBox, QCheckBox, QTextEdit, QTabWidget, QWidget,
    QTextBrowser, QSplitter, QTableWidget, QTableWidgetItem, QHeaderView, QFileDialog, QMessageBox, QGroupBox)
from .lab import OPERATIONS, run_lab, save_lab_report
from .direction import text_direction
from .tokenization import SUBWORD_METHODS


class Worker(QObject):
    completed = Signal(object)
    failed = Signal(str)
    finished = Signal()
    def __init__(self, operation, text, corpus, settings):
        super().__init__(); self.arguments = operation, text, corpus, settings
    @Slot()
    def run(self):
        try:
            operation, text, corpus, settings = self.arguments
            self.completed.emit(run_lab(operation, text, corpus, **settings))
        except Exception as exc:
            self.failed.emit(f'{type(exc).__name__}: {exc}')
        finally: self.finished.emit()


class CourseLab(QDialog):
    def __init__(self, text='', parent=None):
        super().__init__(parent)
        self.setWindowTitle('Course Lab v3.0 · Normalization and Tokenization')
        self.resize(1240, 860)
        self.last_result = None; self.thread = None; self.model_path = None; self.input_paths = set()
        self.evaluation_records = None
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel('FOUR-HANDOUT LAB · Run explicit experiments on your own text'))
        bar = QHBoxLayout(); layout.addLayout(bar)
        self.operation = QComboBox(); self.operation.addItems(OPERATIONS)
        bar.addWidget(QLabel('Activity')); bar.addWidget(self.operation)
        self.run_button = QPushButton('Run activity'); self.run_button.clicked.connect(self.start); bar.addWidget(self.run_button)
        for name, callback in [('Guide', self.show_guide), ('Reset model', self.reset_model), ('Load sample', self.load_sample), ('Open corpus', self.load_corpus),
                               ('Load model', self.load_model), ('Save model', self.save_model),
                               ('Load holdout', self.load_holdout), ('Export JSON', self.export)]:
            button = QPushButton(name); button.clicked.connect(callback); bar.addWidget(button)
        self.note = QLabel('Corpus: one document per line. Classify: one JSON object with text and label per line.'); self.note.setWordWrap(True); layout.addWidget(self.note)
        controls = QGroupBox('Experiment settings'); grid = QGridLayout(controls); layout.addWidget(controls)
        self.algorithm = QComboBox(); self.algorithm.addItems(SUBWORD_METHODS)
        self.vocab = QSpinBox(); self.vocab.setRange(8, 50000); self.vocab.setValue(300)
        self.maximum = QSpinBox(); self.maximum.setRange(1, 10000); self.maximum.setValue(128)
        self.overlap = QSpinBox(); self.overlap.setRange(0, 9999); self.overlap.setValue(16)
        self.form = QComboBox(); self.form.addItems(['NFKC', 'NFC', 'NFD', 'NFKD'])
        self.spacing = QComboBox(); self.spacing.addItems(['conservative', 'hazm', 'none'])
        self.digits = QComboBox(); self.digits.addItems(['keep', 'ascii', 'persian'])
        self.language = QComboBox(); self.language.addItems(['fa', 'en'])
        self.morph_method = QComboBox(); self.morph_method.addItems(['stem', 'lemma'])
        self.pos = QComboBox(); self.pos.addItems(['n', 'v', 'a', 'r', 's'])
        self.ngram = QSpinBox(); self.ngram.setRange(1, 5)
        self.side = QComboBox(); self.side.addItems(['right', 'left'])
        for i, (label, widget) in enumerate([('Algorithm', self.algorithm), ('Vocabulary', self.vocab),
            ('Max tokens', self.maximum), ('Overlap', self.overlap), ('Unicode form', self.form),
            ('Spacing', self.spacing), ('Digits', self.digits), ('Language', self.language),
            ('Morphology', self.morph_method), ('English POS', self.pos), ('N-gram', self.ngram), ('Pad/truncate side', self.side)]):
            row, col = divmod(i, 6); grid.addWidget(QLabel(label), row * 2, col); grid.addWidget(widget, row * 2 + 1, col)
        self.flags = {}
        for i, (key, label, checked) in enumerate([('persian_letters', 'Persian letters', True),
            ('remove_marks', 'Remove diacritics', False), ('arabic_variants', 'Arabic variants', False),
            ('casefold', 'Case folding', False), ('expand_contractions', 'English contractions', False),
            ('lexical_map', 'Small lexical dictionary', False), ('placeholders', 'Entity placeholders', False),
            ('elongation', 'Reduce long letters', False), ('stopwords', 'Remove stopwords', False),
            ('use_subword', 'Subwords for batch/chunks', False), ('truncation', 'Allow truncation', True)]):
            checkbox = QCheckBox(label); checkbox.setChecked(checked); self.flags[key] = checkbox
            grid.addWidget(checkbox, 4 + i // 6, i % 6)
        self.model_label = QLabel('Model: train locally from the corpus (no remote model download)'); layout.addWidget(self.model_label)
        splitter = QSplitter(); layout.addWidget(splitter, 1)
        left = QWidget(); inputs = QVBoxLayout(left); inputs.setContentsMargins(0, 0, 6, 0)
        inputs.addWidget(QLabel('INPUT / QUERY'))
        self.input = QTextEdit(); self.input.setAcceptRichText(False); self.input.setPlainText(text); inputs.addWidget(self.input)
        inputs.addWidget(QLabel('TRAINING CORPUS / DOCUMENT COLLECTION'))
        self.corpus = QTextEdit(); self.corpus.setAcceptRichText(False); inputs.addWidget(self.corpus)
        self.corpus.setPlaceholderText('Paste separate training documents here. Query is not automatically added to training.')
        splitter.addWidget(left)
        self.tabs = QTabWidget(); splitter.addWidget(self.tabs); splitter.setSizes([480, 740])
        self.summary = QTextEdit(); self.summary.setReadOnly(True); self.tabs.addTab(self.summary, 'Readable result')
        self.table = QTableWidget(); self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers); self.tabs.addTab(self.table, 'Details')
        self.matrices = QTextEdit(); self.matrices.setReadOnly(True); self.tabs.addTab(self.matrices, 'Matrices')
        self.json_view = QTextEdit(); self.json_view.setReadOnly(True); self.tabs.addTab(self.json_view, 'Full JSON')
        self.status = QLabel('Ready. Normalization preserves a source copy and records each stage.'); self.status.setWordWrap(True); layout.addWidget(self.status)
        self.operation.currentTextChanged.connect(self.activity_changed)
        for editor in (self.input, self.corpus): editor.textChanged.connect(lambda e=editor: self.align(e))
        self.align(self.input); self.activity_changed()

    def align(self, editor):
        editor.blockSignals(True)
        block = editor.document().begin()
        while block.isValid():
            rtl = text_direction(block.text()) == 'rtl'
            fmt = block.blockFormat(); fmt.setLayoutDirection(Qt.RightToLeft if rtl else Qt.LeftToRight)
            fmt.setAlignment((Qt.AlignRight if rtl else Qt.AlignLeft) | Qt.AlignAbsolute)
            cursor = QTextCursor(block); cursor.setBlockFormat(fmt); block = block.next()
        editor.blockSignals(False)

    def activity_changed(self):
        op = self.operation.currentText()
        descriptions = {
            'normalize': 'Compare every normalization stage and check whether a second pass changes the result.',
            'unicode': 'Inspect code points, UTF-8 bytes, grapheme clusters and all four Unicode forms.',
            'compare': 'Run whitespace, regex, Unicode, character, grapheme, NLTK and Hazm tokenizers.',
            'subword': 'Train BPE / WordPiece / Unigram or SentencePiece locally; encode the separate input query.',
            'oov': 'Fit a word vocabulary on the corpus and show unknown words in the query.',
            'batch': 'Encode corpus documents, then inspect padding, masks and removed-token counts.',
            'chunk': 'Pack complete sentences within the token budget. Long sentences fall back to word boundaries.',
            'morphology': 'Inspect stopword removal and stems or lemmas. English lemmas require local WordNet.',
            'features': 'Compute Bag-of-Words, TF-IDF, cosine similarity, N-grams and Zipf rank statistics.',
            'classify': 'Train TF-IDF + Naive Bayes on labeled JSONL. Holdout is separate; no training-set accuracy.'}
        self.note.setText(descriptions[op])

    def settings(self):
        norm = {key: self.flags[key].isChecked() for key in ('persian_letters', 'remove_marks', 'arabic_variants',
                'casefold', 'expand_contractions', 'lexical_map', 'placeholders')}
        norm.update(unicode_form=self.form.currentText(), spacing=self.spacing.currentText(),
                    digit_style=self.digits.currentText(), elongation='language-aware' if self.flags['elongation'].isChecked() else 'keep')
        settings = dict(normalization=norm, method=self.algorithm.currentText(), vocab_size=self.vocab.value(),
            max_length=self.maximum.value(), overlap=self.overlap.value(), language=self.language.currentText(),
            morph_method=self.morph_method.currentText(), pos=self.pos.currentText(), ngram=self.ngram.value(),
            side=self.side.currentText(), stopwords=self.flags['stopwords'].isChecked(),
            use_subword=self.flags['use_subword'].isChecked(), truncation=self.flags['truncation'].isChecked())
        if self.model_path: settings['model_file'] = str(self.model_path)
        return settings

    def start(self, save_to=None):
        if self.thread and self.thread.isRunning(): return
        op = self.operation.currentText(); settings = self.settings()
        corpus = [row for row in self.corpus.toPlainText().splitlines() if row.strip()]
        if (op in ('oov', 'batch', 'features', 'classify') or (op in ('subword', 'chunk') and not self.model_path and (op == 'subword' or settings['use_subword']))) and not corpus:
            QMessageBox.warning(self, 'Corpus needed', 'Paste or open separate training documents first.'); return
        if save_to: settings['save_model'] = str(save_to)
        if op == 'classify':
            try: settings['training_records'] = [json.loads(row) for row in corpus]
            except ValueError as exc: QMessageBox.warning(self, 'Invalid JSONL', str(exc)); return
            settings['evaluation_records'] = self.evaluation_records
        self.last_result = None; self.run_button.setEnabled(False); self.status.setText('Running locally...')
        self.thread = QThread(self)
        self.worker = Worker(op, self.input.toPlainText(), corpus or None, settings)
        self.worker.moveToThread(self.thread); self.thread.started.connect(self.worker.run)
        self.worker.completed.connect(self.show_result); self.worker.failed.connect(self.show_error)
        self.worker.finished.connect(self.thread.quit); self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(lambda: self.run_button.setEnabled(True))
        self.thread.start()

    @Slot(object)
    def show_result(self, result):
        self.last_result = result
        matrix_lines = []
        for key in ('vocabulary', 'document_frequency', 'idf', 'bow', 'tfidf', 'cosine_similarity', 'input_ids', 'attention_mask'):
            if key in result: matrix_lines.append(key + ':\n' + json.dumps(result[key], ensure_ascii=False, indent=2))
        self.matrices.setPlainText('\n\n'.join(matrix_lines) or 'This activity does not produce a matrix.')
        self.json_view.setPlainText(json.dumps(result, ensure_ascii=False, indent=2))
        lines = []
        for key, value in result.items():
            if isinstance(value, (str, int, float, bool)) or value is None: lines.append(f'{key}:\n{value}')
        if 'tokens' in result: lines.append('Tokens:\n' + ' · '.join(map(str, result['tokens'])))
        if 'input_ids' in result: lines.append('Input IDs:\n' + str(result['input_ids']) + '\nAttention masks:\n' + str(result['attention_mask']))
        if 'unknown_tokens' in result: lines.append('Unknown tokens: ' + ', '.join(result['unknown_tokens']))
        if 'chunks' in result: lines += [f"Chunk {i}: {row['text']} ({row['token_count']} tokens)" for i, row in enumerate(result['chunks'], 1)]
        if 'comparisons' in result: lines += [f"{r['method']}: {r.get('count', 'unavailable')} tokens\n{r.get('tokens', r.get('error'))}" for r in result['comparisons']]
        if 'evaluation' in result: lines.append('Holdout evaluation: ' + str(result['evaluation']))
        self.summary.setPlainText('\n\n'.join(lines)); self.align(self.summary)
        rows = next((result[key] for key in ('stages', 'comparisons', 'rows', 'characters', 'zipf', 'chunks') if key in result), [])
        if not rows and 'tokens' in result:
            rows = [{'index': i, 'token': token, 'id': result.get('ids', [None] * len(result['tokens']))[i]} for i, token in enumerate(result['tokens'])]
        headers = list(rows[0]) if rows else []
        self.table.setColumnCount(len(headers)); self.table.setHorizontalHeaderLabels(headers)
        self.table.setRowCount(min(len(rows), 1000))
        for i, row in enumerate(rows[:1000]):
            for j, key in enumerate(headers): self.table.setItem(i, j, QTableWidgetItem(str(row.get(key, ''))))
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.table.resizeColumnsToContents()
        for column in range(len(headers)): self.table.setColumnWidth(column, min(360, self.table.columnWidth(column)))
        self.status.setText('Complete. Details table shows up to 1,000 rows; Full JSON and export contain all results.')

    @Slot(str)
    def show_error(self, message):
        self.status.setText(message); self.summary.setPlainText(message)
        self.json_view.clear(); self.matrices.clear(); self.table.setRowCount(0)

    def reset_model(self):
        self.model_path = None
        self.model_label.setText('Model: train locally from the corpus')

    def show_guide(self):
        dialog = QDialog(self); dialog.setWindowTitle('Four-handout course guide'); dialog.resize(900, 700)
        layout = QVBoxLayout(dialog); browser = QTextBrowser(); layout.addWidget(browser)
        path = Path(__file__).resolve().parents[1] / 'docs' / 'COURSE_GUIDE.md'
        browser.setMarkdown(path.read_text(encoding='utf-8'))
        dialog.show()

    def load_sample(self):
        path = Path(__file__).resolve().parents[1] / 'examples' / 'lab_corpus.txt'
        if path.is_file(): self.corpus.setPlainText(path.read_text(encoding='utf-8'))
        self.input.setPlainText('سلام! من کتاب ها را می خوانم. I love learning NLP!')
        self.model_path = None; self.model_label.setText('Model: train locally from the corpus')

    def load_corpus(self):
        path, _ = QFileDialog.getOpenFileName(self, 'Open training corpus', '', 'Text/JSONL (*.txt *.jsonl)')
        if path:
            try:
                self.corpus.setPlainText(Path(path).read_text(encoding='utf-8-sig')); self.input_paths.add(Path(path).resolve())
            except (OSError, UnicodeError) as exc: self.show_error(str(exc))

    def load_model(self):
        path, _ = QFileDialog.getOpenFileName(self, 'Open local tokenizer', '', 'Tokenizer (*.json *.model)')
        if path:
            self.model_path = Path(path); self.input_paths.add(self.model_path.resolve())
            self.model_label.setText('Loaded model: ' + str(path))

    def save_model(self):
        self.operation.setCurrentText('subword')
        extension = '.model' if self.algorithm.currentText() == 'sentencepiece' else '.json'
        path, _ = QFileDialog.getSaveFileName(self, 'Save trained tokenizer', 'tokenizer' + extension)
        if path:
            if Path(path).resolve() in self.input_paths: self.show_error('Choose a new destination, not an input file.'); return
            self.start(save_to=path)

    def load_holdout(self):
        path, _ = QFileDialog.getOpenFileName(self, 'Open held-out labeled data', '', 'JSONL (*.jsonl)')
        if path:
            try:
                self.evaluation_records = [json.loads(s) for s in Path(path).read_text(encoding='utf-8').splitlines() if s.strip()]
                self.input_paths.add(Path(path).resolve()); self.status.setText(f'Loaded {len(self.evaluation_records)} holdout records.')
            except (OSError, ValueError) as exc: self.show_error(str(exc))

    def export(self):
        if self.last_result is None: self.show_error('Run an activity successfully before exporting.'); return
        path, _ = QFileDialog.getSaveFileName(self, 'Export full result', 'lab-result.json', 'JSON (*.json)')
        if path:
            if Path(path).resolve() in self.input_paths: self.show_error('Output must not overwrite a loaded source.'); return
            try: save_lab_report(self.last_result, path)
            except OSError as exc: self.show_error(str(exc))

    def closeEvent(self, event):
        if self.thread and self.thread.isRunning():
            self.status.setText('Please wait for the current activity to finish before closing.'); event.ignore()
        else: event.accept()
