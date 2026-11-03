"""NLP Sessions 1–2 text analysis and optional preprocessing toolkit."""
from .core import AnalysisOptions, AnalysisResult, analyze
from .preprocessing import PreprocessOptions, CleaningResult, clean_text, preset

__all__ = ['AnalysisOptions', 'AnalysisResult', 'analyze',
           'PreprocessOptions', 'CleaningResult', 'clean_text', 'preset']
__version__ = '3.0.0'
