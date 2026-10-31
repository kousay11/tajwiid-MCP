# Licence of the bundled data

This folder holds data and two small source files that are **not** covered by the MIT licence of
the rest of the repository. Each part keeps its own terms.

| Part | Files | Terms |
| --- | --- | --- |
| Quran text and the compilation that carries it | `data/raw/quran-json/repo/data/quranpedia/qalun.json`, `qpc-hafs.json` | Text from Qur'anpedia.net (KFGQPC Qaloun and QPC Hafs), in the compilation of `risan/quran-json` (revision `6523a9ad3b73bb7e8cb3a9cdf0ea774b8bab3123`), licensed **CC BY-SA 4.0** (`data/raw/quran-json/repo/LICENSE.txt`). The Qur'anpedia.net data licence asks for credit to Qur'anpedia.net and the dump version when the data is republished: both are given here. The files are unchanged. |
| Page map of the 559-page Qaloun mushaf | `data/generated/qaloun_pagination_verified.json` | Derived by the Wirdi AI project from the page images of the King Fahd Complex mushaf (Qaloun, 1427 H), as the file's own metadata states. Offered here under CC BY-SA 4.0 together with the text it indexes. |
| Mapping resolver and Arabic normaliser | `backend/app/tadabbur/mapping.py`, `arabic.py` | Code of the Wirdi AI project, owned by the author of this repository, offered under the MIT licence. |
| Trimmed schemas, public notes, audit data | `backend/app/schemas.py`, `docs/*.md`, `docs/reader-correction-mapping-audit.json` | Written or extracted for this repository by its author; MIT licence. |

ShareAlike (CC BY-SA 4.0) applies to the Quran text and page map and to adaptations of them. It
does not reach the code of this repository, which only reads these files.

See `NOTICE.md` for the credits.
