"""Session 2: cleaning, Unicode, task presets, dataset audits and safety."""
from dataclasses import replace
import csv
import json
from pathlib import Path
import tempfile
import unittest

from nlp_analyzer import AnalysisOptions, analyze
from nlp_analyzer.dataset import clean_dataset
from nlp_analyzer.preprocessing import PreprocessOptions, clean_text, preset, persian_script_ratio
from nlp_analyzer.reports import render_report


class PreprocessingTests(unittest.TestCase):
    def test_persian_unicode_digits_and_half_space(self):
        source = 'كي‌تاب ۱۲٣ \ufeff\u200b\u200eب\u200d👩\u200d👧'
        cleaned = clean_text(source, replace(preset('general'), digit_style='ascii')).text
        self.assertIn('کی‌تاب 123', cleaned)
        self.assertNotIn('\ufeff', cleaned)
        self.assertNotIn('\u200b', cleaned)
        self.assertNotIn('\u200e', cleaned)
        self.assertIn('\u200c', cleaned)
        self.assertIn('\u200d', cleaned)  # Don't destroy emoji joining sequences.

    def test_unicode_compatibility_and_diacritics_optional(self):
        source = 'ﻛِـتاب ① مَرْحَبًا'
        default = clean_text(source).text
        without_marks = clean_text(source, replace(preset('general'), remove_diacritics=True)).text
        self.assertIn('کتاب 1', default.replace('ِ', ''))
        self.assertIn('مرحبا', without_marks)
        self.assertNotIn('ِ', without_marks)

    def test_html_entity_script_style_and_literal_comparison(self):
        source = '<p>سلام&nbsp;<b>دنیا</b></p><script>secret = 42</script><style>hide</style>2 < 3'
        output = clean_text(source).text
        self.assertIn('سلام دنیا', output)
        self.assertIn('2 < 3', output)
        self.assertNotIn('secret', output)
        self.assertNotIn('hide', output)

    def test_links_mentions_hashtags_and_emails(self):
        output = clean_text('Hi @alice #NLP #هوش_مصنوعی visit https://x.ir/a mail a@b.com',
                            preset('general')).text
        self.assertEqual(output, 'Hi NLP هوش_مصنوعی visit mail')

    def test_emoji_keep_remove_label_and_zwj(self):
        source = 'عالی 😍 👩‍👧 🇮🇷'
        self.assertIn('😍', clean_text(source, preset('sentiment')).text)
        self.assertNotIn('😍', clean_text(source, preset('topic')).text)
        labeled = clean_text(source, replace(preset('general'), emoji_mode='label')).text
        self.assertIn(':smiling_face_with_heart-shaped_eyes:', labeled)
        self.assertIn(':woman_girl:', labeled)

    def test_sentence_boundaries_before_punctuation_removed(self):
        result = analyze('سلام! خوبی؟ من خوبم.', AnalysisOptions(preprocessing=preset('topic')))
        self.assertEqual(result.sentence_count, 3)
        self.assertEqual(result.cleaned_text, 'سلام خوبی من خوبم')

    def test_punctuation_normalization_and_repeats(self):
        config = replace(preset('general'), collapse_repeated_punctuation=True)
        self.assertEqual(clean_text('«سلام»!!!! وای…', config).text, '"سلام"! وای...')

    def test_numbers_and_script_presets(self):
        text = 'قیمت ۱۲۰۰تومان #خرید 😍'
        self.assertIn('<NUM>', clean_text(text, preset('sentiment')).text)
        self.assertNotIn('۱۲۰۰', clean_text(text, preset('topic')).text)
        self.assertIn('😍', clean_text(text, preset('transformer')).text)
        self.assertIn('#خرید', clean_text(text, preset('spam')).text)
        self.assertGreater(persian_script_ratio('سلام NLP'), 0.4)
        self.assertEqual(persian_script_ratio('123'), 0.0)

    def test_retweets_elongations_and_url_terminal_punctuation(self):
        source = 'RT @bob سالااام! Visit https://example.org. Bye.'
        output = clean_text(source, preset('general')).text
        self.assertEqual(output, 'سالام! Visit . Bye.')
        result = analyze(source, AnalysisOptions(preprocessing=preset('general')))
        self.assertEqual(result.sentence_count, 3)

    def test_pii_masking_mixed_digit_scripts(self):
        text = 'ایمیل test@example.com تلفن ۰۹۱۲۳۴۵۶۷۸۹ کد ۱۲۳۴۵۶۷۸۹۰'
        cleaned = clean_text(text, replace(preset('general'), mask_pii=True)).text
        self.assertIn('<EMAIL>', cleaned)
        self.assertIn('<PHONE>', cleaned)
        self.assertIn('<NATIONAL_ID>', cleaned)
        self.assertNotIn('test@example.com', cleaned)
        self.assertNotIn('۰۹۱۲۳۴۵۶۷۸۹', cleaned)

    def test_raw_unchanged_statistics_and_report(self):
        raw = '  <p>سلام&nbsp;دنیا</p> https://example.com  '
        outcome = clean_text(raw, preset('general'))
        self.assertTrue(raw.startswith('  <p>'))
        self.assertEqual(outcome.text, 'سلام دنیا')
        self.assertEqual(outcome.statistics['characters_before'], len(raw))
        self.assertTrue(outcome.statistics['changed_stages']['html']['changed'])
        result = analyze(raw, AnalysisOptions(preprocessing=preset('general')))
        self.assertIn('Preprocessing audit', render_report(result, 'html'))
        self.assertIn('Changed stages', render_report(result, 'text'))
        self.assertIn('cleaning_statistics', json.loads(render_report(result, 'json')))

    def test_html_report_escapes_preprocessing_view(self):
        setting = replace(preset('transformer'), remove_html=False)
        report = render_report(analyze('<img src=x onerror=alert(1)>',
                                       AnalysisOptions(preprocessing=setting)), 'html')
        self.assertNotIn('<img src=x', report)
        self.assertIn('&lt;img', report)

    def test_invisible_and_control_modes(self):
        raw = 'a\x01b\u200bc\u200dd\u200ce'
        self.assertIn('\x01', clean_text(raw, replace(preset('general'), invisible_mode='safe')).text)
        cleaned = clean_text(raw, replace(preset('general'), invisible_mode='controls')).text
        self.assertEqual(cleaned, 'abc\u200dd\u200ce')

    def test_invalid_settings(self):
        with self.assertRaises(ValueError):
            preset('bogus')
        with self.assertRaises(ValueError):
            PreprocessOptions(emoji_mode='random')
        with self.assertRaises(TypeError):
            analyze('hi', AnalysisOptions(preprocessing='general'))


