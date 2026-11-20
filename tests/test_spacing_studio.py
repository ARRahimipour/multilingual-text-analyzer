"""Headless regression coverage for Persian spaces and English six-stage labels."""
import unittest

from nlp_analyzer.normalization import NormalizationOptions, normalize
from nlp_analyzer.spacing_inspection import spacing_counts, visible_spaces
from nlp_analyzer.six_stage_pipeline import NAMES, run_six_stage_pipeline


OPTIONS = NormalizationOptions(spacing='conservative', digit_style='ascii', remove_marks=True)


class PersianSpacingStudioTests(unittest.TestCase):
    def test_fa_arabic_forms_and_joined_suffixes(self):
        text = 'من ميروم و ميخواهم كتابها و كتابهاي جديد را بخوانم.'
        output = normalize(text, OPTIONS)['text']
        self.assertIn('می‌روم', output)
        self.assertIn('می‌خواهم', output)
        self.assertIn('کتاب‌ها', output)
        self.assertIn('کتاب‌های', output)
        self.assertEqual(output, normalize(output, OPTIONS)['text'])

    def test_spaces_malformed_zwnj_and_digits(self):
        raw = 'می  ‌  روم   و  کتاب ‌ ها!  ۱۲۳'
        clean = normalize(raw, OPTIONS)['text']
        self.assertEqual(clean, 'می‌روم و کتاب‌ها! 123')
        self.assertEqual(clean, normalize(clean, OPTIONS)['text'])

    def test_no_unsafe_joining_of_unrelated_words(self):
        text = 'او تنها روی میز ماند و در خانه بود.'
        result = normalize(text, OPTIONS)['text']
        self.assertEqual(result, text)
        self.assertNotIn('تن‌ها', result)

    def test_zwnj_vs_space_explicitly_visible(self):
        original = 'می‌روم و کتاب ها\u00a0!'
        view = visible_spaces(original)
        self.assertIn('⟦ZWNJ⟧', view)
        self.assertIn('·', view)
        self.assertIn('⟦NBSP⟧', view)
        self.assertEqual(spacing_counts(original)['half_spaces_ZWNJ_U+200C'], 1)
        self.assertEqual(original, 'می‌روم و کتاب ها\u00a0!')

    def test_repeated_punctuation_keeps_internal_boundaries(self):
        result = normalize('سلام!!!خوبی؟! بله؟ نه!!!', OPTIONS)['text']
        self.assertIn('سلام!!! خوبی؟!', result)
        self.assertNotIn('! ! !', result)
        self.assertEqual(result, normalize(result, OPTIONS)['text'])

    def test_stage_six_is_english_and_auditable(self):
        self.assertEqual(NAMES[5][2], 'Stemming / Lemmatization')
        self.assertTrue(all(name[1][0].isascii() for name in NAMES))
        settings = dict(language='fa', tokenizer='regex',
                        normalization={'spacing': 'conservative'},
                        remove_stopwords=False, morph_method='none')
        result = run_six_stage_pipeline('كتابها و كتاب هاي جديد. ميروم!', **settings)
        normalized = result['stages'][2]
        self.assertEqual(len(result['stages']), 6)
        self.assertIn('کتاب‌ها', normalized['output'])
        self.assertIn('می‌روم', normalized['output'])
        self.assertTrue(normalized['idempotent'])
        self.assertGreater(normalized['spacing_after']['half_spaces_ZWNJ_U+200C'], 0)
        self.assertEqual(result['stages'][5]['english'], 'Stemming / Lemmatization')


if __name__ == '__main__':
    unittest.main()
