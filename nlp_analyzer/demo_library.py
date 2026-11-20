"""Curated UTF-8 research cases aligned to the six-stage teaching pipeline.

Cases are inputs for inspection, not a claim of perfect automatic correction.
All descriptions and documentation are in English; source text stays in its
original language so that Unicode and morphology can be tested.
"""

DEMO_CASES = {
    'mixed': {'label': '01  Mixed web & Unicode', 'file': '01_web_mixed_fa.txt', 'language': 'fa', 'cleaning': 'general', 'description': 'HTML, scripts, URLs, email, emoji, hashtags, elongated letters, mixed digits and ZWNJ.'},
    'spacing': {'label': '02  Persian spacing stress', 'file': '02_zwnj_unicode_fa.txt', 'language': 'fa', 'cleaning': 'general', 'description': 'Arabic/Persian letters, separated or missing half-spaces, diacritics, NBSP and joined emoji.'},
    'sentiment': {'label': '03  Sentiment & negation', 'file': '03_sentiment_negation_fa.txt', 'language': 'fa', 'cleaning': 'sentiment', 'description': 'Positive, negative and sarcastic opinions. Retain emojis and negation for meaningful analysis.'},
    'morphology': {'label': '04  Inflections & morphology', 'file': '04_morphology_fa.txt', 'language': 'fa', 'cleaning': 'general', 'description': 'Nouns, plurals, verbal inflections and comparison of stemming versus lemmatization.'},
    'frequency': {'label': '05  Frequency / Zipf sketch', 'file': '05_frequency_zipf_fa.txt', 'language': 'fa', 'cleaning': 'topic', 'description': 'Repetition, unique terms, stopword effects, frequency tables and a small illustrative Zipf sample.'},
    'pdf_noise': {'label': '06  PDF/OCR noisy source', 'file': '06_pdf_ocr_noisy_fa.txt', 'language': 'fa', 'cleaning': 'general', 'description': 'Split lines, presentation forms, invisible controls and page furniture; some need document-level cleaning.'},
    'entities': {'label': '07  Entities & privacy', 'file': '07_entities_privacy_fa.txt', 'language': 'fa', 'cleaning': 'ner', 'description': 'Synthetic identifiers, dates, prices, emails, links and mentions; compare General versus NER.'},
    'informal': {'label': '08  Informal mixed-language', 'file': '08_colloquial_mixed_fa.txt', 'language': 'fa', 'cleaning': 'general', 'description': 'Colloquial Persian, English technical terms, punctuation, social media and mixed digits.'},
    'english': {'label': '09  English baseline', 'file': '09_english_benchmark.txt', 'language': 'en', 'cleaning': 'general', 'description': 'Porter/NLTK, tense and plural forms, negation, English sentence boundaries and HTML.'},
}
