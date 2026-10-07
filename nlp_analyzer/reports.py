"""Human-readable and machine-readable reports."""
import csv
import html
import io
import json
from .core import AnalysisResult


def render_report(result: AnalysisResult, format: str = 'text') -> str:
    if format == 'json':
        return json.dumps(result.to_dict(), ensure_ascii=False, indent=2) + '\n'
    if format == 'csv':
        buffer = io.StringIO(newline='')
        writer = csv.writer(buffer)
        writer.writerow(['word', 'count'])
        writer.writerows(result.frequencies.items())
        return buffer.getvalue()
    status = 'PASS' if result.target_met else 'CHECK'
    if format == 'text':
        lines = ['NLP TEXT ANALYZER', '=' * 40,
                 f'Sentences: {result.sentence_count}', f'Words: {result.word_count}',
                 f'Unique words (vocabulary): {result.unique_word_count}',
                 f'Words appearing once: {result.singleton_word_count}',
                 f'Target: {result.options["target_words"]} words [{status}]', '',
                 f'Top {len(result.top_words)} words (ties: first appearance):']
        lines += [f'{i:>2}. {row["word"]}  {row["count"]}' for i, row in enumerate(result.top_words, 1)]
        lines += ['\nCounting options: ' + json.dumps(result.options)]
        lines += ['WARNING: ' + warning for warning in result.warnings]
        lines += ['\nPASS checks the word-count target only; it is not a grading guarantee.']
        return '\n'.join(lines) + '\n'
    if format != 'html':
        raise ValueError(f'Unsupported report format: {format}')
    escape = html.escape
    cards = ''.join(f'<article><strong>{value}</strong><span>{label}</span></article>'
                    for label, value in [('Sentences', result.sentence_count), ('Words', result.word_count),
                                         ('Unique words', result.unique_word_count), ('Words appearing once', result.singleton_word_count)])
    maximum = result.top_words[0]['count'] if result.top_words else 1
    rows = ''.join(f'<tr><td>{i}</td><td dir="auto">{escape(row["word"])}</td>'
                   f'<td><div class="bar" style="width:{row["count"] / maximum * 100:.2f}%"></div></td>'
                   f'<td>{row["count"]}</td></tr>' for i, row in enumerate(result.top_words, 1))
    sentences = ''.join(f'<li dir="auto">{escape(sentence)}</li>' for sentence in result.sentences)
    warnings = ''.join(f'<p class="warning">{escape(warning)}</p>' for warning in result.warnings)
    vocabulary = ', '.join(result.frequencies)
    return f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>NLP Text Analysis Report</title><style>
*{{box-sizing:border-box}}body{{margin:0;background:#f2f5f9;color:#192637;font:16px/1.6 system-ui,sans-serif}}
main{{max-width:1000px;margin:48px auto;padding:32px}}header{{border-bottom:1px solid #d3dce6;padding-bottom:24px}}
.eyebrow{{color:#176b61;font-weight:700;letter-spacing:2px;font-size:12px}}h1{{font-size:40px;line-height:1.2;margin:10px 0}}
.sub{{color:#546579}}.cards{{display:grid;grid-template-columns:repeat(4,1fr);gap:16px;margin:28px 0}}
article,section{{background:white;border:1px solid #dee5ed;border-radius:14px;padding:24px}}article strong{{display:block;font-size:36px}}article span{{font-size:13px;color:#546579}}
section{{margin:18px 0}}h2{{font-size:21px;margin:0 0 18px}}table{{border-collapse:collapse;width:100%}}td,th{{padding:12px;text-align:left;border-bottom:1px solid #edf0f4}}td:nth-child(3){{width:40%}}
.bar{{height:10px;background:#198678;border-radius:8px}}.badge{{display:inline-block;background:#e2eee9;color:#225f50;padding:6px 12px;border-radius:8px;font-weight:600}}
.warning{{background:#fff0ce;padding:14px;border-radius:8px}}li{{padding:8px 0}}pre{{white-space:pre-wrap;overflow-wrap:anywhere}}footer{{font-size:12px;color:#546579;margin-top:24px}}
@media(max-width:650px){{main{{margin:0;padding:18px}}.cards{{grid-template-columns:repeat(2,1fr)}}h1{{font-size:30px}}td,th{{padding:6px}}}}
@media print{{body{{background:white}}main{{margin:0;padding:0}}section,article{{break-inside:avoid}}}}
</style></head><body><main><header><div class="eyebrow">NLP / SESSION 01</div><h1>Language, counted.</h1>
<p class="sub">Sentence tokenization · Word tokenization · Frequency analysis</p>
<span class="badge">{status} · {result.word_count} / {result.options['target_words']} words</span></header>
{warnings}<div class="cards">{cards}</div><section><h2>Top {len(result.top_words)} words</h2>
<table><thead><tr><th>Rank</th><th>Word</th><th>Relative frequency</th><th>Count</th></tr></thead><tbody>{rows}</tbody></table></section>
<section><h2>Sentence audit</h2><ol>{sentences}</ol></section><section><h2>Unique vocabulary</h2><p dir="auto">{escape(vocabulary)}</p></section>
<section><h2>Counting rules</h2><pre>{escape(json.dumps(result.options, indent=2))}</pre>
<p>Ties follow first appearance. Stopwords are retained. Sentence boundaries use documented heuristics.
PASS checks the word-count target only; it is not a grading guarantee.</p></section>
<footer>ARRahimipour · NLP Text Analyzer · Offline, reproducible analysis</footer></main></body></html>'''
