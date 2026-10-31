# Notice

The Quran text served by wirdi-mcp comes from these public sources, bundled here unchanged and
pinned by SHA-256 in `../source_manifest.json`:

- **Qur'anpedia.net**: KFGQPC Qaloun (riwaya of Qaloun from Nafi') and QPC Hafs text. Credit to
  Qur'anpedia.net; the dump version is the revision below.
- **risan/quran-json** (https://github.com/risan/quran-json), revision
  `6523a9ad3b73bb7e8cb3a9cdf0ea774b8bab3123`, CC BY-SA 4.0: the compilation of the dump. Its licence
  text is in `data/raw/quran-json/repo/LICENSE.txt`.
- **Page map** (`data/generated/qaloun_pagination_verified.json`): 559 printed pages of the King
  Fahd Complex mushaf, Qaloun from Nafi' (1427 H). The file's own metadata says the verse-end markers
  and surah banners were detected on the page images by the Wirdi AI project and checked against the
  verse counts, the printed index and a visual audit. See `docs/qaloun-pagination-validation.md`.
- **Mapping resolver** (`backend/app/tadabbur/`): code of the Wirdi AI project that maps Qaloun
  ayah numbers to the Kufian (Hafs) numbering. See `docs/reader-corrections-report.md` for its limits.

The Tajwid rules of this repository are paraphrases written by an automated drafter. They are
unreviewed and carry the status `candidate` at most. The Quran text is never altered. Terms: see
`LICENSE-DATA.md`.
