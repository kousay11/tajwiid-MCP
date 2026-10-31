# Rule records

`<rule_id>/<version>.json` are paraphrased rule records (English with Arabic terms) with
conditions, exceptions, limitations and book and page citations. All are
`validation_status: "unreviewed"`; a rule definition establishes nothing about any passage.
`manifest.json` pins each file's SHA-256 and the edition metadata; regenerate it with
`scripts/build_rule_manifest.py` (`--check` verifies). A changed byte makes the registry fail
closed with `INTEGRITY_FAILURE`. Adding a rule needs a detector, a citation that resolves
and tests; promoting one needs a named reviewer's `validation/` record.
