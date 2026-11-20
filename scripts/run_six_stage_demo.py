"""Run both lecture examples and write complete UTF-8 JSON reports."""
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from nlp_analyzer.lab import run_lab, save_lab_report


def main():
    folder = ROOT / 'outputs' / 'six_stages'
    folder.mkdir(parents=True, exist_ok=True)
    configs = [
        ('english', 'the children were running and the cats are sleeping',
         'six_stages_english_config.json'),
        ('persian', (ROOT / 'examples/six_stages_sample_fa.txt').read_text(encoding='utf-8'),
         'six_stages_persian_config.json'),
    ]
    for label, source, name in configs:
        config = json.loads((ROOT / 'examples' / name).read_text(encoding='utf-8'))
        try:
            result = run_lab('six_stages', source, **config)
        except (ImportError, ValueError) as exc:
            print(f'{label} not run: {exc}')
            continue
        target = folder / (label + '.json')
        save_lab_report(result, target)
        print(f'{label}: {len(result["stages"])} stages -> {target}')
        for stage in result['stages']:
            print('  ', stage['title'], ':', stage.get('token_count', len(stage['output'])))


if __name__ == '__main__':
    main()