class DatasetTests(unittest.TestCase):
    def test_csv_clean_dedup_after_normalization_and_filters(self):
        with tempfile.TemporaryDirectory() as folder:
            inp, out = Path(folder) / 'in.csv', Path(folder) / 'out.csv'
            with inp.open('w', encoding='utf-8', newline='') as stream:
                writer = csv.DictWriter(stream, fieldnames=['id', 'text'])
                writer.writeheader()
                writer.writerows([{'id': 1, 'text': 'كتابها عالی است'},
                                  {'id': 2, 'text': 'کتابها عالی است'},
                                  {'id': 3, 'text': 'ok'},
                                  {'id': 4, 'text': 'English sentence'},
                                  {'id': 5, 'text': ''}])
            summary = clean_dataset(inp, out, preset('general'), min_persian_ratio=0.5)
            with out.open(encoding='utf-8') as stream:
                rows = list(csv.DictReader(stream))
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]['id'], '1')
            self.assertEqual(summary['reasons']['exact_duplicate'], 1)
            self.assertEqual(summary['reasons']['script_ratio'], 1)
            self.assertEqual(summary['reasons']['too_short'], 1)
            self.assertEqual(summary['reasons']['empty'], 1)

    def test_jsonl_near_duplicate_and_source_preserved(self):
        with tempfile.TemporaryDirectory() as folder:
            inp, out = Path(folder) / 'in.jsonl', Path(folder) / 'out.jsonl'
            records = [{'text': 'پردازش زبان طبیعی کار جالبی است', 'id': 1},
                       {'text': 'پردازش زبان طبیعی کار جالبی هست', 'id': 2},
                       {'text': 'سلام به همه دوستان', 'id': 3}]
            source = ''.join(json.dumps(row, ensure_ascii=False) + '\n' for row in records)
            inp.write_text(source, encoding='utf-8')
            summary = clean_dataset(inp, out, preset('general'), near_duplicate_threshold=0.8)
            self.assertEqual(summary['reasons']['near_duplicate'], 1)
            self.assertEqual(summary['kept'], 2)
            self.assertEqual(inp.read_text(encoding='utf-8'), source)

    def test_tsv_and_safe_destination_checks(self):
        with tempfile.TemporaryDirectory() as folder:
            inp, out = Path(folder) / 'in.tsv', Path(folder) / 'out.tsv'
            inp.write_text('text\tlabel\nسلام دنیا\tok\n', encoding='utf-8')
            summary = clean_dataset(inp, out, preset('general'))
            self.assertEqual(summary['kept'], 1)
            self.assertIn('\tok', out.read_text(encoding='utf-8'))
            with self.assertRaises(ValueError):
                clean_dataset(inp, inp, preset('general'))
            with self.assertRaises(ValueError):
                clean_dataset(inp, out, preset('general'), text_column='missing')
            with self.assertRaises(ValueError):
                clean_dataset(inp, out, preset('general'), min_length=10, max_length=2)

    def test_dataset_masking_does_not_retain_raw_text(self):
        with tempfile.TemporaryDirectory() as folder:
            inp, out = Path(folder) / 'input.jsonl', Path(folder) / 'output.jsonl'
            inp.write_text(json.dumps({'text': 'ایمیل ali@example.org'}) + '\n')
            clean_dataset(inp, out, replace(preset('general'), mask_pii=True))
            data = out.read_text()
            self.assertIn('<EMAIL>', data)
            self.assertNotIn('ali@example.org', data)

    def test_malformed_jsonl_keeps_previous_output_intact(self):
        with tempfile.TemporaryDirectory() as folder:
            inp, out = Path(folder) / 'input.jsonl', Path(folder) / 'output.jsonl'
            inp.write_text('{"text":"سلام دنیا"}\n{bad json}\n', encoding='utf-8')
            out.write_text('PREVIOUS CONTENT', encoding='utf-8')
            with self.assertRaises(ValueError):
                clean_dataset(inp, out, preset('general'))
            self.assertEqual(out.read_text(encoding='utf-8'), 'PREVIOUS CONTENT')


if __name__ == '__main__':
    unittest.main()
