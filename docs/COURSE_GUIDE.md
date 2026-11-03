# Four-handout course guide

## 1. What NLP does

Natural Language Processing connects language with computation. NLU is concerned with interpreting language, such as identifying an intent or classifying a document. NLG produces language, such as a summary or response. Counting words is useful descriptive analysis; it is not semantic understanding.

Ambiguity can be lexical (a word has multiple meanings), syntactic (more than one parse), or contextual (a pronoun or implied meaning depends on the conversation). Irony and world knowledge can reverse the apparent meaning of a sentence. This project does not claim to resolve those problems by cleaning text.

The historical progression includes explicit rules, corpus statistics, classical machine learning, dense word embeddings, recurrent networks including LSTMs, and attention-based Transformers. BERT is commonly used as an encoder; GPT-style systems generate autoregressively. RAG retrieves external evidence and supplies it to a generator. These are architectural concepts in the roadmap; this application does not train an LLM or provide RAG.

**Try:** run the original 300-word example in the main window, then replace it with a longer text. Inspect sentence count, tokens, types, singletons and top frequencies. A token is an occurrence; a type is a distinct vocabulary entry. Case sensitivity changes type counts. Ties in the top-frequency table follow first occurrence.

## 2. Cleaning is task-dependent

Cleaning removes unwanted material: HTML markup, scripts, tracking links or unwanted controls. It should not blindly delete useful information. Emoji may be useful for sentiment, punctuation for sentence boundaries, and names/numbers for NER. Transformer tokenizers may expect punctuation and casing. Presets are explicit educational policies, not a guarantee of optimal downstream accuracy.

The main window offers a source view and a separate cleaned preview. Dataset cleaning additionally handles empty/short/long rows, duplicate content and script-ratio filtering. A Persian/Arabic script ratio is a character-level heuristic, not a language classifier. Pattern-based email, phone and ID masking can miss sensitive material and can mask innocent numeric strings.

**Try:** enter HTML, a URL, an email, a hashtag, an emoji and a Persian sentence. Compare `general`, `sentiment` and `ner` presets and inspect the changes before exporting.

## 3. Unicode and normalization

Bytes, code points and visible graphemes are different units. An accented letter can be one precomposed code point or a base plus combining mark. A family emoji contains several code points joined into one grapheme cluster. Lab → Unicode shows all three counts and individual Unicode names.

NFC composes canonical equivalents; NFD decomposes them. NFKC/NFKD also apply compatibility mappings, which can erase distinctions. Unicode normalization alone does not unify Arabic yeh/kaf with Persian forms. Persian letters, digits and Arabic marks are separate controls. Optional Arabic letter collapsing can lose distinctions and therefore starts disabled.

Conservative spacing repairs already separated prefixes/suffixes, repeated half-spaces and punctuation spacing. It does not insert a half-space into every word beginning with `می`: that would corrupt words such as `میز`. Hazm mode runs the library's broader Persian normalization, which may also change digits and other forms. Its effects appear in a named stage.

Repeated Latin letters of length three or more reduce to two, preserving ordinary double letters such as `book` and `coffee`; repeated non-Latin letters reduce to one when enabled. This remains a heuristic and can alter intentional emphasis. Contraction expansion avoids ambiguous `'s` and `'d`. Colloquial, spelling and Finglish conversions use a small explicit dictionary; extend it through the CLI rather than assuming contextual understanding.

Placeholder replacement runs URL → email → mention → number. Existing placeholders retain uppercase labels under case folding. The idempotence audit applies the exact pipeline twice and compares outputs. A custom dictionary such as `a → b`, `b → c` can fail that test; the application reports the failure instead of hiding it.

**Try:** Load sample → normalize. Change Unicode form, spacing and digit settings, then inspect Details for before/after text. Export JSON to retain options and every stage.

## 4. Tokenization and model inputs

Whitespace splitting is simple but attaches punctuation. Regex and WordPunct separate punctuation differently. Character tokenization is not grapheme tokenization. The Unicode word tokenizer preserves useful word structure, while Hazm adds Persian-specific behavior. Compare their output before choosing an approach.

