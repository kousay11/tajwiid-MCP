# Mushaf pilot report (J4): decision NO-GO

Scope: 10 pages of the coloured Hannibal mushaf (`scripts/mushaf_pilot.py`, outputs only
under the git-ignored `.work/mushaf_pilot/`). Pages (pdf numbers): 3 (Fatiha and start of
Baqara), 50, 150, 299, 300 and 301 (Kahf, 300 is printed page 299), 450, 605 (last Quran
page), 616 (legend, م11), 620 (annex with coloured examples). Nothing derived from the
scan is committed.

## Gate

GO needed at least 95% of red blobs attached to the correct letter **and** at least 90%
agreement with the detectors where comparable. **Neither could be reached or even measured
with the available tooling**, so the full extraction (J5) was not run.

## What was measured

| Check | Result |
| --- | --- |
| Pages processed | 10 of 10, no failure |
| Coloured blobs found (area ≥ 30 px, inside the text frame) | 666 crimson, 91 pure red, 231 grey |
| Blobs that are fragment-sized (< 120 px: dots, small strokes) | 428 of 666 crimson (64%) |
| Blobs merged into letter-sized clusters (22 px gap) | 666 → 377 |
| Verse rings found by Hough circles | 1 to 21 per page; page 300: 8 found, one visibly missed (ring 46) |
| Blobs masked as being on a ring | 0 to 28 per page for crimson |
| Page 300 vs detectors (Kahf qalun 45–52, waqf) | 33 crimson clusters on the page; detectors give 28 ghunna/qalqala-related candidates and 71 in total |

## Findings that decide the question

1. **The page is a raster.** No glyph, codepoint or position exists in the file. Attaching a
   blob to a codepoint needs glyph recognition or forced alignment against the printed
   font. Neither tool exists here: OCR is excluded, the printed font is not available and
   Arabic letters join, so splitting words by gaps is unreliable. The "% attached to the
   right letter" metric is therefore not computable automatically.
2. **Blobs are not letters.** 64% of crimson blobs are fragments (hollow dots of a jeem,
   small strokes of a diacritic). Merging by proximity gives clusters, but a cluster can
   still be a letter plus a neighbouring dot.
3. **Recall is incomplete.** Thin crimson strokes fall below the saturation threshold. On
   page 300 two visibly coloured letters (a ra in the word before "وَحَشَرْنَاهُمْ" and the ra at
   the end of "نُغَادِرْ") were not detected at all.
4. **Ornaments produce false positives and also hide real hits.** One ring (46) on page 300
   was not masked and gave two blobs. On page 3 the circle detector reported 21 rings for
   a page with about a dozen, so masking can also remove genuine letter blobs.
5. **The legend colours do not separate on the text.** Sampled swatches on page م11:
   grey (hue undefined), "red" #2 = pure red (hue 0, BGR ≈ 18,15,240) and "orange" #3 =
   a crimson (hue 173, BGR ≈ 84,39,236), not orange. On page 300 **every** coloured blob
   has hue 170–177 (crimson), including the red qalqala letter of "لَقَدْ" and the waw
   after a tanween. By the swatches that is colour #3, yet the legend assigns ghunna and
   qalqala to #2. Either the legend swatches are not faithful or the printer used one
   colour for both; this is a conflict between the legend and the pages and needs the
   publisher or a reviewer. Pure red appears only on a few pages (30 small blobs on pages 301
   and 605) and its meaning is unknown.
6. **Some colourings are not explained by the legend or the detectors**, for example the
   coloured ra at the end of "نُغَادِرْ": no implemented rule explains it. Colour alone
   cannot be turned into a rule without a reviewer.

Examples of failure (page 300): ring 46 blobs; undetected thin ra; a hollow-dot fragment
counted separately from its jeem.

## Decision

**NO-GO.** The full mushaf was not processed, and no `source_annotated`, `cross_checked`
or `conflict` annotation exists. The MCP stays valid on books plus detectors. The detector
output is not compared with colours anywhere in the served data.

## What a future attempt would need

- A way to identify glyphs: font-based forced alignment or a trained recognizer, and a
  hand-labelled ground truth of a few hundred blobs by a qualified reader.
- The publisher's legend (or a reviewer) to settle whether #2 and #3 are separable.
- Clearance of the scan's licence for any derived data.
