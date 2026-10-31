"""The README table of rules and its counts must follow the rule records."""

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
README = (ROOT / "README.md").read_text("utf-8")
RULES = [
    json.loads(p.read_text("utf-8"))
    for p in sorted((ROOT / "knowledge" / "rules").glob("*/1.json"))
]


def test_every_rule_has_a_row_in_the_readme_table_with_its_family():
    rows = dict(re.findall(r"^\| `([a-z0-9_]+)` \| [^|]+ \| `([a-z_]+)` \|", README, re.M))
    assert set(rows) == {r["rule_id"] for r in RULES}
    assert all(rows[r["rule_id"]] == r["family"] for r in RULES)


def test_the_readme_counts_follow_the_repository():
    from wirdi_mcp.tajwid.detectors import DETECTORS

    assert f"{len(RULES)} rules · {len(DETECTORS)} detectors" in README
    assert f"## 7. All {len(RULES)} rules" in README
    assert "docs/APPLY.json" in README
    assert (ROOT / "docs" / "APPLY.json").is_file()


def test_every_local_link_of_the_readme_exists():
    links = [x for x in re.findall(r"\]\(([^)#]+)\)", README) if not x.startswith("http")]
    assert links and all((ROOT / link).exists() for link in links), links
