# Local Tajwid roadmap

The project is local-first. The MCP server uses stdio and reads only the explicitly
configured, checksum-pinned Qaloun source files and its own hash-pinned knowledge files.

| Phase | Scope | Gate | State |
| --- | --- | --- | --- |
| 1 Foundation | Packaging, stdio transport, diagnostics, typed contracts | Tests, smoke test, lint | done |
| 2 Quran tools | Read-only Qaloun access and the existing mapping authority | Integrity and conformance | done |
| 3 Tajwid knowledge | Audited sources, page-cited rule records, local page store | Tamper tests, citations resolve | done for 14 rules (unreviewed) |
| 4 Tajwid engine | Deterministic detectors, wasl/waqf context, candidate annotations | Fixtures; full-corpus run; frequency audit | done for the same 14 rules |
| 5 Scholarly validation | Named reviewer, validation records, reviewed explanations | Records bound to subject hashes | **blocked: no reviewer** |
| 6 Coloured-mushaf source | Extract the publisher's colouring as a second source | Pilot: 95% attach, 90% agreement | **NO-GO** (see PILOT_REPORT) |
| 7 Application integration | Managed MCP client in wirdi-Ai, UI of verified annotations only | Regression, privacy, failure isolation | not started, out of scope so far |

Current state: **0.5.0, local Tajwid candidates.** Quran access, mapping, rule lookup,
candidate analysis, summaries, per-page analysis and local page lookup all work through
stdio. Everything Tajwid is unreviewed. Not covered at all: madd, hamza, imala, ya'at,
tafkhim and tarqiq, waqf rules, lafz al-jalala, and every Book B section that is not named
in [HANDOFF](HANDOFF.md). No network provider, outbound MCP client, RAG or agent is part of
this project.
