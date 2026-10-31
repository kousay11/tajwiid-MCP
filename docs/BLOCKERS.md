# Blockers

Each entry: milestone, what could not be done, what was done instead.

1. **Scholarly validation (needs you).** No named reviewer exists, so no annotation can be
   verified and explanations cannot exist. Done instead: statuses stop at `candidate`, the
   validation store is empty and ready, and [REVIEW_SAMPLE](REVIEW_SAMPLE.md) was prepared.
2. **J4/J5 coloured mushaf: NO-GO.** Blob to letter mapping is not computable from a raster
   without glyph recognition; the legend colours do not separate on the pages; recall and
   ornament masking were inadequate ([PILOT_REPORT](PILOT_REPORT.md)). J5 was skipped by the
   gate, not by a failure. The MCP stands on books and detectors.
3. **J2 book B text.** The PDF is a copy-protected scan; protection is respected and OCR was not
   used, so there is no local page store for it (`get_source_page` answers `DATA_UNAVAILABLE`
   for `book-b-2010`). Its rule citations come from reading page images by eye.
4. **J2 book A text quality.** The extractor inverts lam-alef; the page store keeps the raw text
   and `search_source_pages` tolerates it. Not cleaned.
5. **J0 Wirdi AI has no git metadata.** The two drifted files could not be diffed; the update
   was admitted functionally (full conformance). Note it if the application's code changes again.
6. **Uncertain source metadata.** The author name on book B's calligraphic cover is a reading
   to confirm; book A's author is the PDF's author field plus the book's own colophon.
