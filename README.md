# NLP Text Analyzer

**NLP text analysis · Python · Offline · Unicode-aware · No word-count limit**

Maintainer: **ARRahimipour** · **arrahimipourdev@gmail.com**

Analyze text of any length and report its sentence count, word count, unique vocabulary, and ten most frequent words. The project follows the first NLP pipeline in the provided `NLP_Session1_White.pdf`: raw text → sentence tokenization → word tokenization → frequency analysis.

## Quick start

Requires Python **3.10 or newer**. No pip packages, downloaded models, account, API key, or internet connection are required.

Extract the ZIP and open a terminal inside `nlp-text-analyzer`.

```bash
python main.py examples/english_300.txt
```

On systems where Python is named `python3`, use `python3` instead. On Windows, `py` may also be used.

### Desktop interface

```bash
python main.py --gui
```

Click **Load sample**, paste your own text, or use **Open text**. Metrics update automatically. **Export report** saves HTML, JSON, CSV, or plain text. Ctrl+O opens a file; Ctrl+S exports. A graphical desktop and a Python installation with Tk are required. If your Linux Python lacks Tk, install your distribution's Python Tk package (often `python3-tk`). The CLI works without Tk. Complex script rendering in Tk depends on the operating system; the HTML report uses browser text shaping and automatic text direction.

### Automatic text alignment

Version 1.2.0 aligns Persian/Arabic paragraphs to the right and English paragraphs to the left as you type, paste, or load a file. Unicode strong-character direction determines alignment; numbers and punctuation do not override it. Mixed paragraphs use the majority direction, with the first strong character breaking ties. The word column follows the overall text direction. HTML sentences and word cells use explicit directions and logical alignment.

Alignment only changes display tags: it does not reverse text, insert direction controls, move the cursor, or change analysis counts. Tk handles glyph shaping and bidirectional rendering according to the local OS/Tk build; right alignment is not a replacement for a full bidirectional text engine.

### Submit-ready sample

`examples/english_300.txt` is original text about the NLP pipeline. Its expected default result is:

| Metric | Result |
| --- | ---: |
| Sentences | 26 |
| Words | 300 |
| Unique vocabulary items | 207 |
| Words appearing exactly once | 166 |

| Rank | Word | Count |
| --- | --- | ---: |
| 1 | the | 19 |
| 2 | and | 9 |
| 3 | a | 7 |
| 4 | language | 6 |
| 5 | text | 6 |
| 6 | word | 6 |
| 7 | words | 5 |
| 8 | with | 3 |
| 9 | to | 3 |
| 10 | this | 3 |

Open `examples/english_300_report.html` in a browser for a formatted report with the full sentence audit and vocabulary. The matching JSON report contains every token, sentence, frequency, and counting option.

**There is no 300-word restriction, target, or PASS/CHECK status. The included 300-word text is only a reproducible example.**

## Command-line examples

```bash
# Analyze any UTF-8 text file.
python main.py my_text.txt

# Normalize Arabic letter variants in Persian input.
python main.py examples/persian.txt --persian

# Analyze a literal string.
python main.py --text "Hello world! Hello NLP."

# Save an offline report; output directories are created automatically.
python main.py examples/english_300.txt --format html --output outputs/report.html
python main.py examples/english_300.txt --format json --output outputs/report.json
python main.py examples/english_300.txt --format csv --output outputs/vocabulary.csv

# Equivalent module entry point.
python -m nlp_analyzer examples/english_300.txt
```

Omit both the filename and `--text` to read piped standard input. Use UTF-8 for files and terminal streams. Warnings are sent to stderr so JSON stdout remains parseable.

| Option | Default | Meaning |
| --- | --- | --- |
| `--top N` | 10 | Maximum number of frequent words |
| `--case-sensitive` | Off | Keep uppercase and lowercase variants separate |
| `--persian` | Off | Convert Arabic yeh/alef maksura/kaf to Persian forms and remove tatweel |
| `--include-numbers` | Off | Include purely numeric tokens |
| `--format` | text | Select text, json, csv, or html |
| `--output PATH` | stdout | Write a UTF-8 report |
| `--gui` | Off | Launch the desktop interface |

Exit codes: **0** for successful analysis at any word count, **2** for invalid arguments, unreadable files, invalid UTF-8, or unavailable GUI. CLI options apply to CLI analysis; the GUI uses its own controls and shows the top ten words. The old `--strict` and `--target` options have been removed.

## Counting policy

The instructor does not specify every tokenization convention. This implementation makes its choices explicit and reproducible:

