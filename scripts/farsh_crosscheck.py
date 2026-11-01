#!/usr/bin/env python3
"""Compare the ya rows of the farsh tables (Nabhan pp.111-198) with the ya detectors, by place.

Reads the local rows written by scripts/extract_farsh_rows.py. For each row that opens a ya, closes
a ya or keeps a zaida ya, it asks whether the detectors report that kind of ya in the corpus ayah at
the row's Kufian place. Prints a markdown summary and the places where the two disagree. Read-only.
"""

import collections
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from wirdi_mcp.domain.models import ReadingContext  # noqa: E402
from wirdi_mcp.knowledge.registry import RuleRegistry  # noqa: E402
from wirdi_mcp.quran.source import PublicSourceRepository  # noqa: E402
from wirdi_mcp.tajwid.engine import TajwidEngine  # noqa: E402

CLASSES = {
    "فتح الياء": (
        "the table opens a ya",
        {"ya_idafa_fath", "ya_idafa_fath_exception"},
    ),
    "أسكن الياء": (
        "the table closes a ya",
        {"ya_idafa_iskan_exception", "ya_idafa_iskan_before_letter", "ya_idafa_maee"},
    ),
    "أثبت الياء": (
        "the table keeps a zaida ya",
        {"ya_zaida_joined_kept", "ya_zaida_two_ways", "ya_zaida_kept_both"},
    ),
}


def norm(desc: str) -> str:
    return re.sub(r"\s+", " ", desc.replace("اهل", "اله").replace("وصال", "وصلا")).strip()


def main() -> int:
    rows = json.loads(
        (ROOT / "knowledge/sources/thamar-yani-2003/farsh_rows.json").read_text(encoding="utf-8")
    )
    repo = PublicSourceRepository.bundled()
    corpus = repo.load_edition("qalun")
    engine = TajwidEngine(repo, RuleRegistry(ROOT / "knowledge"))
    wanted = set().union(*(rules for _, rules in CLASSES.values()))
    rules = engine.select_rules(tuple(sorted(wanted)), ())
    found: dict[tuple[int, int], set[str]] = collections.defaultdict(set)
    for index, row in enumerate(corpus):
        result = engine.detect(corpus, index, index, ReadingContext(mode="wasl"), rules)
        for _verse, occurrence in result.occurrences:
            for k in row.links:
                found[(row.surah, k)].add(occurrence.rule_id)
    summary = collections.Counter()
    misses = collections.defaultdict(list)
    for row in rows:
        d = norm(row["desc"])
        for key, (label, rule_ids) in CLASSES.items():
            if key not in d:
                continue
            for ayah in row["ayah"]:
                summary[(label, "rows")] += 1
                if found.get((row["surah"], ayah), set()) & rule_ids:
                    summary[(label, "found")] += 1
                else:
                    misses[label].append((row["surah"], ayah))
    print("| Table says | Places | A detector reports it | Missing |")
    print("| --- | ---: | ---: | ---: |")
    for _key, (label, _rules) in CLASSES.items():
        total, hit = summary[(label, "rows")], summary[(label, "found")]
        print(f"| {label} | {total} | {hit} | {total - hit} |")
    for label, places in misses.items():
        print(f"\n{label}, no detector hit at: {sorted(set(places))}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
