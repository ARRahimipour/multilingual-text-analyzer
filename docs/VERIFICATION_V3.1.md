# Verification — rebuilt v3.1.1

Verified on 2026-11-16, Linux with a fresh project-local Python environment and the pinned requirements.

- **131 tests passed**, no skips; complete log in test-results-v3.1.txt.
- Page 110 exact textbook fixture checked against hand calculations, including zero common-term weight and repeated-term weighting.
- Smoothed TF-IDF independently compared with scikit-learn. CSR round-trip, zero vectors, feature controls and large-preview bounds verified.
- Retrieval checked for ranking, unknown queries and Persian letter normalization without query fitting.
- Classifier comparison checked for seeded repeatability, held-out vocabulary isolation, normalized leakage rejection and confusion-matrix counts.
- Stopword protection, custom/statistical removal, four-stage counts, all three English stemmers, actual Hazm pipeline and Random Forest experiment exercised.
- Real offscreen Qt worker tests include the new search activity, option parsing and paragraph direction. Updated Qt window rendered and inspected.
- run_expanded_demo.py completed all new examples. pip check and git diff --check passed.

Optional English NLTK full-pipeline/WordNet execution requires locally installed punkt_tab, stopwords and wordnet resources. They are not bundled and were not executed with downloaded corpora in this rebuild; the actionable missing-resource error is tested. No network security override is enabled.

Classification data are tiny classroom demonstrations, not a benchmark. No production accuracy, universal language coverage or contextual disambiguation is claimed. Physical Windows/macOS displays were not tested. Environments and caches are excluded.

The GitHub connection reported read-only permission. Changes are supplied as local commits, an apply-ready patch and a complete bundle; no push or PR is claimed. Original baseline history is preserved. Previous release hashes were not fabricated after the temporary files expired.
