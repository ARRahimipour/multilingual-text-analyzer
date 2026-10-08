"""Behavioral checks for homework metrics and multilingual edge cases."""
import unittest
from pathlib import Path
from nlp_analyzer import AnalysisOptions, analyze


class AnalysisTests(unittest.TestCase):
    def test_hand_counted_example(self):
        result = analyze('Hello world! Hello NLP. NLP is useful.')
        self.assertEqual((result.sentence_count, result.word_count, result.unique_word_count), (3, 7, 5))
        self.assertEqual(result.top_words[:2], [{'word': 'hello', 'count': 2}, {'word': 'nlp', 'count': 2}])
        self.assertEqual(result.singleton_word_count, 3)

    def test_empty_and_punctuation(self):
        for text in ['', '  \n\t ', '... ؟! — 😀']:
            with self.subTest(text=text):
                result = analyze(text)
                self.assertEqual((result.sentence_count, result.word_count, result.unique_word_count), (0, 0, 0))
                self.assertEqual(result.top_words, [])

    def test_persian_normalization_is_opt_in(self):
        text = 'كتاب کتاب علي علی'
        self.assertEqual(analyze(text).unique_word_count, 4)
        result = analyze(text, AnalysisOptions(persian_normalization=True))
        self.assertEqual(result.frequencies, {'کتاب': 2, 'علی': 2})

    def test_persian_joiner_and_question(self):
        result = analyze('من می‌روم. تو می‌روی؟')
        self.assertEqual(result.word_count, 4)
        self.assertEqual(result.sentence_count, 2)
        self.assertIn('می‌روم', result.tokens)

    def test_arabic_marks(self):
        self.assertEqual(analyze('مَرْحَبًا بالعالم!').word_count, 2)

    def test_canonical_unicode(self):
        self.assertEqual(analyze('café cafe\u0301').frequencies, {'café': 2})

    def test_casefold(self):
        self.assertEqual(analyze('Hello HELLO hello').unique_word_count, 1)
        self.assertEqual(analyze('Hello HELLO hello', AnalysisOptions(case_sensitive=True)).unique_word_count, 3)

    def test_contractions(self):
        result = analyze("Don't don’t l’amour rock'n'roll")
        self.assertEqual(result.word_count, 4)
        self.assertEqual(result.frequencies["don't"], 2)

    def test_hyphens_and_emoji(self):
        self.assertEqual(analyze('well-known 😀 text').tokens, ['well', 'known', 'text'])

    def test_numbers(self):
        self.assertEqual(analyze('2026 ۱۲۳ NLP2').tokens, ['nlp2'])
        self.assertEqual(analyze('2026 ۱۲۳ NLP2', AnalysisOptions(include_numbers=True)).word_count, 3)

    def test_decimals_do_not_split_sentences(self):
        result = analyze('The value is 3.14. Next value is 2.5!')
        self.assertEqual(result.sentence_count, 2)

    def test_titles_and_initials(self):
        result = analyze('Dr. Smith met J. Doe. They talked!')
        self.assertEqual(result.sentence_count, 2)

    def test_quotes_and_repeated_endings(self):
        result = analyze('He said "Hello!" Really?! Yes...')
        self.assertEqual(result.sentence_count, 3)
        self.assertEqual(result.sentences[0], 'He said "Hello!"')

    def test_paragraphs_and_wrapping(self):
        self.assertEqual(analyze('One wrapped\nline\n\nSecond paragraph').sentence_count, 2)

    def test_missing_final_punctuation(self):
        self.assertEqual(analyze('First. Second').sentence_count, 2)

    def test_multilingual_sentence_endings(self):
        for text in ['سلام! خوبی؟ بله.', '你好。世界！', 'नमस्ते दुनिया। फिर मिलेंगे।', 'Բարեւ։ Բարեւ։']:
            with self.subTest(text=text):
                self.assertGreaterEqual(analyze(text).sentence_count, 2)

    def test_language_smoke_cases(self):
        samples = {
            'French': ('Bonjour le monde!', 3), 'German': ('Guten Tag Welt!', 3),
            'Russian': ('Привет мир!', 2), 'Greek': ('Γεια σου κόσμε!', 3),
            'Hindi': ('नमस्ते दुनिया।', 2), 'Spanish': ('¡Hola mundo!', 2),
            'Turkish': ('Merhaba güzel dünya!', 3), 'Korean': ('안녕하세요 세계!', 2),
            'Hebrew': ('שלום עולם!', 2), 'Bengali': ('হ্যালো বিশ্ব!', 2),
        }
        for language, (text, count) in samples.items():
            with self.subTest(language=language):
                self.assertEqual(analyze(text).word_count, count)

    def test_unspaced_script_warning(self):
        for text in ['你好世界', 'こんにちは世界', 'สวัสดีโลก', 'សួស្តី', 'မင်္ဂလာပါ']:
            with self.subTest(text=text):
                self.assertTrue(analyze(text).warnings)

    def test_no_stopword_removal(self):
        self.assertEqual(analyze('the the and').frequencies, {'the': 2, 'and': 1})

    def test_ties_follow_source_order(self):
        self.assertEqual([row['word'] for row in analyze('z b a').top_words], ['z', 'b', 'a'])

    def test_top_n(self):
        self.assertEqual(len(analyze('a b c', AnalysisOptions(top_n=2)).top_words), 2)

    def test_sample_exactly_300_words(self):
        sample = Path(__file__).resolve().parents[1] / 'examples' / 'english_300.txt'
        result = analyze(sample.read_text(encoding='utf-8'))
        self.assertEqual((result.word_count, result.sentence_count, result.unique_word_count), (300, 26, 207))
        self.assertEqual(result.top_words[0], {'word': 'the', 'count': 19})

    def test_invariants(self):
        for text in ['a a b', 'سلام دنیا؟ سلام!', 'नमस्ते दुनिया।', '', 'Hello 123.']:
            result = analyze(text)
            self.assertEqual(sum(result.frequencies.values()), result.word_count)
            self.assertEqual(len(result.frequencies), result.unique_word_count)
            self.assertLessEqual(result.singleton_word_count, result.unique_word_count)

    def test_bad_options(self):
        for value in [0, -1, 1.5, True]:
            with self.subTest(value=value), self.assertRaises(ValueError):
                AnalysisOptions(top_n=value)

    def test_arbitrary_lengths(self):
        for size in [0, 1, 298, 300, 301, 10000]:
            with self.subTest(size=size):
                result = analyze('word ' * size)
                self.assertEqual(result.word_count, size)
                self.assertEqual(result.unique_word_count, int(size > 0))
                self.assertNotIn('target_met', result.to_dict())
                self.assertNotIn('target_words', result.options)

    def test_persian_numbers_explain_two_token_difference(self):
        text = 'سال فارسی ۱۴۰۵ و سال انگلیسی ۲۰۲۶ است.'
        without_numbers = analyze(text)
        with_numbers = analyze(text, AnalysisOptions(include_numbers=True))
        self.assertEqual(without_numbers.word_count, 6)
        self.assertEqual(with_numbers.word_count, 8)
        self.assertEqual(with_numbers.frequencies['سال'], 2)
        self.assertEqual(with_numbers.frequencies['۱۴۰۵'], 1)
        self.assertEqual(with_numbers.frequencies['۲۰۲۶'], 1)
        self.assertEqual(with_numbers.sentence_count, 1)

    def test_independently_counted_multilingual_frequencies(self):
        from collections import Counter
        words = ['hello', 'دنیا', 'नमस्ते', 'κόσμος', 'hello', 'دنیا', 'world']
        result = analyze(' '.join(words) + '.', AnalysisOptions(case_sensitive=True))
        expected = Counter(words)
        self.assertEqual(result.frequencies, dict(expected))
        self.assertEqual(result.word_count, len(words))
        self.assertEqual(result.unique_word_count, len(set(words)))
        self.assertEqual(result.singleton_word_count, 3)
        self.assertEqual(result.sentence_count, 1)

    def test_quoted_punctuation_examples(self):
        text = 'برنامه باید نشانه‌های «،»، «؛»، «؟» و «!» را مدیریت کند.'
        result = analyze(text)
        self.assertEqual(result.sentence_count, 1)
        self.assertEqual(result.sentences, [text])

    def test_quoted_symbols_across_quote_styles(self):
        for opening, closing in [('«', '»'), ('“', '”'), ('"', '"'),
                                 ("'", "'"), ('「', '」'), ('『', '』')]:
            with self.subTest(opening=opening):
                text = f'Use {opening}?!{closing} carefully. Next sentence.'
                self.assertEqual(analyze(text).sentence_count, 2)

    def test_real_quoted_sentences_still_split(self):
        result = analyze('او گفت «سلام!» سپس رفت. خوبی؟')
        self.assertEqual(result.sentence_count, 3)
        self.assertEqual(result.sentences[0], 'او گفت «سلام!»')

    def test_unmatched_quote_does_not_hide_endings(self):
        self.assertEqual(analyze('Hello «world! Next sentence.').sentence_count, 2)

    def test_uploaded_persian_report_regression(self):
        path = Path(__file__).resolve().parents[1] / 'examples' / 'persian_regression.txt'
        text = path.read_text(encoding='utf-8')
        for include_numbers, expected in [(False, (19, 298, 181, 130)),
                                           (True, (19, 300, 183, 132))]:
            result = analyze(text, AnalysisOptions(persian_normalization=True,
                                                  include_numbers=include_numbers))
            self.assertEqual((result.sentence_count, result.word_count,
                              result.unique_word_count, result.singleton_word_count), expected)
            self.assertEqual(result.top_words[0], {'word': 'و', 'count': 16})

    def test_bad_input(self):
        with self.assertRaises(TypeError):
            analyze(None)

    def test_bom_and_newlines(self):
        self.assertEqual(analyze('\ufeffHello\r\nworld.').tokens, ['hello', 'world'])


if __name__ == '__main__':
    unittest.main()
