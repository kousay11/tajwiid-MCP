# Initial application integration

This project is a standalone local MCP server. During development, keep it
separate from the initial application and test the complete stdio contract
first. The application can later launch the same executable as a managed MCP
client without copying the Quran or Tajwid logic.

## Local client lifecycle

Use an absolute executable path and keep the client alive for the application
lifespan rather than creating a process for every request:

```python
from mcp import Client, StdioServerParameters

params = StdioServerParameters(
    command="/absolute/path/wirdi-mcp/.venv/bin/wirdi-mcp",
    env={
        "WIRDI_MCP_LOG_LEVEL": "WARNING",
    },
)

async with Client(params, read_timeout_seconds=5) as client:
    tools = await client.list_tools()
    result = await client.call_tool(
        "analyze_qaloun_tajwid",
        {
            "selection": selection,
            "reading_context": {"mode": "wasl"},
        },
    )
```

`analyze_qaloun_tajwid` now returns **candidate** annotations (status `candidate`,
unreviewed, with book and page citations and the app's 559-page span). The application
must show them as unreviewed, or not at all: nothing is scholarly verified and
`get_tajwid_explanation` still returns `UNSUPPORTED_CAPABILITY`. It must also preserve
the difference between an empty result, a `partial` coverage with `unresolved` positions,
and a typed error (`DATA_UNAVAILABLE`, `INTEGRITY_FAILURE`); none of them means "the passage
has no Tajwid rule". Integration into the application is not started.

## Boundaries

- Send only public passage selections and explicit reading context.
- Keep user accounts, sessions, progress and private notes in the application.
- Treat the Qaloun source and mapping identities as part of every request.
- Keep the local MCP process on stdio; no public listener is enabled.
- Integrate only after the local MCP tests and real-source checks pass.

The mapping authority remains reusable through its existing read-only adapter.
Reviewed validation records, when they exist, will be added behind the same tool
contracts, so the application client will not need to change.
