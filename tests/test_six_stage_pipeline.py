"""Checks the six *ordered* stages against the handout's examples."""
import importlib.util
import json
import unittest
from nlp_analyzer.lab import run_lab
from nlp_analyzer.six_stage_pipeline import run_six_stage_pipeline


EN = dict(language='en', tokenizer='regex', stopword_mode='custom',
          custom_stopwords=[], morph_method='stem')
FA = dict(language='fa', tokenizer='regex', normalization={'spacing': 'conservative'},
          stopword_mode='custom', custom_stopwords=[], morph_method='none')


class SixStagePipelineTests(unittest.TestCase):
    def test_six_snapshots_and_no_source_mutation(self):
        text = '<p>کتاب ها و كتابها!</p> https://example.org'
        result = run_lab('six_stages', text, **FA)
        stages = result['stages']
        self.assertEqual([s['stage'] for s in stages],
                         ['raw', 'cleaning', 'normalization', 'tokenization', 'stopwords', 'morphology'])
        self.assertEqual([s['number'] for s in stages], list(range(1, 7)))
        self.assertEqual(stages[0]['output'], text)
        self.assertIn('کتاب‌ها', stages[2]['output'])
        self.assertNotIn('<p>', stages[1]['output'])
        self.assertNotIn('example.org', stages[1]['output'])
        self.assertTrue(stages[2]['idempotent'])
        self.assertEqual(result['source'], text)

    def test_handout_english_nine_to_four(self):
        result = run_six_stage_pipeline('the children were running and the cats are sleeping',
            **(EN | {'custom_stopwords': ['the', 'were', 'and', 'are']}))
        self.assertEqual(result['stages'][3]['token_count'], 9)
        self.assertEqual(result['stages'][4]['tokens'], ['children', 'running', 'cats', 'sleeping'])
        self.assertEqual(result['stages'][5]['tokens'], ['children', 'run', 'cat', 'sleep'])
        self.assertEqual(result['statistics']['removed_stopwords'], 5)
        self.assertEqual(result['statistics']['final_unique_words'], 4)

    def test_sentence_splitting_before_punctuation_deletion(self):
        result = run_six_stage_pipeline('One! Two? Three. URL https://a.org',
            **(EN | {'cleaning_preset': 'topic', 'remove_stopwords': False}))
        self.assertNotIn('!', result['stages'][1]['output'])
        self.assertEqual(len(result['sentences']), 4)
        self.assertIn('three.', result['sentences'])

    def test_persian_normalization_and_zwnj(self):
        result = run_six_stage_pipeline('من مي روم و كتاب ها ۱۲۳ را می خوانم.', **FA)
        tokens = result['stages'][3]['tokens']
        self.assertIn('می‌روم', tokens)
        self.assertIn('کتاب‌ها', tokens)
        self.assertIn('123', tokens)
        self.assertEqual(result['stages'][4]['tokens'], tokens)

    def test_optional_stopwords_and_morphology(self):
        result = run_six_stage_pipeline('The children were running',
            **(EN | {'remove_stopwords': False, 'morph_method': 'none'}))
        self.assertFalse(result['stages'][4]['enabled'])
        self.assertEqual(result['stages'][3]['tokens'], result['stages'][4]['tokens'])
        self.assertEqual(result['stages'][4]['tokens'], result['stages'][5]['tokens'])
        self.assertEqual(result['stages'][5]['method'], 'none')

    def test_protected_domain_terms_and_negation(self):
        result = run_six_stage_pipeline('This film is not good',
            **(EN | {'custom_stopwords': ['this', 'film', 'not', 'is'],
                     'protected_words': ['film']}))
        kept = result['stages'][4]['tokens']
        self.assertIn('not', kept)
        self.assertIn('film', kept)
        self.assertNotIn('this', kept)
        self.assertNotIn('is', kept)
        self.assertEqual(result['stages'][4]['removed_count'], 2)

    def test_sentiment_keeps_emoji_and_topic_removes_it(self):
        source = 'Great😍! Awful!!!!'
        sentiment = run_six_stage_pipeline(source, **(EN | {'cleaning_preset': 'sentiment'}))
        topic = run_six_stage_pipeline(source, **(EN | {'cleaning_preset': 'topic'}))
        self.assertIn('😍', sentiment['stages'][1]['output'])
        self.assertNotIn('😍', topic['stages'][1]['output'])

    def test_num_placeholder_remains_whole_token(self):
        result = run_six_stage_pipeline('Price 123 and cost ٤٥!',
            **(EN | {'cleaning': {'number_mode': 'placeholder'}}))
        self.assertEqual(result['stages'][3]['tokens'].count('<NUM>'), 2)

    def test_bad_options_and_statistical_corpus(self):
        with self.assertRaisesRegex(ValueError, 'Unknown stage options'):
            run_six_stage_pipeline('Hi', **(EN | {'cleaning': {'bogus': True}}))
        with self.assertRaisesRegex(ValueError, 'multiple corpus'):
            run_six_stage_pipeline('cat dog', **(EN | {'stopword_mode': 'statistical'}))
        with self.assertRaisesRegex(ValueError, 'Never apply both'):
            run_six_stage_pipeline('Hello', **(EN | {'morph_method': 'stem+lemma'}))

    def test_exportable_all_details(self):
        result = run_six_stage_pipeline('The cats running.', **EN)
        saved = json.loads(json.dumps(result, ensure_ascii=False))
        self.assertEqual(len(saved['stages']), 6)
        self.assertEqual(len(saved['stages'][5]['mappings']), 3)
        self.assertTrue(saved['statistics']['normalization_idempotent'])

    @unittest.skipUnless(importlib.util.find_spec('hazm'), 'Optional Hazm not installed')
    def test_real_hazm_backend(self):
        result = run_six_stage_pipeline('من کتاب ها را می خوانم. این کتاب‌ها عالی هستند!',
                                        language='fa', morph_method='stem')
        self.assertEqual(result['tokenizer'], 'hazm')
        self.assertEqual(len(result['stages']), 6)
        self.assertTrue(result['stages'][5]['backend'].startswith('Hazm'))
        self.assertGreaterEqual(len(result['sentences']), 2)


if __name__ == '__main__': unittest.main()
