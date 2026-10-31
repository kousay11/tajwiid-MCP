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
        "WIRDI_AI_ROOT": "/absolute/path/wirdi-Ai",
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

The current analysis response is an explicit
`UNSUPPORTED_CAPABILITY` error until local rules and a detector are loaded.
The application must preserve that distinction and must not display it as an
empty or verified Tajwid result.

## Boundaries

- Send only public passage selections and explicit reading context.
- Keep user accounts, sessions, progress and private notes in the application.
- Treat the Qaloun source and mapping identities as part of every request.
- Keep the local MCP process on stdio; no public listener is enabled.
- Integrate only after the local MCP tests and real-source checks pass.

The mapping authority remains reusable through its existing read-only adapter.
The Tajwid engine will be added behind the local tool contracts, so the
application client does not need to change when reviewed rules become available.
