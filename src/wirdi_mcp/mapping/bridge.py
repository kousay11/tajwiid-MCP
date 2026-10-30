"""Dependency binding for the unchanged, checksum-pinned Wirdi AI resolver.

This is a deliberately limited read interface, not an SQL implementation. The
mapper, schemas and normalizer are compiled from verified original bytes. No
application imports, private records, database connections or bytecode writes.
"""

import builtins
import unicodedata
from dataclasses import dataclass
from functools import lru_cache
from types import SimpleNamespace

from wirdi_mcp.quran.source import SourceAyah


class _Column:
    def __init__(self, name: str):
        self.name = name

    def __eq__(self, value):
        return self.name, value


class _AyahType:
    edition_id = _Column("edition_id")
    surah = _Column("surah")


class _QuranEditionType:
    pass


@dataclass(frozen=True)
class _Select:
    predicates: tuple = ()

    def where(self, *predicates):
        if (
            len(predicates) != 2
            or {p[0] for p in predicates} != {"edition_id", "surah"}
            or dict(predicates)["edition_id"] not in {"qalun", "hafs"}
            or type(dict(predicates)["surah"]) is not int
        ):
            raise RuntimeError("Unsupported authority query")
        return _Select(tuple(predicates))


def _select(model):
    if model is not _AyahType:
        raise RuntimeError("Unsupported authority entity")
    return _Select()


class ReadOnlyAuthorityView:
    """Fresh row objects per read prevent mutations reaching the source records."""

    def __init__(self, rows: dict[str, tuple[SourceAyah, ...]], editions: dict):
        self.rows = rows
        self.editions = editions

    def get(self, model, edition):
        if model is not _QuranEditionType or edition not in {"qalun", "hafs"}:
            raise RuntimeError("Unsupported authority lookup")
        return SimpleNamespace(**self.editions[edition]) if edition in self.editions else None

    def scalars(self, query):
        if not isinstance(query, _Select) or not query.predicates:
            raise RuntimeError("Unsupported authority query")
        where = dict(query.predicates)
        return tuple(
            SimpleNamespace(number=r.number, number_in_hafs=list(r.links), text=r.text)
            for r in self.rows[where["edition_id"]]
            if r.surah == where["surah"]
        )

    def select_qaloun(self, surah: int, lo: int, hi: int):
        rows = self.scalars(
            _select(_AyahType).where(
                _AyahType.edition_id == "qalun",
                _AyahType.surah == surah,
            )
        )
        return [row for row in rows if lo <= row.number <= hi]


@lru_cache(maxsize=1)
def bind_authority(mapper: bytes, arabic: bytes, schemas: bytes):
    """Caller verifies all hashes before reaching this compiler; no importlib/pyc."""
    schema_ns = {"__name__": "wirdi_mcp.mapping._authority_schemas"}
    exec(compile(schemas, "<pinned-wirdi-schemas>", "exec"), schema_ns)
    arabic_ns = {"__name__": "wirdi_mcp.mapping._authority_arabic"}
    exec(compile(arabic, "<pinned-wirdi-arabic>", "exec"), arabic_ns)
    bindings = {
        ("unicodedata", 0): unicodedata,
        ("sqlalchemy", 0): SimpleNamespace(select=_select),
        ("models", 2): SimpleNamespace(Ayah=_AyahType, QuranEdition=_QuranEditionType),
        ("schemas", 2): SimpleNamespace(
            MappingOut=schema_ns["MappingOut"],
            PassageReference=schema_ns["PassageReference"],
        ),
        ("arabic", 1): SimpleNamespace(normalize=arabic_ns["normalize"]),
    }

    def authority_import(name, globals=None, locals=None, fromlist=(), level=0):
        if (name, level) not in bindings:
            raise ImportError("Unsupported authority dependency")
        return bindings[name, level]

    namespace = {
        "__name__": "wirdi_mcp.mapping._authority",
        "__builtins__": {**vars(builtins), "__import__": authority_import},
    }
    exec(compile(mapper, "<pinned-wirdi-mapper>", "exec"), namespace)
    return namespace["resolve"]
