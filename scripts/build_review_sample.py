#!/usr/bin/env python3
"""Write a reviewer worksheet: a deterministic sample of candidates per rule (references only).

No Quran or book text is written; a reviewer reads the passage with `get_qaloun_passage` and
the rule with `get_tajwid_rule`. Usage: build_review_sample.py --source-root ... --out ...
"""

import argparse
import functools
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from wirdi_mcp.domain.models import ReadingContext  # noqa: E402
from wirdi_mcp.knowledge.registry import RuleRegistry  # noqa: E402
from wirdi_mcp.quran.source import PublicSourceRepository  # noqa: E402
from wirdi_mcp.tajwid.engine import TajwidEngine  # noqa: E402

PER_RULE = 5


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--out", type=Path, default=ROOT / "docs" / "REVIEW_SAMPLE.md")
    args = parser.parse_args()
    repo = PublicSourceRepository(args.source_root)
    repo.load_edition = functools.cache(repo.load_edition)
    engine = TajwidEngine(repo, RuleRegistry(ROOT / "knowledge"))
    rules = engine.select_rules((), ())
    rows = repo.load_edition("qalun")
    pages = repo.load_pages()
    found: dict[str, list] = {rid: [] for rid in rules}
    for index in range(len(rows)):
        result = engine.detect(rows, index, index, ReadingContext(mode="waqf"), rules)
        for verse, occ in result.occurrences:
            found[occ.rule_id].append((verse, occ))
    out = [
        "# Reviewer worksheet",
        "",
        "For the future qualified reviewer. Every row is a **candidate** from a deterministic",
        "detector (waqf reading, one ayah at a time); none is verified. References only: read the",
        "ayah with `get_qaloun_passage`, the rule with `get_tajwid_rule`, and the cited book pages",
        "from your own copy. Codepoints are a half-open range into the unchanged ayah text;",
        "the word index counts words that contain at least one letter. Mark each row correct,",
        "wrong or doubtful and note a reason; a decision becomes a `ValidationRecord` only",
        "under your name.",
        "",
        "Open points for the reviewer, independent of the sample:",
        "",
        "- Books A (pp.5-6) and B (p.58) classify the completeness of idgham with ghunna",
        "  differently.",
        "- Whether the corpus (tariq unspecified) follows the Abu Nashit path the rules cite.",
        "- Lam rules cite book A only; the Abu Nashit book has not been read for them.",
        "- Plural-mim connection (silat) and internal waqf signs are not modelled.",
        "",
    ]
    for rule_id, rule in sorted(rules.items()):
        hits = found[rule_id]
        step = max(1, len(hits) // PER_RULE)
        sample = hits[::step][:PER_RULE]
        cites = ", ".join(c.locator + f" ({c.source_id})" for c in rule.evidence)
        out += [
            f"## `{rule_id}` ({rule.name_ar})",
            "",
            f"{len(hits)} candidates in the corpus. Cited: {cites}.",
            "",
            "| ayah | word | codepoints | app page | note | verdict |",
            "| --- | ---: | --- | --- | --- | --- |",
        ]
        for verse, occ in sample:
            page = pages[verse.index]
            span = f"{page[0]}" if page[0] == page[1] else f"{page[0]}-{page[1]}"
            out.append(
                f"| {verse.row.surah}:{verse.row.number} | {occ.word_index} "
                f"| {occ.start}-{occ.end} | {span} | {occ.note} | |"
            )
        out.append("")
    args.out.write_text("\n".join(out) + "\n", encoding="utf-8")
    print(f"wrote {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
