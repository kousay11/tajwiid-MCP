# Source admission boundary

No source text is bundled. `editions.json` holds **metadata only** for the one source
(book A): identity, page count, printed/pdf page offset and the SHA-256 of the owner's PDF;
its licence status is `unknown`. Rule citations resolve
against it (edition known, page inside the edition, offset consistent).

Local page stores (`<edition>/pages.jsonl`, `pages_manifest.json`) are git-ignored; build
them from your own copy with `scripts/build_page_store.py`. Copy-protected PDFs are refused.
Do not place books, scans, extracted text, credentials, personal data or a copied Quran
corpus here.
