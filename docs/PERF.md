# Performance (0.6.0, 79 detectors)

Measured through the real stdio server (`scripts/measure_perf.py`), 30 runs per case, on the
development machine, Python 3.12, real Wirdi AI source files, waqf context. Every call
re-verifies the Quran corpus, pagination and rule checksums (fail closed).

| Target | Result |
| --- | --- |
| Cold start to the first `tools/list` | 0.57 s (target < 3 s) |
| One app page (`analyze_app_page`) | p50 106 ms, p95 128 ms (target < 200 ms) |

| call | p50 ms | p95 ms | max ms |
| --- | ---: | ---: | ---: |
| 1 ayah (analyze) | 54 | 76 | 116 |
| 8 ayat (analyze) | 106 | 128 | 129 |
| 50 ayat (analyze, 100 rows) | 125 | 150 | 167 |
| 100 ayat (analyze, largest page: 500 rows) | 439 | 454 | 459 |
| 1 surah (summarize, Kahf) | 81 | 105 | 105 |
| longest surah (summarize, Baqara) | 229 | 234 | 237 |
| 1 app page (analyze_app_page) | 106 | 128 | 142 |
| get_tajwid_rule | 8 | 10 | 20 |

## What was optimised

- One read of the corpus and one of the pagination file per request (the first version read
  the corpus four times); a request that returned 8 ayat went from 154 ms to 80 ms.
- The rule manifest and edition metadata are read once per request, not once per rule.
- Per-verse references are shared between annotations; only the requested page window is
  turned into annotation objects while counts use every occurrence.
- Default page size is 100 annotations (maximum 500). The 500-row case is dominated by JSON
  serialization (about 1 MB twice: structured and text content), not by detection.

## What was deliberately not done

There is no cache of parsed data across requests. Revalidating the checksums on each call
keeps the earlier "fail closed on any source change" guarantee; the cost is about 30 ms.
A cache keyed on file stat signatures would cut that and is a possible later step.
Detection itself over all 6,214 ayat takes about 10 s with all 79 detectors in both modes
(`scripts/audit_rules.py`), against 0.7 s for the 14 first detectors: the Book A families
tripled the per-ayah work, and every figure above stays inside the targets.
