# Qaloun to Hafs mapping: validation limits (public note)

This note replaces an internal report of the Wirdi AI project and keeps what limits the mapping.

## What the mapping establishes

- For a selection of Qaloun ayat it finds the corresponding ayat in the Hafs (Kufian) count, by
  linked components and an exact comparison of the letter skeletons of both texts. Example:
  **Qaloun 6:1-8 corresponds to Hafs 6:1-7**, not 6:1-8.
- The comparison works on derived copies only: it removes orthographic marks, unifies a documented
  set of letter forms, maps the Qaloun yeh barree (U+06D2) to ya, and compares the letter sequence
  exactly. The stored and returned Quran text is never modified.
- A verified correspondence means the **passages cover the same text**. It does not mean identical
  spelling, vocalization or recitation.

## Statuses

| Status | Meaning |
| --- | --- |
| `verified_equivalent` | the two numberings agree for the selection |
| `verified_difference` | they differ and the correspondence is verified |
| `mapping_requires_review` | the correspondence could not be verified; the selection is unsafe for retrieval (for example Al-Baqara 2:27) |

In the audit run for the application, 3,076 selections were verified as equivalent in their
boundaries and 473 required review. A multi-ayah selection that contains an unresolved component is
also withheld.

## Pagination

459 ayat have a verified physical span across two pages. None has a separately stored, independently
validated text-level break, so the page map gives the page span of an ayah, not the position of a
break inside it.
