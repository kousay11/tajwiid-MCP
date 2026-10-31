#!/usr/bin/env python3
"""Validate every rule record and (re)write knowledge/rules/manifest.json.

`--check` only verifies that the committed manifest matches the files on disk.
"""

import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from wirdi_mcp.knowledge.models import TajwidRule  # noqa: E402
from wirdi_mcp.knowledge.registry import RuleRegistry  # noqa: E402


def build(knowledge: Path) -> dict:
    entries = []
    for path in sorted((knowledge / "rules").glob("*/*.json")):
        raw = path.read_bytes()
        rule = TajwidRule.model_validate_json(raw)
        relative = path.relative_to(knowledge).as_posix()
        if relative != f"rules/{rule.rule_id}/{rule.version}.json":
            raise SystemExit(f"{relative}: path does not match rule id and version")
        entries.append(
            {
                "rule_id": rule.rule_id,
                "version": rule.version,
                "path": relative,
                "sha256": hashlib.sha256(raw).hexdigest(),
            }
        )
    editions = (knowledge / "sources" / "editions.json").read_bytes()
    return {
        "manifest_version": "wirdi-mcp-rules-v1",
        "editions_sha256": hashlib.sha256(editions).hexdigest(),
        "rules": entries,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--knowledge", type=Path, default=ROOT / "knowledge")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    manifest = build(args.knowledge)
    target = args.knowledge / "rules" / "manifest.json"
    text = json.dumps(manifest, ensure_ascii=False, indent=2) + "\n"
    if args.check:
        if not target.is_file() or target.read_text(encoding="utf-8") != text:
            print("manifest is stale; run scripts/build_rule_manifest.py", file=sys.stderr)
            return 1
        registry = RuleRegistry(args.knowledge)
        for rule_id, version in registry.list_rules():
            registry.get_rule(rule_id, version)  # also resolves every citation
        print(f"manifest ok: {len(manifest['rules'])} rules")
        return 0
    target.write_text(text, encoding="utf-8")
    print(f"wrote {target} ({len(manifest['rules'])} rules)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
