"""Clean UTF-8 CSV/TSV/JSONL datasets without overwriting their source files."""
from collections import Counter, defaultdict
import csv
from difflib import SequenceMatcher
import json
import os
from pathlib import Path
import tempfile
from .core import tokenize_words
from .preprocessing import PreprocessOptions, clean_text, persian_script_ratio


def _shingles(text):
    """Candidate index for approximate duplicates (a recall-oriented heuristic)."""
    words = text.casefold().split()
    if len(words) >= 3:
        return {' '.join(words[i:i + 3]) for i in range(len(words) - 2)}
    compact = text.casefold()
    return {compact[i:i + 3] for i in range(max(0, len(compact) - 2))} or {compact}


def clean_dataset(source: str | Path, destination: str | Path, options: PreprocessOptions,
                  *, text_column: str = 'text', min_length: int = 3,
                  max_length: int = 5000, min_persian_ratio: float = 0.0,
                  deduplicate: bool = True, near_duplicate_threshold: float | None = None) -> dict:
    """Filter cleaned text records and return counts, lengths and vocabulary stats.

    Exact deduplication happens *after* normalization/cleaning. Optional near
    deduplication compares candidates sharing character or word shingles;
    it is a heuristic and should not be used as a train/test leakage guarantee.
    Original rows are never included in the summary.
    """
    source, destination = Path(source), Path(destination)
    if source.resolve() == destination.resolve():
        raise ValueError('Dataset output must not overwrite the input file.')
    if source.suffix.lower() not in ('.csv', '.tsv', '.jsonl'):
        raise ValueError('Dataset must be .csv, .tsv, or .jsonl.')
    if source.suffix.lower() != destination.suffix.lower():
        raise ValueError('Dataset output must use the same extension as the input.')
    if isinstance(min_length, bool) or isinstance(max_length, bool) or not (0 <= min_length <= max_length):
        raise ValueError('Require 0 <= min_length <= max_length.')
    if not 0 <= min_persian_ratio <= 1:
        raise ValueError('min_persian_ratio must be between 0 and 1.')
    if near_duplicate_threshold is not None and not 0.7 <= near_duplicate_threshold < 1:
        raise ValueError('near_duplicate_threshold must be >= 0.7 and < 1.')
    if near_duplicate_threshold is not None and not deduplicate:
        raise ValueError('Near-duplicate filtering requires deduplicate=True.')

    counts = Counter()
    before_lengths, after_lengths = 0, 0
    before_vocab, after_vocab = set(), set()
    seen = set()
    kept_texts = []
    shingles_index = defaultdict(set)

    def cleaned_rows(rows):
        nonlocal before_lengths, after_lengths
        for row in rows:
            counts['input'] += 1
            if text_column not in row:
                raise ValueError(f'Missing dataset text column: {text_column}')
            raw = row[text_column]
            before_lengths += len(raw) if isinstance(raw, str) else 0
            if not isinstance(raw, str) or not raw.strip():
                counts['empty'] += 1
                continue
            outcome = clean_text(raw, options)
            cleaned = outcome.text
            before_vocab.update(tokenize_words(raw.casefold()))
            if not cleaned:
                counts['empty_after_cleaning'] += 1
                continue
            if len(cleaned) < min_length:
                counts['too_short'] += 1
                continue
            if len(cleaned) > max_length:
                counts['too_long'] += 1
                continue
            if persian_script_ratio(cleaned) < min_persian_ratio:
                counts['script_ratio'] += 1
                continue
            key = cleaned.casefold()
            if deduplicate and key in seen:
                counts['exact_duplicate'] += 1
                continue
            if near_duplicate_threshold is not None:
                grams = _shingles(key)
                candidates = set().union(*(shingles_index[s] for s in grams))
                # Limit very common-shingle comparisons to keep costs bounded.
                is_near = any(SequenceMatcher(None, key, kept_texts[index], autojunk=False).ratio()
                              >= near_duplicate_threshold for index in sorted(candidates, reverse=True)[:250]
                              if min(len(key), len(kept_texts[index])) /
                                 max(len(key), len(kept_texts[index])) >= near_duplicate_threshold)
                if is_near:
                    counts['near_duplicate'] += 1
                    continue
                for gram in grams:
                    shingles_index[gram].add(len(kept_texts))
                kept_texts.append(key)
            seen.add(key)
            counts['kept'] += 1
            after_lengths += len(cleaned)
            after_vocab.update(tokenize_words(cleaned.casefold()))
            # No raw-text companion column is added: masked PII stays masked.
            yield {**row, text_column: cleaned}

    # Atomic save: a malformed row must not leave a half-written output.
    staged = None
    try:
        with source.open('r', encoding='utf-8-sig', newline='') as inp:
            if source.suffix.lower() == '.jsonl':
                def records():
                    for line_number, line in enumerate(inp, 1):
                        if not line.strip():
                            continue
                        item = json.loads(line)
                        if not isinstance(item, dict):
                            raise ValueError(f'JSONL line {line_number} must be an object.')
                        yield item
                iterator = records()
                fields = None
            else:
                delimiter = '\t' if source.suffix.lower() == '.tsv' else ','
                reader = csv.DictReader(inp, delimiter=delimiter)
                if not reader.fieldnames or text_column not in reader.fieldnames:
                    raise ValueError(f'Missing dataset text column: {text_column}')
                iterator, fields = reader, reader.fieldnames
            destination.parent.mkdir(parents=True, exist_ok=True)
            with tempfile.NamedTemporaryFile('w', encoding='utf-8', newline='',
                                             dir=destination.parent, prefix='.nlp-clean-',
                                             delete=False) as out:
                staged = Path(out.name)
                if fields is None:
                    for record in cleaned_rows(iterator):
                        out.write(json.dumps(record, ensure_ascii=False) + '\n')
                else:
                    writer = csv.DictWriter(out, fieldnames=fields, delimiter=delimiter)
                    writer.writeheader()
                    writer.writerows(cleaned_rows(iterator))
        os.replace(staged, destination)
        staged = None
    finally:
        if staged is not None:
            staged.unlink(missing_ok=True)
    n = counts['input']
    return {'input': n, 'kept': counts['kept'], 'removed': n - counts['kept'],
            'reasons': {name: counts[name] for name in ('empty', 'empty_after_cleaning', 'too_short',
                         'too_long', 'script_ratio', 'exact_duplicate', 'near_duplicate')},
            'mean_raw_length': round(before_lengths / n, 2) if n else 0,
            'mean_kept_length': round(after_lengths / counts['kept'], 2) if counts['kept'] else 0,
            'vocabulary_before': len(before_vocab), 'vocabulary_after': len(after_vocab),
            'text_column': text_column, 'min_persian_script_ratio': min_persian_ratio,
            'warning': 'Script ratio is not language detection; names and PII in other columns are not anonymized.'}
