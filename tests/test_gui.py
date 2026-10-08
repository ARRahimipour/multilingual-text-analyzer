"""Optional offscreen Qt integration checks; install requirements-gui.txt first."""
import os
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
import unittest
from pathlib import Path
try:
    from PySide6.QtCore import Qt
    from PySide6.QtGui import QTextCursor
    from PySide6.QtWidgets import QApplication
    from nlp_analyzer.gui import AnalyzerWindow
    QT_AVAILABLE = True
except ImportError:
    QT_AVAILABLE = False


@unittest.skipUnless(QT_AVAILABLE, 'Install requirements-gui.txt for Qt integration tests')
class DesktopTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.window = AnalyzerWindow()

    def tearDown(self):
        self.window.close()
        self.window.deleteLater()
        self.app.processEvents()

    def test_persian_and_english_paragraph_directions(self):
        text = 'این متن فارسی درباره NLP است.\nThis is English.'
        self.window.set_text(text)
        first = self.window.editor.document().begin()
        self.assertEqual(first.blockFormat().layoutDirection(), Qt.LayoutDirection.RightToLeft)
        self.assertEqual(first.next().blockFormat().layoutDirection(), Qt.LayoutDirection.LeftToRight)
        self.assertEqual(self.window.editor.toPlainText(), text)

    def test_refresh_preserves_selection_and_source(self):
        text = 'سلام دنیا ۱۴۰۵! Hello 2026.'
        self.window.editor.setPlainText(text)
        cursor = self.window.editor.textCursor()
        cursor.setPosition(0); cursor.setPosition(4, QTextCursor.MoveMode.KeepAnchor)
        self.window.editor.setTextCursor(cursor)
        self.window.refresh()
        cursor = self.window.editor.textCursor()
        self.assertEqual(cursor.selectedText(), 'سلام')
        self.assertEqual(self.window.editor.toPlainText(), text)
        self.window.refresh()
        self.assertEqual(self.window.editor.textCursor().selectedText(), 'سلام')

    def test_uploaded_text_counts_in_actual_gui(self):
        text = (Path(__file__).resolve().parents[1] / 'examples/persian_regression.txt').read_text(encoding='utf-8')
        self.window.persian.setChecked(True); self.window.numbers.setChecked(True)
        self.window.set_text(text)
        self.assertEqual([label.text() for label in self.window.metric_labels], ['19', '300', '183', '132'])
        self.assertEqual(self.window.table.item(0, 1).text(), 'و')

    def test_clear_and_sample(self):
        self.window.set_text('سلام دنیا!'); self.window.clear()
        self.assertEqual(self.window.result.word_count, 0)
        self.window.load_sample()
        self.assertEqual(self.window.result.word_count, 300)
        self.assertEqual(self.window.result.sentence_count, 26)

    def test_wrapped_rtl_lines_stay_inside_editor(self):
        self.window.resize(900, 800); self.window.show()
        self.window.set_text('پردازش زبان طبیعی برای تحلیل متن فارسی استفاده می‌شود. ' * 20)
        self.app.processEvents()
        doc = self.window.editor.document()
        block = doc.begin(); layout = block.layout()
        self.assertGreater(layout.lineCount(), 1)
        rect = doc.documentLayout().blockBoundingRect(block)
        for index in range(layout.lineCount()):
            line = layout.lineAt(index)
            bounds = line.naturalTextRect()
            self.assertGreaterEqual(bounds.left() + rect.left(), 0)
            self.assertLessEqual(bounds.right() + rect.left(), self.window.editor.viewport().width())

    def test_short_lines_reach_the_correct_physical_edge(self):
        self.window.show()
        for text, rtl in [('سلام دنیا.', True), ('مرحبا بالعالم.', True), ('Hello world.', False)]:
            with self.subTest(text=text):
                self.window.set_text(text)
                self.app.processEvents()
                line = self.window.editor.document().begin().layout().lineAt(0)
                actual = line.naturalTextRect()
                available = line.rect()
                if rtl:
                    self.assertAlmostEqual(actual.right(), available.right(), delta=1.0)
                    self.assertGreater(actual.left(), available.left() + 50)
                else:
                    self.assertAlmostEqual(actual.left(), available.left(), delta=1.0)

    def test_wrapped_paragraph_last_line_is_right_aligned_after_resize(self):
        self.window.show()
        text = 'پردازش زبان طبیعی برای تحلیل متن فارسی استفاده می‌شود. ' * 5
        for width in (900, 1180):
            self.window.resize(width, 800)
            self.window.set_text(text)
            self.app.processEvents()
            layout = self.window.editor.document().begin().layout()
            self.assertGreater(layout.lineCount(), 1)
            last = layout.lineAt(layout.lineCount() - 1)
            self.assertAlmostEqual(last.naturalTextRect().right(), last.rect().right(), delta=1.0)

    def test_zoom_bounds(self):
        self.window.resize_text(100)
        self.assertEqual(self.window.font_size, 24)
        self.window.resize_text(-100)
        self.assertEqual(self.window.font_size, 11)
