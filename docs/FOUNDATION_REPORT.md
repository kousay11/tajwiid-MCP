# Foundation completion report

Completed 2026-10-30 in `/home/najjar/Documents/Me/wirdi-mcp`.
Scope: architecture and Phase 1 foundation only.

## Outcome and decisions

The installed 0.1.0 package runs an official Python MCP SDK 2.3.0 server over
stdio and advertises only `health_check`. No network listener is started.
Inbound MCP handlers are separated from typed domain records, a read-only Quran
port, an existing-mapper authority port, and outbound provider contracts.
There are no provider connections or knowledge service implementations.

The seven proposed tools have typed input/result contracts and documented
provenance, error handling, validation, dependencies and phase gates:
`get_qaloun_passage`, `resolve_source_mapping`, `get_tajwid_rule`,
`analyze_qaloun_tajwid`, `get_tajwid_explanation`, `search_scholarly_sources`,
and `get_provider_capabilities`. None is registered as an operational tool.

Every Quran reference requires corpus/version/numbering and riwaya/tariq
identity. Future exact-byte hashing and manifest admission preserve immutable
text. The existing verified mapper will be reused through a shared package,
read-only service or immutable reviewed artifact; no mapping algorithm was
duplicated. SQLite is recommended for an initial small read-only knowledge
artifact, with PostgreSQL deferred until concurrent editorial/service needs
justify its operations. No database was created.

The Tajwid design distinguishes scholarly rules, deterministic detectors,
candidate occurrences, passage-specific scholarly approvals and Arabic
explanations. It requires Qaloun/Abu Nashit scope and explicit Wasl/Waqf context.
Pydantic validation alone cannot establish scholarly truth. No detection rule,
scientific annotation, explanation generator, RAG pipeline or LLM agent exists.

Planned external adapters are Quran MCP, Tafsir MCP and Quran Search Engine MCP.
Their documentation and selected source were reviewed; no external MCP tool was
called. The provider report records Tafsir's inconsistent published tool counts
and keeps Qaloun compatibility unresolved pending audit. Optional providers
cannot block local tools or replace authoritative local text.

Wirdi AI integration will use a backend-owned stdio client lifecycle locally,
with authenticated Streamable HTTP as a later deployment option. Existing
Quran.ai retrieval remains behind a migration flag and preserves attribution.
Users, reading progress and authentication stay in Wirdi AI. The existing
application repository was not inspected or modified.

All seven roadmap phases and release gates are documented. The next milestone
is Phase 2: authorize and audit the existing manifest/mapping interface, freeze
reference/boundary semantics, and implement read-only adapters with conformance
tests before exposing passage and mapping tools.

## Exact authored file manifest and final structure

33 project files were created:

```text
wirdi-mcp/
├── .env.example
├── .gitignore
├── README.md
├── pyproject.toml
├── docs/
│   ├── ARCHITECTURE.md
│   ├── DECISIONS.md
│   ├── FOUNDATION_REPORT.md
│   ├── INTEGRATION.md
│   ├── MCP_TOOLS.md
│   ├── PROVIDERS.md
│   ├── ROADMAP.md
│   └── TAJWID_ENGINE.md
├── knowledge/
│   ├── rules/README.md
│   └── sources/README.md
├── src/wirdi_mcp/
│   ├── __init__.py
│   ├── config.py
│   ├── server.py
│   ├── domain/
│   │   ├── __init__.py
│   │   ├── models.py
│   │   └── ports.py
│   ├── knowledge/
│   │   ├── __init__.py
│   │   └── models.py
│   ├── mapping/
│   │   ├── __init__.py
│   │   └── adapter.py
│   ├── providers/
│   │   ├── __init__.py
│   │   └── base.py
│   └── tools/
│       ├── __init__.py
│       ├── contracts.py
│       └── diagnostics.py
└── tests/
    ├── fixtures/README.md
    ├── integration/test_stdio.py
    └── unit/
        ├── test_config.py
        └── test_contracts.py
```

