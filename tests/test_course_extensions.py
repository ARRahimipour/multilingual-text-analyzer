"""Independent numeric oracles and regression tests for expanded exercises."""
import unittest
import math
from nlp_analyzer.course_extensions import (representation, search_documents, stopword_activity,
    pipeline_comparison, classification_comparison, learned_stopwords)
from nlp_analyzer.analytics import morphology
from nlp_analyzer.lab import run_lab

DOCS=['فیلم خوب بود','فیلم بد بود','غذا خوب بود','فیلم فیلم عالی بود']
TRAIN=[{'text':t,'label':l} for t,l in [('good useful book','positive'),('excellent helpful lesson','positive'),
 ('wonderful enjoyable course','positive'),('great lovely product','positive'),('bad boring book','negative'),
 ('awful useless lesson','negative'),('terrible disappointing course','negative'),('poor broken product','negative')]]
TEST=[{'text':'good wonderful unseenword','label':'positive'},{'text':'awful terrible','label':'negative'}]

class RepresentationTests(unittest.TestCase):
    def test_page_110_textbook_values(self):
        r=representation(DOCS,idf_mode='textbook',norm='none');v=r['vocabulary']
        self.assertEqual(r['idf'][v.index('بود')],0)
        self.assertTrue(all(row[v.index('بود')]==0 for row in r['tfidf']))
        self.assertAlmostEqual(r['tfidf'][3][v.index('فیلم')],2*math.log(4/3))
        self.assertAlmostEqual(r['tfidf'][0][v.index('خوب')],math.log(2))
    def test_sklearn_agrees(self):
        from sklearn.feature_extraction.text import TfidfVectorizer
        from nlp_analyzer.course_extensions import text_tokens
        import numpy as np
        expected=TfidfVectorizer(tokenizer=text_tokens,token_pattern=None,lowercase=False).fit_transform(DOCS)
        np.testing.assert_allclose(representation(DOCS)['tfidf'],expected.toarray())
    def test_sparse_roundtrip(self):
        from scipy.sparse import csr_matrix
        r=representation(DOCS);m=r['bow_csr']
        self.assertEqual(csr_matrix((m['data'],m['indices'],m['indptr']),shape=m['shape']).toarray().tolist(),r['bow'])
    def test_feature_controls(self):
        r=representation(['cat cat dog','cat bird'],language='en',binary=True,ngram_min=1,ngram_max=2,min_df=2)
        self.assertEqual(r['vocabulary'],['cat']);self.assertEqual(r['bow'],[[1],[1]])
    def test_zero_vectors(self):
        r=representation(['cat','cat'],language='en',idf_mode='textbook',norm='l2')
        self.assertEqual(r['tfidf'],[[0],[0]]);self.assertEqual(r['cosine_similarity'],[[0,0],[0,0]])
    def test_sparse_large_preview(self):
        r=representation(['term'+str(i) for i in range(110)],language='en')
        self.assertNotIn('bow',r);self.assertNotIn('cosine_similarity',r);self.assertEqual(r['bow_csr']['nnz'],110)
    def test_search_no_query_fit(self):
        r=search_documents(['python tutorial','cooking pasta','python course'],['python tutorial','never-seen'],language='en')
        self.assertEqual(r['queries'][0]['matches'][0]['document_index'],0)
        self.assertAlmostEqual(r['queries'][0]['matches'][0]['score'],1)
        self.assertTrue(r['queries'][1]['zero_vector']);self.assertNotIn('never',r['vocabulary'])
    def test_persian_query_normalization(self):
        r=search_documents(['کتاب فارسی','غذا'],['كتاب فارسي'])
        self.assertAlmostEqual(r['queries'][0]['matches'][0]['score'],1)
    def test_invalid_settings(self):
        for kwargs in ({'idf_mode':'unknown'},{'ngram_min':3,'ngram_max':1}):
            with self.assertRaises(ValueError):representation(DOCS,**kwargs)

