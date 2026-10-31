# Qaloun pagination: how the 559-page map was made (public note)

This note replaces an internal audit of the Wirdi AI project and keeps only what the map needs to be
understood. It describes `data/generated/qaloun_pagination_verified.json`, pinned by SHA-256 in
`source_manifest.json`.

## What the map is

- A page span for each of the 6,214 Qaloun ayat, in the **559-page printed layout** of the King Fahd
  Complex Qaloun mushaf (printed 17/10/1427 H, 2006). Verse numbers are in the Qaloun count.
- Page-number convention: printed page = PDF page index − 1.
- It is **not** the 604-page Madinah-style layout. The old 604-page map taken from a Warsh list of
  `quran-meta` was found not to be the layout of this edition: only 62 of the 6,214 verses fall on
  the same page in both.

## Method

1. Each printed page was rendered and the verse-end markers and surah banners inside the text frame
   were detected, without OCR.
2. Markers were counted per page: 6,214 verses, of which 6,209 were detected and 5 sit on the two
   ornate frame pages (page 1, Al-Fatiha, and page 2, the first 3 ayat of Al-Baqara) and were set
   from the images.
3. Pages were replayed in order, switching surah at each banner, and compared with the Qaloun verse
   counts: 112 of 114 surahs match exactly from the images; the other two are the frame pages.
4. A verse may start on one page and end on the next: 459 of the 558 page boundaries fall inside an
   ayah, and no ayah spans more than 2 pages.

## Cross-check with the mushaf's printed surah index

- The first verse of every surah on the index page: 112 of 114 match; the two exceptions (Fatir 35
  and al-Mumtahana 60) are explained by the images (banner and bismillah at the foot of the previous
  page).
- The heading page: 113 of 114; the exception is al-Layl 92 for the same kind of reason.

## Status

`verified_against_edition`: every page was processed (none extrapolated). The Quran text itself was
not changed; only page boundaries were derived. The page images are copyrighted scans and are not
part of this repository.
