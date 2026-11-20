# Persian NLP Test Suite — Professor's Experiment Notes

The application ships with **eight Persian research inputs** and **one English baseline**, all reproducible UTF-8 files. Each input is intentionally written to expose a different processing decision in the six-stage course pipeline, rather than to imply that one cleaning policy suits every task.

## Choose a case in the desktop

Open **06 / Six-stage pipeline**, select a **Test case**, and click **Load case**. The UI chooses the sample language and suggested cleaning profile. Run **all six stages**, then click stages 01–06 in the multirow stage navigator. Use the audit tab to describe which transformations were actually made.

| Case | File | What to inspect | Suggested task profile |
|---|---|---|---|
| 01 Mixed web & Unicode | `01_web_mixed_fa.txt` | HTML/script removal, URLs, email, emojis, hashtags, elongated characters, mixed digits and ZWNJ | General |
| 02 Persian spacing stress | `02_zwnj_unicode_fa.txt` | Arabic/Persian yeh and kaf, ZWNJ, NBSP, malformed separated prefixes and suffixes, diacritics and emoji joiners | General; compare Hazm with Conservative |
| 03 Sentiment & negation | `03_sentiment_negation_fa.txt` | Positive/negative terms, negation, sarcasm, emotive punctuation and emoji | Sentiment; preserve negation |
| 04 Inflections & morphology | `04_morphology_fa.txt` | Nouns, plural forms, verb tenses and Stem-versus-Lemma mapping | General; compare Stem versus Lemma |
| 05 Frequency / Zipf sketch | `05_frequency_zipf_fa.txt` | Total vs unique tokens, top-ten frequencies, stopword impact, type-token ratio | Topic; compare Stage 04 and Stage 05 |
| 06 PDF/OCR noisy source | `06_pdf_ocr_noisy_fa.txt` | Page numbers, broken lines, Arabic presentation forms, invisible controls and extra line breaks | General; manual review required |
| 07 Entities & privacy | `07_entities_privacy_fa.txt` | Synthetic phone numbers, dates, technical names, emails, links and hashtags | NER; compare with General |
| 08 Informal mixed-language | `08_colloquial_mixed_fa.txt` | Persian colloquial inflections, English technical vocabulary and punctuation | General; note unhandled ambiguities |
| 09 English baseline | `09_english_benchmark.txt` | Tokenization and NLTK Porter/WordNet morphology | English / General |

## Five experiments to show the instructor

**Experiment A — Unicode and spacing.** Load Case 02, select **Conservative** spacing, choose Regex tokenization and set morphology to None if Hazm is not installed. Compare stages 01 and 03, then enable **Show spaces & ZWNJ**. Examine whether a second normalization pass is unchanged. Do not assume the program can infer every ambiguous boundary.

**Experiment B — Sentiment information loss.** Load Case 03 and keep the **Sentiment** profile. Compare emoji and punctuation with the **Topic** profile, and test with **Keep negation** enabled and disabled. Explain why an apparently aggressive cleaning policy might make polarity classification worse.

**Experiment C — Morphology.** Load Case 04 with Hazm installed. Run once with Stem and again with Lemma. Compare token-to-result mappings in the Stage 06 audit and discuss whether the output is a plausible root, a lemma, or unchanged. Never apply both in sequence.

**Experiment D — Frequency distribution.** Load Case 05 and run with stopword filtering enabled and disabled. Compare Stage 04/Stage 05 token counts, type-token ratio and top-ten terms. This is a *small illustration* of frequency imbalance, not a statistically sufficient proof of Zipf's law.

**Experiment E — Noise and entity preservation.** Compare Case 01 with Case 07 and change the cleaning profile from General to NER. Observe which URLs, email addresses, identifiers and mentions are retained. The synthetic contact data are for demonstrations; do not interpret the program as a full privacy-anonymization system.

## What the professor should see in each report

- Exact raw input and UTF-8 lengths.
- Cleaning operations, including changed/unchanged flags and the sentence-boundary snapshot.
- Normalization audit and Unicode spacing counts, with the idempotence check.
- Sentence tokens, lexical tokens, unique types and top-ten frequencies.
- An explicit stopword-removal list and protected negations.
- English-labeled Stage 06 morphology and complete token-to-output mappings.

Save **Export JSON** to preserve a reproducible experiment record. Any result that differs from expectations should be reported as a meaningful limitation, not silently corrected in the documentation.

## Verification without model downloads

```bash
python -m unittest tests.test_persian_demo_suite tests.test_spacing_studio -v
```

For an offline smoke run with only standard-library tokenizer options, set `tokenizer="regex"`, `normalization={"spacing":"conservative"}`, `morph_method="none"` and `remove_stopwords=False` in the Python API. This still exercises all six output stages, while marking skipped optional operations explicitly.
