# Book A coverage

Book A is `docs/BOOK_21652_1.pdf` (51 pages, a simplified Qaloun summary, not committed). This
table maps each section to what the MCP does with it. Page numbers are the printed numbers of
the book, which equal the PDF page numbers. "Detected" means a deterministic detector proposes
`candidate` annotations; "record only" means the rule is readable with `get_tajwid_rule` but
nothing is detected. Everything is unreviewed.

Book A names places in the Kufian numbering of its printed copy. The corpus carries those
numbers in `number_in_hafs`, so lists are matched against that and not against the Qaloun count.

| Pages | Book A section | Rule ids | State |
| --- | --- | --- | --- |
| 1-3 | Lives of Qaloun and Nafi' | none | not a rule |
| 4-13 | Noon, tanween, meem, qalqala, lam, ghunna | 14 first-release rules | detected (0.5.0) |
| 14-15 | Natural madd; badal | `madd_tabii`, `madd_badal` | detected |
| 15 | Joining hamzat al-wasl and hamzat al-qat' in one word | none | **not covered** (needs morphology) |
| 16-17 | Madd al-'iwad, alef of حي طهر | `madd_iwad`, `madd_harf_hay_tahar` | detected |
| 17-20 | Sila of the plural meem and of the pronoun ha, with its exceptions | `madd_sila_sughra_meem`, `madd_sila_kubra_meem`, `madd_sila_sughra_ha`, `madd_sila_kubra_ha`, `madd_sila_ha_exception` | detected; the ha follows the sign the corpus writes, the meem lists both readings (see "The plural meem before ba and meem") |
| 17 | Waqf on a verb with a tanween-like light tawkid noon (وليكونا، لنسفعا) | none | **not covered** (two words) |
| 19-20 | Muttasil, munfasil | `madd_muttasil`, `madd_munfasil` | detected, lengths in `variants` |
| 20-21 | 'Arid lil-sukun, muttasil 'arid, lin | `madd_arid_sukun`, `madd_muttasil_arid`, `madd_lin` | detected, waqf only |
| 21-22 | Lazim kalimi (muthaqqal, mukhaffaf: محياي، آلآن) | `madd_lazim_kalimi_muthaqqal`, `madd_lazim_kalimi_mukhaffaf` | detected |
| 22-23 | Lazim harfi (نقص عسلكم) | `madd_lazim_harfi_muthaqqal`, `madd_lazim_harfi_mukhaffaf` | detected at the 29 opening ayat |
| 23 | الم الله (two readings when joined) | none | **not covered** |
| 23-24 | Alefs kept at a stop; the alef of أنا | `alef_thabita`, `alef_ana_before_hamza`, `alef_ana_before_hamza_kasra`, `alef_ana_dropped` | detected |
| 24 | Madd letter dropped between two sakin | `madd_letter_dropped` | detected, wasl only |
| 25 | Single hamza replaced or changed | `hamza_ibdal_yajuj`, `hamza_ibdal_ruya`, `hamza_ibdal_minsaa`, `hamza_ibdal_saala`, `hamza_ibdal_musada`, `hamza_waw_huzu_kufu` | detected (word lists) |
| 25-26 | The prophet and its derivatives; two exceptions | `hamza_nabi`, `hamza_nabi_exception` | detected |
| 26-27 | Two hamzas in one word; exceptions; added interrogative hamza | `hamza_double_in_word`, `hamza_double_exception`, `hamza_istifham_added` | detected; the softening of أرأيت is **not covered** |
| 27 | The 11 repeated interrogatives | `istifham_repeated_first`, `istifham_repeated_second` | detected at ayah level (anchored on the ayah's first word) |
| 27-29 | Two hamzas in two words (same, different) | `hamza_two_words_same`, `hamza_two_words_different` | **record only**: the Qaloun text already carries the result, not the original hamzas |
| 29-31 | Hamzat al-wasl: article, 7 nouns, verbs | `hamzat_wasl_article`, `hamzat_wasl_noun`, `hamzat_wasl_verb` | detected; verbs are recognised from the spelling, with no morphology |
| 31 | Vowel given to a sakin letter before hamzat al-wasl | `sakin_before_hamzat_wasl` | partial: من, the plural meem and tanween only |
| 32-35 | Isti'la, ra, lam of Allah, alef, ghunna | `ra_*` (6), `lam_jalala_*` (2), `alef_tafkhim`, `alef_tarqiq`, `ghunna_tafkhim`, `ghunna_tarqiq` | detected; the degrees of the isti'la letters are **not covered** |
| 35 | Taqlil and imala | `taqlil_tawrat`, `imala_har` | detected |
| 36-39 | Idgham kabir and saghir; naqis | `idgham_kabir_mutamathil`, `idgham_mutamathilayn`, `idgham_mutajanisayn`, `idgham_mutaqaribayn`, `idgham_naqis` | detected; second readings the book mentions are listed only for the two-reading words |
| 40-45 | Places of articulation and characteristics | tool `get_letter_properties` | static tables, 29 letters |
| 45-50 | Ya'at al-idafa | `ya_idafa_fath`, `ya_idafa_iskan_exception`, `ya_idafa_fath_exception`, `ya_idafa_iskan_before_letter`, `ya_idafa_maee`, `ya_idafa_rabbi_two_readings` | partial (see below) |

## The plural meem before ba and meem

The corpus writes the sakin meem with no sukun before ب and م. The sila detector first required a
sukun and so missed these meems (1,314 places). It now includes them.

- **Page basis.** p.17 says the plural meem before a moving letter that is not a hamza has two
  readings, iskan or sila. p.18 gives an example before a meem (في قلوبهم مرض). No example is given
  before a ba; that case rests on the general wording of p.17.
- **Variants.** Every place of `madd_sila_sughra_meem` lists `["iskan", "sila_2_harakat"]`, new ones
  included. p.17 says explicitly that the sila of the plural meem is « قدر حركتين » (2 harakat), so the
  length is kept in the name. The short form `["iskan", "sila"]` is forbidden by a test.
- **Interaction with ikhfa/idgham shafawi.** The book does not say it. By the construction of the
  rule, with the sila the meem is no longer sakin, so ikhfa/idgham shafawi on the same meem apply to
  the iskan reading only. This is an inference, written in the notes of both annotations: the sila
  note says the shafawi rule applies to the iskan reading only, and the `ikhfa_shafawi` and
  `idgham_shafawi` notes of a plural meem say the sila excludes them. A test checks that the two
  always come in pairs on the same meem.

## Words Book A states in two ways

- **فألقه** (an-Naml 28): p.19 item 7 reads the ha with a kasra **and** the sila; p.20 reads it with a
  kasra and **no** sila. The book contradicts itself. `madd_sila_ha_exception` keeps the word with
  `variants: ["without_sila", "with_sila"]` and a note citing both pages. Nothing is chosen.
- **يأته** (Ta-Ha 75): p.19 item 6 gives two readings, a kasra without the sila and the sila.
  The rule lists both in `variants`.
- The other words of that list (نؤته، نوله، نصله، أرجه، يتقه، يؤده) are stated one way and carry no
  `variants`.

## Contradictions between pages of Book A (ya'at al-idafa)

Read from the page images (pp.46-50) and checked against the corpus. Places are the book's Kufian
numbers; "kept" means the word is in that ayah of the corpus.

| Word | Page A says | Page B says | Corpus check | Kept |
| --- | --- | --- | --- | --- |
| تدعونني | p.46 item 13: Ghafir 43 only | p.49 item 6: Ghafir 41 and 43 | in 40:41 and 40:43 | both |
| أنظرني | p.46 item 6: al-A'raf 40 | p.49 item 1: al-A'raf 14 | in 7:14, not in 7:40 | 7:14 |
| فأنظرني | p.46 item 6: al-Hijr 36, Sad 79 | p.49 item 4: al-Hijr 36, Sad 147 | in 15:36 and 38:79; Sad has no 147 | 15:36, 38:79 |
| أوزعني | p.49 item 6: al-Ahqaf 14 | p.46 item 15 puts ذريتي in 15, the same ayah | in 46:15, not in 46:14 | 46:15 |
| عهدي الظالمين | p.47 item 1: al-Baqara 144 | (no other page) | in 2:124, not in 2:144 | no place used |

The heading of p.46 announces 21 closed words but its list gives 20 places (it omits Ghafir 41);
p.48-49 list 21. Nothing in the code depends on the p.46 count.

## Ya'at al-idafa

The corpus spells the open ya with a fatha and the closed ya with the yeh barree, but the yeh
barree also ends ordinary words (في، الذي). So:

- An open ya before a hamza or hamzat al-wasl is **detected** from its spelling (`ya_idafa_fath`).
- The closed ones that the book names against its own class (24 places) and the open ones it names
  against the "closed" default (6 places) are matched from its lists.
- The default for "before any other letter" is closed, and it is **not detected** beyond the seven
  examples the book names on p.47 (`ya_idafa_iskan_before_letter`): a closed ya is indistinguishable
  from an ordinary final yeh.
- **معي** (p.47, last sentence): the book says the ya is open unless a fatha hamza follows, but the
  corpus spells it the other way round (open only before a fatha hamza, 2 of 11 places), which is
  also what the book's own classes 1 and 6 give. `ya_idafa_maee` reports each occurrence with what
  the corpus spells and chooses nothing.

## Citations checked on the page images

The cited pages of every Book A rule were checked against the page images (pp.14-39 and 45-50), not
against extracted text. Pages that fund a rule but were missing were added: for the sila (p.17,
p.18, p.19), `madd_iwad` (p.15, p.17), `madd_badal` (p.16), `madd_harf_hay_tahar` (p.15, p.23),
`madd_lin` (p.20), `alef_ana_dropped` (p.24), the three hamzat al-wasl rules (p.31), `ra_tafkhim`
(p.34), `lam_jalala_tarqiq` (p.34), `alef_tafkhim` (p.32), `idgham_mutajanisayn` (p.38) and the ya'at
rules (p.47, p.49, p.50). A test pins the pages of each.

Two content points came out of that reading:

- **Fixed:** p.31 says that امشوا، ابنوا، امضوا، اقضوا begin with a kasra (the damma on their third
  letter is accidental). The detector now says so; before it said damma for them.
- **Not fixed, needs a decision:** p.35 says the alef is heavy also after a ra that is not
  inclined (غير المقللة, example « ولو ترى »). `alef_tafkhim` only covers the isti'la letters and the
  heavy lam of the name of Allah, so it misses the alef after ra. It is not implemented because
  deciding which ra is "not inclined" needs the book's list of taqlil words.

## Honest limits

- This is a summary book. Word-by-word rules (farsh) beyond its lists are not in it, so
  "everything in Book A" is not "everything in Qaloun Tajwid".
- The page given for each rule is where the section begins; the cited pages need proofreading.
- Lists keyed to Kufian ayah numbers may flag more than one Qaloun ayah when a Kufian ayah is split
  in the Qaloun count.
- Rule texts are paraphrases written by an automated drafter. No reviewer has confirmed any of them
  or any detected occurrence; the highest status served is `candidate`.
- The corpus `tariq` is `unspecified` and Book A attests Qaloun without naming Abu Nashit, so the
  65 rules from Book A carry `tariq: "unspecified"`.
