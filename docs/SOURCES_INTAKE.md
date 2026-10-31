# Source intake

Three PDFs were placed in `docs/` by the project owner. They are **never committed**
(ignored by `.gitignore`) and **never modified**. Licence status of all three is
`unknown`: nothing here is cleared for redistribution. `scripts/inventory_pdfs.py`
reproduces the facts below; its metadata-only output is `knowledge/sources/inventory.json`.

| Id | Title | Author / publisher | Edition | Path claimed | Pages | SHA-256 |
| --- | --- | --- | --- | --- | --- | --- |
| `book-a` | أحكام رواية قالون عن نافع المدني، شرح مبسط مع الأمثلة | جنوى توفيق (PDF metadata: "NAJWA"), Benghazi, Libya | 1431 H / 2010 (Word file dated 2017) | Qaloun from Nafi'. Abu Nashit appears only as a pupil of Qaloun, not as the path | 51 | `cc504928a9e07f255e9cfb0dd552866f6fe63094d79f5311b96b68dd39c64ad6` |
| `book-b` | مذكرة في أحكام الترتيل، برواية قالون عن نافع من طريق أبي نشيط | collected by عبد الكريم مقيدش (calligraphic cover, reading to confirm), دار المحسن, Algeria | 1st ed. 1431 H / 2010, ISBN 978-9947-881-44-6 | **Abu Nashit** (title) | 156 | `db3ef24243b6f3c87ad9e89935d29f0a8981c984d893a8f9d480fe01ca1075cd` |
| `mushaf-hannibal` | مصحف قالون، الطبعة التونسية (حنبعل, Tunis), coloured | Hannibal for printing, publishing and distribution, Tunis; scan by volunteers of the Fatima Az-Zahra mosque, Sahloul (Sousse) | undated scan, Canon 2014 | **Abu Nashit** (page م1), Kufian count 6236 | 627 | `b4be5ddedc2e9098dfbe5164e73d7a3858ad7e31d37cf0fe8bb1d2d6eafb76a2` |

## Technical shape

- **book-a:** Word-generated, real text layer (6 sampled pages 324 to 1413 characters).
  Ligature output is inverted: lam-alef comes out as alef-lam and the word الله as
  `هللا`, with bidi marks. Any extracted text is raw, unreviewed material.
- **book-b:** 1-bit CCITT scan (JPEG cover), no text layer. The PDF is
  **encrypted with `copy:no`**. Protection is respected: text extraction is not
  attempted by the inventory script, and only image renders (`print:yes`) may be
  consulted. There is no OCR in this project.
- **mushaf-hannibal:** 627 JPEG pages (300 ppi RGB). The embedded text layer is a
  garbage OCR (Latin noise) and is unusable. Layout: pdf 1 cover, pdf 2 credit,
  pdf 3 to 605 Quran (printed page = pdf page − 1, printed 2 to 604), pdf 606 to 626
  appendix printed م1 to م21, pdf 627 back cover.

## Colour legend (mushaf page م11, pdf 616)

| No. | Colour | Declared meaning |
| --- | --- | --- |
| 1 | grey | everything not pronounced |
| 2 | red | ghunna and qalqala rulings |
| 3 | orange | miscellaneous rules and rulings |

The legend is coarse: red covers at least two distinct rule families, orange is
"miscellaneous". A colour never identifies a precise rule on its own.

## Numbering and pagination

- The mushaf follows Kufian numbering (6236). `qalun.json` is a 6,214-verse corpus
  whose `number_in_hafs` links give the verse-level bridge (Kahf 18:45 ↔ mushaf 46).
- Mushaf pagination (604 + appendix) differs from the application's verified
  559-page map. Both numbers are kept in data; alignment is by verse, never by page.

## Path attestation

Abu Nashit is attested by book B and the mushaf, not by the corpus. This is a
documented hypothesis only; the corpus keeps `tariq=unspecified`.
