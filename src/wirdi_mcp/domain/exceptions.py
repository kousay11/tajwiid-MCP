"""Safe domain failures; never carry paths, credentials or raw exception text."""

from wirdi_mcp.domain.models import DomainError


class KnowledgeError(Exception):
    def __init__(self, code: str, message: str):
        self.error = DomainError(code=code, message=message)
        super().__init__(message)
