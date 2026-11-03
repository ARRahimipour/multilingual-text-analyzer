"""Produce inspectable local reports for every course lab activity."""
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from nlp_analyzer.lab import run_lab, save_lab_report
root=Path(__file__).resolve().parents[1]
corpus=(root/'examples/lab_corpus.txt').read_text(encoding='utf-8').splitlines()
text='سلام! من کتاب ها را می خوانم. I love learning NLP!'
output=root/'outputs/course-demo';output.mkdir(parents=True,exist_ok=True)
for op in ('normalize','unicode','compare','oov','batch','chunk','morphology','features'):
    save_lab_report(run_lab(op,text,corpus),output/(op+'.json'))
for method in ('bpe','wordpiece','unigram','sentencepiece'):
    model=output/(method+('.model' if method=='sentencepiece' else '.json'))
    save_lab_report(run_lab('subword',text,corpus,method=method,save_model=str(model)),output/(method+'-report.json'))
for op in ('batch','chunk'):
    save_lab_report(run_lab(op,text,corpus,model_file=str(output/'bpe.json'),max_length=40,overlap=6),output/(op+'-bpe.json'))
load=lambda name:[json.loads(row) for row in (root/'examples'/name).read_text().splitlines()]
save_lab_report(run_lab('classify','A useful book',training_records=load('classification_train.jsonl'),evaluation_records=load('classification_holdout.jsonl')),output/'classification.json')
print('Reports and reusable tokenizers written to',output)
