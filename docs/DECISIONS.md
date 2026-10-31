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
