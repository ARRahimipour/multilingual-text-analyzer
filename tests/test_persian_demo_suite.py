"""Regression tests for curated Persian academic text cases (no GUI required)."""
import unittest
from pathlib import Path

from nlp_analyzer.demo_library import DEMO_CASES
from nlp_analyzer.normalization import NormalizationOptions, normalize
from nlp_analyzer.six_stage_pipeline import NAMES, run_six_stage_pipeline

ROOT = Path(__file__).resolve().parents[1]


class AcademicCasesTests(unittest.TestCase):
    def test_nine_curated_inputs_have_metadata_and_real_text(self):
        self.assertEqual(len(DEMO_CASES), 9)
        self.assertEqual(sum(v['language'] == 'fa' for v in DEMO_CASES.values()), 8)
        for key, case in DEMO_CASES.items():
            with self.subTest(case=key):
                self.assertEqual(case['language'] in ('fa', 'en'), True)
                self.assertGreater(len(case['description']), 30)
                self.assertTrue(case['label'][:2].isdigit())
                path = ROOT / 'examples' / 'academic_cases' / case['file']
                self.assertTrue(path.is_file())
                self.assertGreater(len(path.read_text(encoding='utf-8')), 250)

    def test_each_case_passes_six_stage_reproducibility_smoke(self):
        for key, case in DEMO_CASES.items():
            with self.subTest(case=key):
                text = (ROOT / 'examples' / 'academic_cases' / case['file']).read_text(encoding='utf-8')
                result = run_six_stage_pipeline(
                    text, language=case['language'], cleaning_preset=case['cleaning'],
                    tokenizer='regex', normalization={'spacing': 'conservative' if case['language'] == 'fa' else 'none'},
                    morph_method='none', remove_stopwords=False)
                self.assertEqual(len(result['stages']), 6)
                self.assertEqual(result['stages'][0]['output'], text)
                self.assertEqual(result['stages'][5]['tokens'], result['stages'][4]['tokens'])
                self.assertEqual(result['stages'][5]['english'], 'Stemming / Lemmatization')
                self.assertTrue(result['stages'][2]['idempotent'])

    def test_spacing_research_case_covers_regression_invariants(self):
        case = DEMO_CASES['spacing']
        text = (ROOT / 'examples' / 'academic_cases' / case['file']).read_text(encoding='utf-8')
        out = normalize(text, NormalizationOptions(spacing='conservative', digit_style='ascii'))['text']
        self.assertIn('می‌روم', out)
        self.assertIn('کتاب‌ها', out)
        self.assertIn('تنها', out)
        self.assertNotIn('تن‌ها', out)
        self.assertIn('123', out)
        self.assertEqual(out, normalize(out, NormalizationOptions(spacing='conservative', digit_style='ascii'))['text'])

    def test_sentiment_profile_retains_emoji(self):
        case = DEMO_CASES['sentiment']
        text = (ROOT / 'examples' / 'academic_cases' / case['file']).read_text(encoding='utf-8')
        out = run_six_stage_pipeline(text, language='fa', cleaning_preset='sentiment',
                                     tokenizer='regex', normalization={'spacing': 'conservative'},
                                     morph_method='none', remove_stopwords=False)
        self.assertIn('😍', out['stages'][1]['output'])
        self.assertIn('نیست', out['stages'][2]['output'])

    def test_stage_metadata_english_only(self):
        for _, display_title, english in NAMES:
            self.assertTrue(display_title.isascii(), display_title)
            self.assertTrue(english.isascii(), english)


if __name__ == '__main__':
    unittest.main()
