# Progress (autonomous Tajwid mission)

Branch: `feat/tajwid-knowledge`. Never push. Resume by reading this file first.

## Current milestone
J1 (inventory and data model)

## Done
- J0 hygiene: `.gitignore` extended before any commit (PDFs, page renders, derived
  mushaf data); baseline commit `6344660`; manifest drift admitted after the full
  real-source suite passed (46 passed), commit `0bebd57`; no PDF tracked.
  Baseline before J0 changes: 31 passed, 15 skipped, ruff clean.

## Next action
J1: `scripts/inventory_pdfs.py`, `docs/SOURCES_INTAKE.md`, then model extensions.

## Resume commands
```bash
cd /home/najjar/Documents/Me/wirdi-mcp
git status --short && git log --oneline | head
.venv/bin/python -m pytest -q
WIRDI_TEST_SOURCE_ROOT=/home/najjar/Documents/Me/wirdi-Ai .venv/bin/python -m pytest -q
.venv/bin/ruff check . && .venv/bin/ruff format --check .
git ls-files | grep -i -E '\.(pdf|png|jpe?g)$'   # must print nothing
```
