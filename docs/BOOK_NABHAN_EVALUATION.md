# Evaluation of a second Qaloun book

Local file `docs/Quraan01260.pdf` (git-ignored, never committed). It is used to **verify** the rules
and to **add what Book A lacks**, not as an independent proof. See "What was done" at the end.

## Identity

| | |
| --- | --- |
| Title | الثمر اليانع في أصول رواية قالون عن نافع |
| Author | Muhammad Nabhan Misri (Umm al-Qura University), from the book's own pages 1 and 5 |
| File | 214 pages, not encrypted, text layer present, SHA-256 `373d7271…6560` |
| Printed page | equals the PDF page (offset 0) |
| Registered as | edition `thamar-yani-2003` in `knowledge/sources/editions.json`; local page store built, git-ignored |
| Structure | usul and tajwid pp.8-110; farsh tables Hafs against Qaloun, ayah by ayah, pp.111-198; indexes pp.199-214 |

**Text quality.** The text layer uses Arabic presentation forms with detached diacritics. Search works
after NFKC (already done by `normalize_arabic`), but numbers and marks in tables must be read on the
page images. Every claim below marked *(image)* was read on the rendered page.

## Tariq

The book follows the Shatibiyya (pp.4, 7) and heads its farsh part with
« رواية قالون عن نافع – طريق الشاطبية عن أبي نشيط » (p.111). It is the only source in this project
that names Abu Nashit. Book A names none.

## Book A is a digest of this book

The wording and the examples of Book A are the same, sometimes word for word:

| Subject | New book | Book A |
| --- | --- | --- |
| Two hamzas in two words | pp.45-47 (جاء أحد، جاء أمرنا، أولياء أولئك) | pp.27-29 |
| Sakin before hamzat al-wasl | p.51 (أنِ امشوا، قالت اخرج، أو انقص…) | p.31 |
| Ranks of the isti'la letters | p.65 (للطائفين، طبع، ضرب، دخلت) | p.32 |
| Alef after a non-inclined ra | p.69 (« ولو ترى »), same sentence | p.35 |
| Taqlil and imala | pp.69-70 (التوراة, هار) | p.35 |
| Qalqala | p.60 (letters قطب جد, sound of the sakin letter) | p.44 |

So it is **not an independent second witness**: agreeing with Book A is not proof, because Book A
copied it. What it gives is the original, which is longer and sometimes more exact.

## What it settles in Book A (read on images)

| Point | Book A | New book | Effect |
| --- | --- | --- | --- |
| **معي** (ya of the speaker) | p.47: « ففتحها أين ما وقعت بشرط ألا تقع بعدها همزة قطع » (fatha) | p.79 *(image)*: in the list « أسكن الياء وصلا ووقفا », معي when no hamza qat' follows, **9 places** | Book A's sentence is a transcription error. The source agrees with the corpus spelling. `ya_idafa_maee` can say so |
| فأنظرني | p.49 « Sad 147 » | p.77 *(image)*: « الحجر 36، ص 79 » | « 147 » is Book A's own slip; 15:36 and 38:79 are right |
| أوزعني | p.49 « al-Ahqaf 14 » | p.78 *(image)*: « النمل 19 والأحقاف 15 » | « 14 » is Book A's own slip |
| أنظرني | p.46 « al-A'raf 40 » | p.77 *(image)*: « الأعراف 40 » | The slip is **inherited**: the corpus has the word at 7:14. Neither book is right |
| تدعونني | p.46 « Ghafir 43 » | p.78 *(image)*: items 17-18 both « غافر 43 » | Inherited. The corpus has 40:41 and 40:43 |
| عهدي الظالمين | p.47 « al-Baqara 144 » | p.78 *(image)*: « البقرة 144 » | Inherited. The corpus has it at 2:124 |
| فألقه (An-Naml 28) | p.19 kasra **with** sila; p.20 **without** | p.31 *(image)*: « بكسر الهاء مع الصلة »; p.164 *(image)*, table: « كسر الهاء بدون صلة » | The contradiction is **in the source**. It stays listed in `variants` |
| Madd munfasil lengths | 2, 3 or 4 | p.33: « حركتان أو ثلاث أو أربع » | Agrees with Book A, not with the reviewer's 2 or 4 |
| Qalqala kinds | none | none (p.60) | `qalqala_sughra` / `kubra` stay unsupported; one rule is right |