- Unicode NFC normalization merges canonically equivalent character sequences. Curly apostrophes become straight apostrophes. A leading BOM is ignored.
- A token consists of Unicode letters/numbers and attached combining marks. It must contain a letter unless `--include-numbers` is enabled. Internal apostrophes, ZWNJ, and ZWJ remain inside tokens. Punctuation, symbols, emoji, underscores, and hyphens separate tokens. Thus `don't` and `می‌روم` are each one token, while `well-known` is two. Decimal punctuation separates numeric tokens when numbers are included.
- Case folding is applied to tokens by default: `Hello` and `HELLO` share one entry. Unicode case folding is language-independent, not a locale-specific rule for Turkish or other languages.
- Unique words means **distinct normalized vocabulary items**, not words occurring once. The report includes both measurements separately.
- No stopword removal, stemming, or lemmatization is performed. These operations would change the homework's raw frequency counts.
- Frequency ties follow first appearance in the source text. If fewer than ten distinct tokens exist, every available item is returned.
- Quoted punctuation-only examples such as `«؟»` and `"!"` do not end sentences. Actual quoted sentences still use the normal boundary rules.
- Sentences end at common Western, Persian/Arabic, CJK, Indic, Armenian, and Ethiopic terminal punctuation. Repeated endings and trailing closing quotes remain together. Decimal points, common English titles, and single-letter initials receive basic protection. Blank lines also separate sentences; single line wraps do not. A final unpunctuated fragment counts as a sentence. Punctuation-only fragments do not count.
- Optional Persian normalization does not delete Arabic vowel marks or infer missing word spaces. It does not merge `می روم`, `میروم`, and `می‌روم` into one spelling.

### Language coverage and limitations

The analyzer accepts Unicode text in any language. Tests include Persian, Arabic, English, French, German, Spanish, Russian, Greek, Hindi, Bengali, Turkish, Hebrew, and Korean. These examples verify deterministic token handling, not full linguistic accuracy in each language.

**Unicode support is not universal word segmentation.** Chinese, Japanese, Thai, Lao, Khmer, and Myanmar text can contain lexical words without spaces. This implementation preserves uninterrupted character runs and emits a warning for the detected script ranges. It does not pretend those runs are dictionary words. Accurate segmentation requires an appropriate language-specific tokenizer and a defined evaluation corpus. Mixed-script runs also remain single tokens. Sentence splitting is heuristic: uncommon abbreviations, initials at sentence ends, ellipses within a sentence, unpunctuated writing, and language-specific conventions can require manual review. There is no universal hidden-test or “all languages” PASS claim.

The lecture mentions Python + NLTK as the initial pipeline. This project implements the same beginner pipeline directly using Python's standard library so it runs offline without NLTK/Punkt downloads. If the instructor explicitly requires NLTK rather than Python, that is an additional requirement and would need an adapter and its resources.

## API

```python
from nlp_analyzer import AnalysisOptions, analyze

result = analyze("سلام دنیا! سلام NLP.", AnalysisOptions(persian_normalization=True))
print(result.sentence_count)
print(result.word_count)
print(result.unique_word_count)
print(result.top_words)
```

`result.to_dict()` returns a JSON-compatible result. JSON includes the entire analysis. CSV includes the full vocabulary frequency table, not sentence totals. HTML and text include the headline metrics; HTML also includes a sentence audit and vocabulary list.

## Tests and verification

```bash
python -m unittest discover -s tests -v
```

The automated suite contains **54 tests**, including multilingual subcases, a hand-counted example, the exact 300-word sample, invariants, CLI subprocess execution, arbitrary input lengths, author details, exports, UTF-8 failures, input-overwrite protection, and HTML escaping. See `docs/test-results.txt` for the captured run and `docs/VERIFICATION.md` for tested scope and limitations. No third-party test runner is required.

## Project layout

```text
nlp-text-analyzer/
  main.py                     Convenience entry point
  nlp_analyzer/
    core.py                   Normalization, tokenization, counting
    cli.py                    Argument parsing and file handling
    gui.py                    Tk desktop interface
    reports.py                Text, JSON, CSV, HTML rendering
  examples/                   300-word English sample and Persian example
  tests/                      Automated regression and integration tests
  docs/                       Design explanation and verification record
  history.bundle              Portable Git history, included in release ZIP
```

## Author

Alireza Rahimipour Anaraki

Ph.D. Candidate in Computer Engineering – Artificial Intelligence

Department of Computer Engineering, NT.B, Islamic Azad University, Tehran, Iran

info@arrahimipour.com

arrahimipour.com

The author block appears below the desktop workspace and in HTML and plain-text reports. Desktop and HTML email/website links are clickable.

## Git history and identity

All included commits use this author and committer identity:

```text
ARRahimipour <arrahimipourdev@gmail.com>
```

The release includes `history.bundle`, a portable Git repository containing the actual development commits. Restore the history from the extracted directory:

```bash
git clone history.bundle ../nlp-text-analyzer-repo
cd ../nlp-text-analyzer-repo
git config user.name "ARRahimipour"
git config user.email "arrahimipourdev@gmail.com"
git log --format="%h %an <%ae> | %s"
```

Git's local identity configuration is not transferred by cloning, so the two `git config` commands set it for your future commits as well. No remote repository was created or pushed. If you later push to your GitHub account, contribution attribution also depends on that email being associated with your account. The included commits are not cryptographically signed.
