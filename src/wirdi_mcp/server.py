"""Local stdio MCP server with diagnostics and read-only public Quran tools."""

import logging
import sys

from mcp.server import MCPServer
from mcp.types import ToolAnnotations

from wirdi_mcp import __version__
from wirdi_mcp.config import Settings
from wirdi_mcp.knowledge.pages import PageStore
from wirdi_mcp.knowledge.registry import RuleRegistry
from wirdi_mcp.quran.source import PublicSourceRepository
from wirdi_mcp.tajwid.service import TajwidService
from wirdi_mcp.tools.diagnostics import HealthReport
from wirdi_mcp.tools.quran import register_quran_tools
from wirdi_mcp.tools.tajwid import register_tajwid_tools


def create_server(settings: Settings | None = None) -> MCPServer:
    settings = settings or Settings.from_env()
    server = MCPServer(
        "wirdi-mcp",
        version=__version__,
        log_level=settings.log_level,
        instructions=(
            "Read-only Qaloun access and source mapping require configured checksum-pinned files. "
            "Review-required mappings are unsafe for retrieval. Tajwid rules, candidate "
            "annotations and source-page lookup are local-only and unreviewed: no annotation is "
            "scholarly verified and explanations are unavailable. "
            "Corpus tariq is unspecified, not independently attested."
        ),
    )

    @server.tool(
        annotations=ToolAnnotations(
            read_only_hint=True,
            destructive_hint=False,
            idempotent_hint=True,
            open_world_hint=False,
        )
    )
    def health_check() -> HealthReport:
        """Report process readiness and configuration, without accessing source or private data."""
        state = "configured_unchecked" if settings.wirdi_ai_root is not None else "not_configured"
        return HealthReport(
            quran_data=state,
            mapping=state,
        )

    repository = PublicSourceRepository(settings.wirdi_ai_root)
    registry = RuleRegistry(settings.knowledge_root)
    register_quran_tools(server, repository)
    register_tajwid_tools(
        server, repository, TajwidService(repository, registry), PageStore(registry)
    )
    return server


def main() -> None:
    try:
        settings = Settings.from_env()
    except ValueError as exc:
        # Only the fixed configuration error is shown, never environment contents.
        print(str(exc), file=sys.stderr)
        raise SystemExit(2) from None
    logging.basicConfig(
        level=settings.log_level,
        stream=sys.stderr,
        format="%(levelname)s %(name)s: %(message)s",
    )
    create_server(settings).run(transport="stdio")


if __name__ == "__main__":
    main()
