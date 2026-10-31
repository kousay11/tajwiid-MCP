# Decisions taken autonomously

Applied from the mission defaults; revisit each with the project owner.

1. **Reviewer:** none named. No annotation or rule may reach `verified` /
   `scholarly_verified`; the highest status emitted is `cross_checked`.
2. **Transmission path:** the Abu Nashit attestation of the Hannibal mushaf (page م1)
   and of book B is a documented hypothesis. The corpus keeps `tariq=unspecified`.
3. **Mushaf reading context:** annotations derived from the coloured mushaf are
   labelled `waqf` (end of verse and waqf signs).
4. **Divergent or ambiguous sources:** status `conflict`; no silent choice.
5. **Manifest drift (J0):** only the `arabic.py` and `schemas.py` hashes were updated,
   after the complete real-source conformance passed. See `SOURCE_AUDIT.md`.
6. **Git hygiene:** `*.pdf`, page images and mushaf-derived data are ignored globally
   (including `*.png`/`*.jpg`) before the first commit.
7. **Mushaf pilot (J4): NO-GO.** Blob to letter attachment is not computable without glyph
   recognition, legend colours do not separate on the text, recall and ornament masking
   are inadequate. The full extraction (J5) was skipped; see `PILOT_REPORT.md`.
8. **Rule tariq:** rule records cite book B (Abu Nashit) or only book A; a rule backed by
   both is marked `abu_nashit`, one backed by book A alone `unspecified`. Applying either to
   the corpus is the documented hypothesis from decision 2.
9. **Source divergence:** books A (pp.5-6) and B (p.58) classify the completeness of the
   idgham with ghunna differently. The rule record states both and does not choose.
10. **Detector input:** the corpus spells the sakin noon/mim before idgham, ikhfa and
    iqlab letters without a sukun and signals iqlab with a small high meem, so detectors
    classify by the following letter and recognise bare noon/mim as sakin.
11. **Candidate default:** `include_candidates` defaults to true because no reviewed
    annotation exists; with false the tools return no annotation and say why.
