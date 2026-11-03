"""Independent numeric oracles and round-trip tests for the course lab."""
import json
import math
from pathlib import Path
import tempfile
import unittest
from nlp_analyzer.normalization import normalize, normalization_audit, NormalizationOptions, unicode_inspect
from nlp_analyzer.tokenization import SubwordModel, tokenize, vocabulary_encode, prepare_batch, chunk_text
from nlp_analyzer.analytics import corpus_features, morphology, classify
from nlp_analyzer.lab import run_lab

CORPUS = ['I love NLP and books.', 'We love learning NLP.', 'سلام من کتاب فارسی می خوانم.', 'کتاب خوب است.']

class NormalizationTests(unittest.TestCase):
    def test_all_unicode_forms(self):
        import unicodedata
        for form in ('NFC','NFD','NFKC','NFKD'):
            text='é ﬁ'
            self.assertEqual(normalize(text,NormalizationOptions(unicode_form=form,spacing='none'))['text'],unicodedata.normalize(form,text))
    def test_spacing_and_idempotence(self):
        r=normalization_audit('می روم،کتاب ها روی میز هستند.')
        self.assertEqual(r['text'],'می‌روم، کتاب‌ها روی میز هستند.')
        self.assertTrue(r['idempotent'])
    def test_placeholders(self):
        r=normalization_audit('Visit https://example.com. Mail a@b.com @john ۱۲۳',NormalizationOptions(placeholders=True,casefold=True))
        self.assertEqual(r['text'],'visit <URL>. mail <EMAIL> <USER> <NUM>')
        self.assertTrue(r['idempotent'])
    def test_graphemes(self):
        r=unicode_inspect('e\u0301👨‍👩‍👧')
        self.assertEqual(r['grapheme_count'],2)
        self.assertEqual(r['code_points'],7)
        self.assertEqual(r['utf8_bytes'],len('e\u0301👨‍👩‍👧'.encode()))
    def test_dictionary_is_explicit(self):
        r=normalize('salam نمیدونم book coffee soooo',NormalizationOptions(lexical_map=True,elongation='language-aware'))
        self.assertEqual(r['text'],'سلام نمی‌دانم book coffee soo')
    def test_contractions(self):
        self.assertEqual(normalize("I don't know; we can't.",NormalizationOptions(expand_contractions=True))['text'],'I do not know; we cannot.')
    def test_hazm_spacing(self):
        self.assertIn('می‌روم',normalize('می روم',NormalizationOptions(spacing='hazm'))['text'])

