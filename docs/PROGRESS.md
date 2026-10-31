# Progress (autonomous Tajwid mission)

Branch: `feat/tajwid-knowledge`. Never push. Resume by reading this file first.

## Current milestone
J7 (final verification and documentation)

## Done
- J0 hygiene: `.gitignore` extended before any commit (PDFs, page renders, derived
  mushaf data); baseline commit `6344660`; manifest drift admitted after the full
  real-source suite passed (46 passed), commit `0bebd57`; no PDF tracked.
  Baseline before J0 changes: 31 passed, 15 skipped, ruff clean.

- J1 inventory and models: `scripts/inventory_pdfs.py`, `docs/SOURCES_INTAKE.md`, wider
  annotation statuses, page refs, image provenance, observed colour. Commit `J1`.
- J2 rule registry and page store: 14 rule records (`knowledge/rules`), hash-pinned
  manifest, `RuleRegistry`, `PageStore` (local, git-ignored Book A store built; Book B is
  copy-protected and is not extracted), tamper/isolation tests.
- J3 tokenizer, 14 detectors, `TajwidEngine`/`TajwidService`, 11 MCP tools, frequency
  audit (`scripts/audit_rules.py`): all 6,214 single-ayah selections run in both modes with
  no exception, no rule at zero, idhar mutlaq hits only the four lexemes of book A p.6.

- J4 mushaf pilot on 10 pages: **NO-GO** (see `docs/PILOT_REPORT.md`); J5 skipped.
  Image libraries installed in the project `.venv` only; optional extra `mushaf` added.

- J6 performance and reliability: one corpus/pagination/manifest read per request,
  paging (default 100, max 500), size limits, typed errors with no path leakage,
  `docs/PERF.md`: page call p50 84 ms, cold start 0.56 s.

## Next action
J4: install numpy/opencv/scikit-image/pillow in `.venv`, render 10 sample mushaf pages
losslessly, detect coloured blobs, attach to letters, measure, write `docs/PILOT_REPORT.md`
(GO only if >= 95% red blobs on the right letter and >= 90% agree with the detector).

## Resume commands
```bash
cd /home/najjar/Documents/Me/wirdi-mcp
git status --short && git log --oneline | head
.venv/bin/python -m pytest -q
WIRDI_TEST_SOURCE_ROOT=/home/najjar/Documents/Me/wirdi-Ai .venv/bin/python -m pytest -q
.venv/bin/ruff check . && .venv/bin/ruff format --check .
git ls-files | grep -i -E '\.(pdf|png|jpe?g)$'   # must print nothing
```
