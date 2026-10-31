# Source admission boundary

No source text is bundled. `editions.json` holds **metadata only** for the three sources
(book A, book B, the Hannibal mushaf): identity, page count, printed/pdf page offset and the
SHA-256 of the owner's PDF; licence status is `unknown` for all. Rule citations resolve
against it (edition known, page inside the edition, offset consistent).

Local page stores (`<edition>/pages.jsonl`, `pages_manifest.json`) are git-ignored; build
them from your own copy with `scripts/build_page_store.py`. Copy-protected PDFs are refused.
Do not place books, scans, extracted text, credentials, personal data or a copied Quran
corpus here. See the [intake](../../docs/SOURCES_INTAKE.md).
