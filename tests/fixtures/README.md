# Fixture policy

Foundation tests use synthetic identifiers and non-Quran sentinel strings only.
Later corpus fixtures require authorization, an immutable version and checksum,
explicit numbering identity, source attribution, and reviewed expected mappings.
Never place private reading history or credentials in fixtures.

Tajwid detector tests (`tests/unit/test_tajwid_detectors.py`) use short orthographic
strings spelled the way the corpus spells them and modelled on examples of the cited books
(the page is named in a comment). They exercise the procedure; they are not Quran data.
Real-corpus checks (`tests/integration/test_tajwid_real_corpus.py`) are opt-in with
`WIRDI_TEST_SOURCE_ROOT`. Source books and extracted book text must never be added here.
