"""Optional Qt offscreen regression checks for the adaptive six-stage screen."""
import os
import unittest

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

try:
    from PySide6.QtWidgets import QApplication, QScrollArea
    from PySide6.QtCore import Qt
    from nlp_analyzer.six_stage_gui import SixStageStudio
    AVAILABLE = True
except ImportError:
    AVAILABLE = False


@unittest.skipUnless(AVAILABLE, 'Install PySide6 to execute GUI integration checks')
class ResponsiveStudioTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.dialog = SixStageStudio()
        self.dialog.show()
        self.app.processEvents()

    def tearDown(self):
        self.dialog.close()
        self.dialog.deleteLater()
        self.app.processEvents()

    def test_six_stage_grid_responds_to_window_width(self):
        self.assertEqual(len(self.dialog.stage_buttons), 6)
        self.assertIsInstance(self.dialog.page_scroll, QScrollArea)
        self.assertEqual(self.dialog.page_scroll.horizontalScrollBarPolicy(),
                         Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.dialog.resize(740, 530)
        self.app.processEvents()
        self.assertEqual(self.dialog._stage_columns, 2)
        self.assertEqual(self.dialog._settings_columns, 2)
        self.dialog.resize(1220, 760)
        self.app.processEvents()
        self.assertEqual(self.dialog._stage_columns, 3)
        self.assertEqual(self.dialog._settings_columns, 3)

    def test_each_stage_selection_and_english_morphology(self):
        for i, button in enumerate(self.dialog.stage_buttons):
            self.dialog.select_stage(i)
            self.assertTrue(button.isChecked())
            self.assertEqual(self.dialog.current_stage, i)
        self.assertIn('Stemming / Lemmatization', self.dialog.stage_title.text())
        self.assertIn('Morphology', self.dialog.stage_buttons[5].text())

    def test_sample_is_loaded_without_mutating_source(self):
        self.dialog.demo_selector.setCurrentIndex(1)  # Persian spacing case
        self.dialog.load_demo()
        original = self.dialog.editor.toPlainText()
        self.assertIn('تنها', original)
        self.assertEqual(self.dialog.language.currentData(), 'fa')
        self.dialog.select_stage(2)
        self.assertEqual(self.dialog.editor.toPlainText(), original)


if __name__ == '__main__':
    unittest.main()