class StopwordTests(unittest.TestCase):
    def test_protected_negation_and_domain(self):
        r=stopword_activity('این فیلم خوب نیست',['این فیلم خوب نیست'],custom_stopwords=['نیست','فیلم'],protected_words=['فیلم'])
        self.assertIn('نیست',r['tokens']);self.assertIn('فیلم',r['tokens'])
    def test_statistical_idf(self):
        r=stopword_activity('the cat',['the cat','the dog'],language='en',stopword_mode='statistical',max_idf=0)
        self.assertEqual(r['removed_tokens'],['the']);self.assertEqual(r['tokens'],['cat'])
    def test_custom_mapping(self):
        r=stopword_activity('كتاب خوب است',['کتاب خوب است'],stopword_mode='custom',custom_stopwords=['کتاب'])
        self.assertEqual(r['removed_tokens'],['کتاب'])
    def test_four_stage_comparison(self):
        r=pipeline_comparison('كتاب کتاب و کتاب‌ها خوب نیست')
        self.assertEqual(len(r['stages']),4)
        self.assertLess(r['stages'][1]['type_count'],r['stages'][0]['type_count'])
        self.assertIn('نیست',r['stages'][2]['tokens'])
    def test_english_stemmers(self):
        for stemmer in ('porter','snowball','lancaster'):
            self.assertEqual(morphology('running','en',stemmer=stemmer)['tokens'],['run'])
    def test_learned_word_labels(self):
        corpus=['the and of to cat dog bird fish']*3
        labels=[{'word':w,'label':int(i<4)} for i,w in enumerate(corpus[0].split())]
        r=learned_stopwords(corpus,labels,language='en')
        self.assertEqual(r['holdout_words'],2);self.assertEqual(r['training_words'],6)
        self.assertAlmostEqual(sum(r['feature_importance'].values()),1)
        self.assertTrue(all(0<=v['stopword_probability']<=1 for v in r['rows']))

class ClassificationTests(unittest.TestCase):
    def test_holdout_and_metrics(self):
        r=classification_comparison(TRAIN,TEST,'good',language='en')
        self.assertNotIn('unseenword',r['vocabulary']);self.assertEqual(len(r['rows']),2)
        for row in r['rows']:
            self.assertEqual(sum(map(sum,row['confusion_matrix'])),len(TEST));self.assertTrue(0<=row['f1_macro']<=1)
    def test_stratified_reproducible(self):
        a=classification_comparison(TRAIN,language='en');b=classification_comparison(TRAIN,language='en')
        self.assertEqual(a,b);self.assertEqual(a['evaluation_rows'],2)
    def test_normalized_leakage(self):
        with self.assertRaises(ValueError):
            classification_comparison([{'text':'کتاب','label':'a'},{'text':'غذا','label':'b'}],[{'text':'كتاب','label':'a'}])
    def test_invalid_records(self):
        with self.assertRaises(ValueError):classification_comparison([{'text':None,'label':'a'}])
    def test_lab_dispatch(self):
        self.assertIn('bow_csr',run_lab('representation','',DOCS));self.assertIn('queries',run_lab('search','فیلم',DOCS))
        self.assertIn('tokens',run_lab('stopwords','فیلم',DOCS));self.assertEqual(len(run_lab('pipeline','کتاب خوب است')['stages']),4)

class LibraryPipelineTests(unittest.TestCase):
    def test_actual_hazm_pipeline(self):
        r=run_lab('library_pipeline','این کتاب‌ها خوب هستند. من می‌روم.')
        self.assertEqual(r['backend'],'Hazm');self.assertEqual(len(r['sentences']),2);self.assertTrue(r['tokens'])
    def test_english_resource_error_is_actionable(self):
        from unittest.mock import patch
        with patch('nltk.sent_tokenize',side_effect=LookupError('missing corpus')):
            with self.assertRaisesRegex(ValueError,'setup_resources.py'):
                run_lab('library_pipeline','A sentence.',language='en')
