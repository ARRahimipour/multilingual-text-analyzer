"""Reproduce the expanded handout exercises with local example data."""
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from nlp_analyzer.lab import run_lab, save_lab_report
root=Path(__file__).resolve().parents[1]; examples=root/'examples'; out=root/'outputs/expanded-demo'
load=lambda name:json.loads((examples/name).read_text(encoding='utf-8'))
corpus=(examples/'representation_fa.txt').read_text(encoding='utf-8').splitlines()
for op,config in [('representation','textbook_config.json'),('search','retrieval_config.json'),
                  ('stopwords','stopwords_config.json'),('pipeline','pipeline_config.json')]:
    docs=(examples/'search_fa.txt').read_text(encoding='utf-8').splitlines() if op=='search' else corpus
    save_lab_report(run_lab(op,'این فیلم خوب نیست',docs,**load(config)),out/(op+'.json'))
records=lambda name:[json.loads(s) for s in (examples/name).read_text(encoding='utf-8').splitlines()]
save_lab_report(run_lab('classify_compare','فیلم خوب',training_records=records('classification_fa_train.jsonl'),
    evaluation_records=records('classification_fa_holdout.jsonl'),**load('classification_compare_config.json')),out/'classification.json')
word_corpus=(examples/'word_label_corpus.txt').read_text().splitlines()
save_lab_report(run_lab('learn_stopwords','',word_corpus,**load('learned_stopwords_config.json')),out/'learned-stopwords.json')
save_lab_report(run_lab('library_pipeline','این کتاب‌ها بسیار خوب هستند.'),out/'hazm-pipeline.json')
print('Expanded exercise reports written to',out)
