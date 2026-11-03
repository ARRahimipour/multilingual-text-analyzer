"""Actual Qt worker completion, report display and paragraph direction checks."""
import os
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
import time
import unittest
try:
    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import QApplication
    from nlp_analyzer.lab_gui import CourseLab
    QT=True
except ImportError: QT=False

@unittest.skipUnless(QT,'Install Qt to run desktop integration tests')
class LabGuiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.app=QApplication.instance() or QApplication([])
    def test_worker_and_mixed_paragraphs(self):
        w=CourseLab('می روم مدرسه.\nI love NLP!');w.show();self.app.processEvents()
        first=w.input.document().begin()
        self.assertEqual(first.blockFormat().layoutDirection(),Qt.RightToLeft)
        self.assertEqual(first.next().blockFormat().layoutDirection(),Qt.LeftToRight)
        w.start();deadline=time.monotonic()+20
        while w.thread.isRunning() and time.monotonic()<deadline:self.app.processEvents();time.sleep(.01)
        self.app.processEvents()
        self.assertFalse(w.thread.isRunning())
        self.assertIn('می‌روم',w.last_result['text'])
        self.assertTrue(w.run_button.isEnabled())
        w.show_result({'vocabulary':['cat'],'bow':[[2]],'tfidf':[[1.0]]})
        self.assertIn('tfidf',w.matrices.toPlainText())
        w.close();w.deleteLater();self.app.processEvents()
