#!/usr/bin/env python3
"""Per-rule frequency audit of the detectors over all 6,214 single-ayah selections.

Read-only. Flags any rule with zero hits or a rate above 10% of all letters. Prints markdown.
"""

import argparse
import functools
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WAQF_ONLY = frozenset(
    "madd_arid_sukun madd_iwad madd_lin madd_muttasil_arid ra_mutatarrif_jawaz "
    "ra_mutatarrif_tafkhim ra_mutatarrif_tarqiq".split()
)
sys.path.insert(0, str(ROOT / "src"))

from wirdi_mcp.domain.models import ReadingContext  # noqa: E402
from wirdi_mcp.knowledge.registry import RuleRegistry  # noqa: E402
from wirdi_mcp.quran.source import PublicSourceRepository  # noqa: E402
from wirdi_mcp.tajwid.detectors import DETECTORS  # noqa: E402
from wirdi_mcp.tajwid.engine import TajwidEngine  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--source-root", type=Path, help="optional Wirdi AI checkout; default: bundled"
    )
    args = parser.parse_args()
    repo = (
        PublicSourceRepository(args.source_root)
        if args.source_root
        else PublicSourceRepository.bundled()
    )
    repo.load_edition = functools.cache(repo.load_edition)
    engine = TajwidEngine(repo, RuleRegistry(ROOT / "knowledge"))
    rules = engine.select_rules((), ())
    rows = repo.load_edition("qalun")
    letters = sum(len(r.text) for r in rows)
    flags = []
    print("| rule | waqf | wasl |\n| --- | ---: | ---: |")
    totals, notes = {}, {}
    for mode in ("waqf", "wasl"):
        counts, unresolved, skipped = Counter(), Counter(), Counter()
        for i in range(6214):
            result = engine.detect(rows, i, i, ReadingContext(mode=mode), rules)
            counts.update(o.rule_id for _, o in result.occurrences)
            unresolved.update(result.unresolved)
            skipped.update(result.skipped)
        totals[mode], notes[mode] = counts, (unresolved, skipped)
    for rule_id in sorted(DETECTORS):
        print(f"| `{rule_id}` | {totals['waqf'][rule_id]} | {totals['wasl'][rule_id]} |")
        for mode in totals:
            n = totals[mode][rule_id]
            if n == 0 and mode == "wasl" and rule_id in WAQF_ONLY:
                continue  # a single ayah in wasl never stops, so a stop-only rule cannot fire
            if n == 0:
                flags.append(f"{rule_id} ({mode}): zero hits")
            elif n > letters * 0.1:
                flags.append(f"{rule_id} ({mode}): {n} hits is abnormally high")
    for mode, (unresolved, skipped) in notes.items():
        print(f"\n**{mode}: unresolved** {dict(unresolved) or 'none'}\n")
        print(f"**{mode}: skipped** " + "; ".join(f"{k}: {v}" for k, v in skipped.items()))
    print("\n**Flags:** " + ("; ".join(flags) if flags else "none"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