class TokenizationTests(unittest.TestCase):
    def test_handout_sentence_exceptions(self):
        from nlp_analyzer.core import split_sentences
        self.assertEqual(split_sentences('Dr. Smith lives in the U.S.A. today. The value is 3.14.'), ['Dr. Smith lives in the U.S.A. today.', 'The value is 3.14.'])
        self.assertEqual(split_sentences('سلام؟ بله!'), ['سلام؟', 'بله!'])
    def test_handout_wordpunct(self):
        self.assertEqual(tokenize('I love NLP!','nltk'),['I','love','NLP','!'])
    def test_oov(self):
        r=vocabulary_encode(['cat cat dog'],'cat bird')
        self.assertEqual(r['unknown_rate'],.5)
        self.assertEqual(r['unknown_tokens'],['bird'])
    def test_batch(self):
        r=prepare_batch([[2,3],[4,5,6,7]],3)
        self.assertEqual(r['input_ids'],[[2,3,0],[4,5,6]])
        self.assertEqual(r['attention_mask'],[[1,1,0],[1,1,1]])
        self.assertEqual(r['truncated_counts'],[0,1])
        self.assertEqual(prepare_batch([[2]],3,side='left')['attention_mask'],[[0,0,1]])
        with self.assertRaises(ValueError):prepare_batch([[1,2]],1,truncation=False)
    def test_chunks_budget_and_coverage(self):
        r=chunk_text('One two. Three four. Five six. Seven eight.',4,2)
        self.assertTrue(all(c['token_count']<=4 for c in r['chunks']))
        covered={i for c in r['chunks'] for i in range(c['unit_start'],c['unit_end'])}
        self.assertEqual(covered,set(range(len(r['units']))))
        self.assertEqual(r['chunks'][1]['unit_start'],1)
    def test_long_sentence(self):
        r=chunk_text('one two three four five six seven',3,0)
        self.assertEqual(' '.join(c['text'] for c in r['chunks']),'one two three four five six seven')
    def test_train_save_reload(self):
        with tempfile.TemporaryDirectory() as d:
            for method in ('bpe','wordpiece','unigram','sentencepiece'):
                with self.subTest(method=method):
                    model=SubwordModel.train(CORPUS,method,300)
                    query='I love NLP! سلام'
                    encoded=model.encode(query)
                    self.assertEqual(len(encoded['ids']),len(encoded['tokens']))
                    self.assertTrue(encoded['ids'])
                    path=Path(d)/('tokenizer.model' if method=='sentencepiece' else 'tokenizer.json')
                    model.save(path)
                    self.assertEqual(encoded['ids'],SubwordModel.load(path).encode(query)['ids'])
                    if method=='bpe':
                        self.assertEqual(encoded['unknown_count'],0)
                        self.assertEqual(encoded['decoded'],query)
    def test_invalid_model_extension(self):
        model=SubwordModel.train(CORPUS)
        with self.assertRaises(ValueError):model.save('bad.model')
    def test_all_comparisons_available(self):
        r=run_lab('compare','I love NLP! سلام')
        self.assertEqual(len(r['comparisons']),8)
        self.assertTrue(all('error' not in v for v in r['comparisons']))

class AnalyticsTests(unittest.TestCase):
    def test_tfidf_hand_calculation(self):
        r=corpus_features(['cat cat dog','dog bird'])
        self.assertEqual(r['vocabulary'],['bird','cat','dog'])
        self.assertEqual(r['bow'],[[0,2,1],[1,0,1]])
        a=math.log(3/2)+1
        self.assertEqual(r['document_frequency'],[1,1,2])
        self.assertAlmostEqual(r['idf'][0],a)
        self.assertAlmostEqual(r['tfidf'][0][1],2*a/math.sqrt(4*a*a+1))
        self.assertAlmostEqual(r['cosine_similarity'][0][1],1/math.sqrt((4*a*a+1)*(a*a+1)))
        self.assertEqual(r['token_count'],5)
        self.assertEqual(r['type_count'],3)
        self.assertEqual(r['type_token_ratio'],.6)
    def test_against_sklearn(self):
        from sklearn.feature_extraction.text import TfidfVectorizer
        from nlp_analyzer.analytics import words
        import numpy as np
        r=corpus_features(CORPUS)
        v=TfidfVectorizer(tokenizer=words,token_pattern=None,lowercase=False)
        expected=v.fit_transform(CORPUS).toarray()
        np.testing.assert_allclose(r['tfidf'],expected)
    def test_ngrams_empty(self):
        self.assertEqual(corpus_features(['a b c'],2)['vocabulary'],['a b','b c'])
        self.assertEqual(corpus_features([''])['cosine_similarity'],[[0]])
    def test_morphology(self):
        self.assertEqual(morphology('running books','en')['tokens'],['run','book'])
        self.assertTrue(morphology('کتاب‌ها','fa','lemma')['tokens'])
    def test_classification_and_leakage(self):
        records=[{'text':'good useful','label':'positive'},{'text':'bad awful','label':'negative'}]
        r=classify(records,'good')
        self.assertEqual(r['prediction'],'positive')
        self.assertAlmostEqual(sum(r['probabilities'].values()),1)
        self.assertIsNone(r['evaluation'])
        with self.assertRaises(ValueError):classify(records,'good',[records[0]])
        r=classify(records,'good',[{'text':'useful good lesson','label':'positive'}])
        self.assertEqual(r['evaluation']['rows'],1)

if __name__=='__main__':unittest.main()
