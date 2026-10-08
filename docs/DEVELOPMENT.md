# Development notes

## Environment

Use the project's `.venv` for both the application and tests. `setup_env.py` creates it with Python's `venv` module and does not enable system site packages. Dependencies are installed through that environment's interpreter.

`requirements.txt` includes `requirements-gui.txt`. The Qt dependencies are pinned to 6.8.3, the version used for the desktop checks. There are no additional test packages; the suite uses `unittest`.

To update Qt, change both the Essentials and shiboken versions together, install into a fresh environment, and run the full suite. Render the Persian example in a narrow window as well as a wide one. A successful import alone does not verify text direction or line wrapping. Keep dependency updates separate from unrelated feature work.

Do not commit `.venv`, caches, personal output reports, or editor state. Requirements files describe the environment; they are the files that belong in Git.

## Working on the analyzer

Keep text transformations in `core.py` and display changes in `gui.py`. A font or alignment change should never modify the string passed to `analyze`. Both the GUI and CLI use the same analysis function.

When fixing a counting bug, add a small input that shows it and a hand-checked expected result. The Persian regression file exists because quoted punctuation once added two false sentence boundaries. Keep that full-input regression as well as the smaller tests.

Use English for code comments, documentation, and commit messages. Comments should explain a decision or edge case rather than repeat the next line of code.

## Checks before a commit

```bash
python -m unittest discover -s tests -v
python -m compileall -q nlp_analyzer setup_env.py run_gui.py
python main.py examples/persian_regression.txt --persian --include-numbers

git diff --check
git diff
```

The Persian example should produce 19 sentences, 300 words, 183 unique words, and 132 singleton words. For GUI changes, also check typing, pasting, selection, Ctrl+C/Ctrl+V, undo, resizing, font size, and report export on the target desktop.

## Commit identity and messages

Set the repository identity once after cloning:

```bash
git config user.name "ARRahimipour"
git config user.email "arrahimipourdev@gmail.com"
```

Keep each commit focused on a change that can be reviewed on its own. Use a short message describing the effect, for example `Fix sentence boundaries around quoted punctuation`. Commit when the change is ready; keep the actual timestamp instead of constructing an artificial schedule.

Inspect both identities and dates with:

```bash
git log --format="%h | %an <%ae> | %cn <%ce> | %aI | %cI | %s"
```

A timestamp's UTC offset controls how it is displayed; it does not change when the work happened. Existing commit times are not rewritten by the environment setup.

## Release contents

The ZIP contains tracked source files plus `history.bundle`. It excludes `.venv` and `.git` internals. Create the bundle from a clean, committed repository:

```bash
git bundle create history.bundle --all
git bundle verify history.bundle
```

A user can recover the repository with `git clone history.bundle new-directory` and then create a local environment. The bundle is a release artifact, not a file to add back into the repository.
