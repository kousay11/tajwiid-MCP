# Local Tajwid roadmap

The project is intentionally local-first. The MCP server uses stdio and reads
only the explicitly configured, checksum-pinned Qaloun source files.

| Phase | Scope | Gate |
| --- | --- | --- |
| 1 — Foundation | Packaging, MCP stdio transport, diagnostics and typed contracts | Unit tests, protocol smoke test and lint pass |
| 2 — Quran tools | Read-only Qaloun access and existing mapping authority | Integrity checks and mapping conformance pass |
| 3 — Tajwid knowledge | Audited local sources, licenses, review records and first rules | Qualified review and versioned local artifact |
| 4 — Tajwid engine | Deterministic detectors, context handling and candidate annotations | Positive, negative, exception and Wasl/Waqf fixtures pass |
| 5 — Local integration | Stable backend client and UI-facing adapters in the initial application | Regression, privacy and failure-isolation tests pass |

Current state: **local Tajwid foundation (0.4.0)**. Quran access and mapping
are operational. The three Tajwid tools are registered and tested through MCP,
but return `UNSUPPORTED_CAPABILITY` until reviewed local rules and detectors are
implemented. No network provider, outbound MCP client, RAG or agent is part of
this project.