Generated, ignored local artifacts: `.venv/`, Python bytecode caches,
`.pytest_cache/`, `.ruff_cache/` and
`dist/wirdi_mcp-0.1.0-py3-none-any.whl`. The wheel contains 15 package source
files and a `wirdi-mcp = wirdi_mcp.server:main` console entry point. Existing
managed `.agents`, `.aws`, `.codex` and `.git` directories were left untouched.
The initial `git status` reported that the directory was not a Git repository;
no repository initialization or commit was attempted.

## Verification evidence

| Check | Result |
| --- | --- |
| Full offline test suite | **14 passed** in 1.62 seconds outside the execution sandbox |
| Real stdio subprocess protocol smoke | Passed: negotiation, tool discovery, read-only annotation/output schema, diagnostic call and rejection of unavailable Tajwid tool |
| Structural integrity contracts | Passed: required corpus identity, rejection of Hafs/unknown path and boolean verse IDs, bounded selections, annotation review IDs and seven JSON-schema pairs |
| Configuration | Passed: environment validation and safe stderr-only startup failure |
| Ruff lint | Passed |
| Ruff formatting | Passed |
| `pip check` | No broken requirements |
| Bytecode compilation | Passed |
| Wheel build and entry-point inspection | Passed |
| Local Markdown links | Checked after this report was created |
| External provider MCP calls | **Not performed** |
| Quran corpus / scientific rule validation | **Not performed; data not present** |

The first sandboxed MCP smoke run timed out during connection setup while 13
other tests passed. A raw JSON-RPC subprocess probe also timed out inside the
sandbox. The unchanged smoke test passed outside the sandbox, then the full
suite passed there. The sandbox-specific I/O limitation was not worked around
by changing the server or weakening the test. On a normal Ubuntu environment,
use the documented commands; if this execution sandbox is used, run the stdio
test through its authorized unsandboxed execution mechanism.

Tested environment: Python 3.12.3, `mcp==2.3.0`, `mcp-types==2.3.0`,
`pydantic==2.14.2`, `pytest==9.2.0`, `ruff==0.17.3`, `hatchling==1.33.0`.
The SDK is exactly pinned; other bounded dependencies are not a deployment lock.

## Setup and verification commands executed

Executed from the project directory unless stated otherwise. Shell inspection
also used `pwd`, `ls -la`, `rg --files`, `cat` for the supplied brief, and reads
of applicable ancestor `AGENTS.md` paths (none found). The initial directory
contained only the managed empty directories listed above. Package/API inspection
used Python `inspect.signature`, `importlib.metadata.version`, module discovery,
and read-only `rg`/`sed` on the installed SDK.

```bash
python3 --version
python3 -m pip --version
command -v uv
git status --short
python3 -m venv .venv
.venv/bin/python -m pip index versions mcp
.venv/bin/python -m pip --no-cache-dir index versions mcp --retries 0 --timeout 15
.venv/bin/python -m pip --no-cache-dir install 'mcp==2.3.0' 'pytest>=8,<10' 'ruff>=0.14,<1' 'hatchling>=1.27,<2'
.venv/bin/python -m pip install --no-build-isolation --no-deps -e .
.venv/bin/python -m pip --no-cache-dir install -e '.[dev]'
.venv/bin/ruff check --fix .
.venv/bin/ruff format .
.venv/bin/ruff check .
.venv/bin/ruff format --check .
.venv/bin/ruff check --show-files .
.venv/bin/python -m pytest -q
.venv/bin/python -m pytest tests/integration/test_stdio.py -q
.venv/bin/python -m pip check
.venv/bin/python -m hatchling build -t wheel
.venv/bin/python -m compileall -q src tests
```

The first package-index attempts could not resolve DNS inside the sandbox;
authorized network execution succeeded. The initial no-build-isolation editable
install lacked Hatchling's `editables` build dependency; the standard isolated
editable install then succeeded. Initial lint findings were corrected and all
final checks above passed. No global package install was performed.

Additional read-only Python probes inspected wheel members and entry points,
checked relative Markdown links, generated all proposed tool schemas, and sent
synthetic JSON-RPC initialization messages while diagnosing the sandbox timeout.
No probes retrieved Quran text, scholarly content over MCP, or personal data.
Public provider/SDK documentation was fetched through web/GitHub read tools;
supporting source links and the exact research scope are in the relevant docs.
