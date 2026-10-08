# Changelog

## 1.3.1

- Added a project-local virtual environment setup helper.
- Added a launcher that always uses the project's `.venv` interpreter.
- Pinned the Qt runtime and binding package to the tested 6.8.3 release.
- Reworked the README around installation, normal use, counting examples, and troubleshooting.
- Added development notes for dependency changes, tests, and Git identity.
- Re-ran all 60 tests inside the isolated environment.

## Earlier changes

The Git history records the initial analyzer, CLI/report exports, desktop interface, author details, removal of the 300-word target, and subsequent text-display fixes. The important behavior fixes were quoted-punctuation sentence boundaries and the move from Tk to Qt for Persian/Arabic layout. See `git log` for the original commit dates and messages.
