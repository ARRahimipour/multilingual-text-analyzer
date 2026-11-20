"""Printable, dependency-free checks for Persian whitespace and Unicode."""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from nlp_analyzer.normalization import normalize, NormalizationOptions
from nlp_analyzer.spacing_inspection import visible_spaces

OPTIONS = NormalizationOptions(spacing='conservative', digit_style='ascii', remove_marks=True)
CASES = [
    ('مي روم', 'می‌روم'),
    ('كتاب ها', 'کتاب‌ها'),
    ('كتابها', 'کتاب‌ها'),
    ('كتابهاي', 'کتاب‌های'),
    ('ميروم', 'می‌روم'),
    ('ميخواهم', 'می‌خواهم'),
    ('می  ‌  روم', 'می‌روم'),
    ('نمیدانم', 'نمی‌دانم'),
    ('تنها', 'تنها'),
    ('روی میز', 'روی میز'),
    ('سلام !   خوبی ؟', 'سلام! خوبی؟'),
    ('۱۲۳ و ١٢٣', '123 و 123'),
]


def main():
    for index, (source, expected) in enumerate(CASES, 1):
        actual = normalize(source, OPTIONS)['text']
        stable = normalize(actual, OPTIONS)['text'] == actual
        if actual != expected or not stable:
            raise AssertionError(f'Case {index}: {source!r} → {actual!r}; expected {expected!r}; stable={stable}')
        print(f'{index:02d}  OK  {source}  →  {actual}')
    print('\nVisible space demonstration:')
    print(visible_spaces('می‌روم و کتاب ها'))
    print(f'PASS: {len(CASES)} Persian Unicode/spacing cases; idempotence verified.')


if __name__ == '__main__':
    main()
