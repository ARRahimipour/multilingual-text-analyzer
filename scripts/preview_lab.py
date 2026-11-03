"""Render the actual Qt lab window for local visual verification."""
import os
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from PySide6.QtWidgets import QApplication
from nlp_analyzer.lab_gui import CourseLab
from nlp_analyzer.lab import run_lab
app=QApplication([])
w=CourseLab();w.load_sample();w.show_result(run_lab('normalize',w.input.toPlainText()));w.show();app.processEvents()
w.grab().save(str(Path(__file__).resolve().parents[1]/'docs/course-lab-preview.png'))
w.close()
