# MCP tools — local Tajwid foundation

The stdio server exposes six read-only tools:

- `health_check`
- `get_qaloun_passage`
- `resolve_source_mapping`
- `get_tajwid_rule`
- `analyze_qaloun_tajwid`
- `get_tajwid_explanation`

There is no outbound MCP client, HTTP provider, network fallback or external
scholarly search. All tools use closed-world contracts and return structured
success/error envelopes.

## Local data tools

`get_qaloun_passage` reads unchanged Qaloun ayat from the explicitly configured,
checksum-pinned Wirdi AI source files. `resolve_source_mapping` reuses the
verified local mapping authority. Both require explicit corpus identity and
fail closed for missing, altered or unsupported source data.

## Local Tajwid tools

The three Tajwid tools are registered so the MCP interface can be tested before
the engine is integrated into the main application:

| Tool | Purpose | Current state |
| --- | --- | --- |
| `get_tajwid_rule` | Read a reviewed local rule by ID and version | Returns `UNSUPPORTED_CAPABILITY` until local rules are loaded |
| `analyze_qaloun_tajwid` | Analyze a bounded passage with explicit Wasl/Waqf context | Returns `UNSUPPORTED_CAPABILITY` until a detector is available |
| `get_tajwid_explanation` | Read a reviewed Arabic explanation | Returns `UNSUPPORTED_CAPABILITY` until annotations exist |

An unavailable analysis is never represented as an empty successful result. The
absence of a rule or detector is explicit, so a future local implementation can
be added without changing the MCP transport or silently making scholarly claims.

## Shared response contract

```text
Success[T] = {
  schema_version: "1.0",
  status: "ok",
  data: T,
  provenance: [...],
  validation_status: "...",
  warnings: [...]
}

Failure = {
  schema_version: "1.0",
  status: "error",
  error: {
    code: "...",
    message: "...",
    retryable: false
  }
}
```

The exact Pydantic contracts are in `src/wirdi_mcp/tools/contracts.py`; the
local Tajwid registration is in `src/wirdi_mcp/tools/tajwid.py`. Real stdio
tests validate discovery, schemas, local Qaloun calls and explicit Tajwid
unavailability.
