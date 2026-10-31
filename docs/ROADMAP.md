# Local Tajwid roadmap

The project is local-first. The MCP server uses stdio and reads only the explicitly
configured, checksum-pinned Qaloun source files and its own hash-pinned knowledge files.

| Phase | Scope | Gate | State |
| --- | --- | --- | --- |
| 1 Foundation | Packaging, stdio transport, diagnostics, typed contracts | Tests, smoke test, lint | done |
| 2 Quran tools | Read-only Qaloun access and the existing mapping authority | Integrity and conformance | done |
| 3 Tajwid knowledge | Audited sources, page-cited rule records, local page store | Tamper tests, citations resolve | done for 79 rules (unreviewed): 14 first release + 65 from Book A |
| 4 Tajwid engine | Deterministic detectors, wasl/waqf context, candidate annotations | Fixtures; full-corpus run; frequency audit | done for 77 rules; 2 hamza rules are record-only |
| 5 Scholarly validation | Named reviewer, validation records, reviewed explanations | Records bound to subject hashes | **blocked: no reviewer** |
| 6 Coloured-mushaf source | Extract the publisher's colouring as a second source | Pilot: 95% attach, 90% agreement | **NO-GO** (see PILOT_REPORT) |
| 7 Application integration | Managed MCP client in wirdi-Ai, UI of verified annotations only | Regression, privacy, failure isolation | not started, out of scope so far |

Current state: **0.6.0, local Tajwid candidates.** Quran access, mapping, rule lookup,
candidate analysis, summaries, per-page analysis and local page lookup all work through
stdio. Everything Tajwid is unreviewed. Book A is covered except what [BOOK_A_COVERAGE](BOOK_A_COVERAGE.md)
lists (for example the vowel of a sakin letter before hamzat al-wasl beyond من, the plural
meem and tanween, and the default closed ya). Not covered at all: waqf rules, and the Book B
sections that are not named in [HANDOFF](HANDOFF.md). No network provider, outbound MCP client, RAG or agent is part of
this project.