## What it could add

- **A 21-word ya'at idafa list with places** (pp.77-79): already in Book A.
- **Farsh tables** (pp.111-198): per ayah, the word in Hafs, what changes, and the Qaloun form, for
  example p.112 (2:13 السفهاء ألا, 2:31 هؤلاء إن) and p.164 (27:45 أنِ اعبدوا, 27:28 فألقه). The
  two-hamza cases and some sakin-before-wasl cases appear there **with a place**. That is the closed
  list Book A never gave.
- **A name for the path**: Abu Nashit, for the content of this book only.
- **More detail** in usul (about twice Book A), not yet compared rule by rule.

## What it does not fix

- **Sakin before hamzat al-wasl in general**: p.51 has the same examples and no word list. The
  tables list only some places (27:45 yes, 12:31 قالت اخرج not found in them). Still not detectable.
- **Closed ya before an ordinary letter**: no list of every ya of the speaker beyond Book A's.
- The corpus still carries the result of the rule, not the original letters. A table of places is
  needed to detect these cases, and the table only lists differences from Hafs.

## Roles the book could play

| Role | What changes | Cost | Risk |
| --- | --- | --- | --- |
| **a. Cross-check only** | Report differences; fix Book A's slips in notes and tests (معي, أوزعني, فأنظرني); everything stays `unspecified` | Small | None |
| **b. Second cited source** | Each rule it covers gets a second citation; `abu_nashit` only where the book states it (p.4, p.111) | Medium: 89 rules to match page by page on images | Citing a copy as independent proof; keep the wording « same text as Book A » |
| **c. Closed place lists from the farsh tables** | Detect two hamzas in two words and some sakin-before-wasl places; possibly farsh differences | Large: about 88 table pages (4 columns: ayah, Hafs word, change, Qaloun word) to read on images, because the text layer of the tables is out of order | A wrong parse silently mislabels an ayah; each row needs a check against the corpus |

**Recommendation.** Do **a** now: it removes the `معي` contradiction and three wrong place numbers
at no risk, and records the tariq. Do **b** after, rule by rule, saying where Book A is a copy. Treat
**c** as a separate project: it is the only role that fills the remaining gaps, but it needs a
row-by-row check against the corpus.

## Caveats

- Nothing here is scholarly review: the book is a source, not a validation.
- Its licence is unknown, like Book A's. Only paraphrases with page numbers belong in the repository.
- Page numbers cited above are the printed numbers, which equal the PDF pages.

## What was done with it (2026-11-01)

Every page of the usul part that a rule cites (pp.11-52, 65-81) was read on its image.

**Verification.** All 92 rules that have a counterpart agree with the longer book. Each now carries a
second citation (`scripts/add_second_citations.py`), with the limitation « same text as Book A, not
an independent source ». The tariq of every rule stays `unspecified`: the book names Abu Nashit only at
p.111, above the farsh tables, not in the usul. One rule has no counterpart: `ya_idafa_fath_exception`
(its list is not in the usul part).

**Differences found and recorded**

| Point | Result |
| --- | --- |
| معي (p.79) | Book A's sentence is a slip; noted in the rule |
| فألقه | The book contradicts itself: p.31 with the sila, p.33 and p.164 without. Both stay in `variants` |
| Ikhfa shafawi (p.17) | « ikhfa is the chosen one of two »: both readings now in `variants` (`ikhfa`, `idhar`) |
| تأمنا (p.71) | Two readings, `ishmam` and `ikhtilas`, now in `variants` |
| يلهث ذلك, اركب معنا, ألم نخلقكم (pp.73-75) | Two readings each, now in `variants`; the idgham detector no longer skips a letter that carries a waqf sign |
| آلذكرين / آلله (pp.36, 50) | A rule Book A states but we had not built: `hamza_istifham_before_article`, 4 places |

**Added from the longer book only.** The ya'at zawa'id (pp.80-81): `ya_zaida_joined_kept` (19 places),
`ya_zaida_two_ways` (4), `ya_zaida_kept_both` (1). The corpus writes the kept ya as a small yeh on the
last letter; each of the 19 places was found with it.

**Not done.** The madd length combinations (pp.98-100) and the waqf rules (pp.82-98) need a new
contract or a stop context the engine does not have; the farsh tables (pp.111-198) are untouched.