BPE learns frequent pair merges. WordPiece learns a subword vocabulary with continuation pieces. Unigram learns a probabilistic inventory and selects segmentations. SentencePiece provides a training/encoding framework; the included SentencePiece activity uses its Unigram trainer. All four activities here train on the supplied corpus locally. BPE uses a byte-level alphabet, which explains byte-looking token strings and its ability to encode unseen characters. WordPiece/Unigram can yield unknown IDs when the training vocabulary lacks characters.

Use a separate query to observe generalization. A word vocabulary maps unseen query words to UNK and reports their proportion. Subword methods reduce many whole-word OOV cases but do not automatically provide semantic knowledge. Requested vocabulary size is a target subject to alphabet requirements and available training data.

Save Hugging Face tokenizers as `.json` and SentencePiece as `.model`. Load the same file to preserve the exact token IDs. Reset model switches back to training on the current corpus. No cloud model, API key or pretrained BERT/GPT download is used.

Chunking packs complete sentences within a chosen budget. Overlong sentences fall back to whitespace word boundaries. If a single indivisible word exceeds a subword budget, increase the limit; the application raises an error instead of discarding text. Overlap keeps whole trailing units up to the requested allowance and can be smaller than requested. A typical 10–20% overlap is an experiment, not a universally optimal setting. The report records actual chunks, unit ranges and counts. Without a loaded model or enabled subword training, budgets use Unicode word tokens.

Batch mode pads or truncates encoded documents to a fixed length. Real tokens have attention mask 1, padding has 0. Both left and right modes are available; removed counts are explicit. No CLS/SEP/BOS/EOS tokens are automatically added. Real model integration must reserve that model's required special-token budget and use its tokenizer.

**Try:** load the sample corpus, train each subword method, then compare the same query. Save BPE, load it and run batch/chunk. Inspect Matrices and Full JSON. Tokenizer timing is one warm run; Python allocation peaks exclude native memory and are not a rigorous benchmark.

## 5. Morphology and numerical features

Stopword removal is optional and task-dependent: removing negation can damage sentiment. Stemming removes affixes heuristically and can produce nonwords. Lemmatization uses lexical information but is not automatically contextual disambiguation. Persian uses Hazm. English uses Porter stemming or WordNet lemmatization with an explicit POS setting. Download WordNet once with `python setup_resources.py`; the app gives a clear message when it is absent.

For a corpus of N documents, the feature lab uses raw counts for TF and smoothed `IDF = ln((1 + N)/(1 + document_frequency)) + 1`, followed by row-wise L2 normalization. Cosine similarity is the dot product of the normalized rows. An all-zero document remains a zero vector. N-grams are contiguous sequences of n word tokens. Type/token ratio is distinct words divided by total word occurrences. Zipf rows show measured ranks and frequencies; a small sample does not establish a power law.

**Hand calculation:** for `cat cat dog` and `dog bird`, vocabulary order is `bird, cat, dog`; BoW is `[0,2,1]` and `[1,0,1]`. The rare terms have IDF `ln(3/2)+1`, while `dog` has IDF 1. The test suite checks these values and independently compares the complete TF-IDF result against scikit-learn.

## 6. Classification and honest evaluation

The classifier fits TF-IDF and Multinomial Naive Bayes only on explicit labeled training records. A query receives a label and class probabilities; those probabilities are not calibrated guarantees. Load a separate labeled holdout to obtain accuracy, precision/recall/F1 and a confusion matrix. Normalized exact duplicates between train and holdout are rejected. Near duplicates and related-source leakage still need careful dataset design.

The included tiny positive/negative dataset is original demonstration material, not a benchmark. Its scores do not establish production performance. No training-set accuracy is presented as test accuracy. Preprocessing and feature choices should be selected on appropriate validation data, followed by evaluation on an untouched test set.

## Sources for the libraries used

- Supplied course material: `Binder1.pdf` (the four handouts).
- Hazm: https://github.com/roshan-research/hazm
- NLTK tokenizers: https://www.nltk.org/api/nltk.tokenize.html
- Hugging Face Tokenizers: https://huggingface.co/docs/tokenizers/
- SentencePiece: https://github.com/google/sentencepiece
- scikit-learn text features: https://scikit-learn.org/stable/modules/feature_extraction.html#text-feature-extraction
