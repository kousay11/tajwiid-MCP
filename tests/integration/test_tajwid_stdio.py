"""Real stdio MCP client calls over every Tajwid and source-page tool."""

import asyncio
import json
import shutil
import sys

from conftest import REPO_KNOWLEDGE
from mcp import Client, StdioServerParameters

KAHF = {
    "start": {
        "corpus_id": "wirdi-ai:quranpedia:qalun",
        "corpus_version": "sha256:ece0a2b0efe44d496211c595d0a34f495413bc93f78fba8095a666e2048d1303",
        "numbering_system": "wirdi-ai:qalun-6214",
        "riwaya": "qaloun",
        "tariq": "unspecified",
        "surah": 18,
        "ayah": 45,
    },
    "end_ayah": 52,
}


def params(tmp_path, **env):
    return StdioServerParameters(
        command=sys.executable,
        args=["-m", "wirdi_mcp.server"],
        cwd=tmp_path,
        env={"WIRDI_MCP_LOG_LEVEL": "ERROR", **env},
    )


async def call(client, name, args):
    return await client.call_tool(name, args)


def test_isolation_when_stores_are_absent_or_altered(tmp_path):
    """Missing Quran root, missing knowledge store, altered rule: each fails typed, server lives."""
    altered = tmp_path / "knowledge"
    shutil.copytree(REPO_KNOWLEDGE / "rules", altered / "rules")
    (altered / "sources").mkdir()
    shutil.copy(REPO_KNOWLEDGE / "sources" / "editions.json", altered / "sources" / "editions.json")
    path = altered / "rules" / "iqlab" / "1.json"
    raw = bytearray(path.read_bytes())
    raw[-3] ^= 1
    path.write_bytes(bytes(raw))

    async def run():
        async with (
            asyncio.timeout(30),
            Client(
                params(tmp_path, WIRDI_KNOWLEDGE_ROOT=str(altered), WIRDI_QURAN_SOURCE="none"),
                read_timeout_seconds=10,
            ) as c,
        ):
            tampered = await call(c, "get_tajwid_rule", {"rule_id": "iqlab", "version": "1"})
            assert tampered.structured_content["error"]["code"] == "INTEGRITY_FAILURE"
            intact = await call(c, "get_tajwid_rule", {"rule_id": "idhar_halqi", "version": "1"})
            assert not intact.is_error
            no_quran = await call(
                c,
                "analyze_qaloun_tajwid",
                {"selection": KAHF, "reading_context": {"mode": "waqf"}},
            )
            assert no_quran.structured_content["error"]["code"] == "DATA_UNAVAILABLE"
            absent = await call(
                c, "get_source_page", {"edition_id": "book-a-2010", "page_start": 1, "page_end": 1}
            )
            assert absent.structured_content["error"]["code"] in {"DATA_UNAVAILABLE", "NOT_FOUND"}
            for result in (tampered, no_quran, absent):
                assert str(tmp_path) not in json.dumps(result.structured_content)
            health = await call(c, "health_check", {})
            assert not health.is_error

    asyncio.run(run())


def test_no_knowledge_store_at_all_is_unavailable_not_a_crash(tmp_path):
    async def run():
        async with (
            asyncio.timeout(30),
            Client(
                params(tmp_path, WIRDI_KNOWLEDGE_ROOT=str(tmp_path / "nothing")),
                read_timeout_seconds=10,
            ) as c,
        ):
            result = await call(c, "list_tajwid_rules", {})
            assert result.structured_content["error"]["code"] == "DATA_UNAVAILABLE"
            invalid = await call(
                c, "get_source_page", {"edition_id": "book-a-2010", "page_start": 1, "page_end": 99}
            )
            assert invalid.is_error and invalid.structured_content["error"]["code"] in {
                "INVALID_REFERENCE",
                "DATA_UNAVAILABLE",
            }

    asyncio.run(run())


def test_every_tajwid_tool_over_stdio_on_a_real_passage(tmp_path, real_env):
    async def run():
        async with (
            asyncio.timeout(60),
            Client(params(tmp_path, **real_env), read_timeout_seconds=20) as c,
        ):
            listed = await call(c, "list_tajwid_rules", {})
            assert not listed.is_error and len(listed.structured_content["data"]["rules"]) == 89
            rule = await call(c, "get_tajwid_rule", {"rule_id": "qalqala", "version": "1"})
            data = rule.structured_content["data"]
            assert data["validation_status"] == "unreviewed" and data["evidence"]

            waqf = await call(
                c,
                "analyze_qaloun_tajwid",
                {
                    "selection": KAHF,
                    "reading_context": {"mode": "waqf", "basis": "source_default"},
                    "limit": 25,
                },
            )
            assert not waqf.is_error
            analysis = waqf.structured_content["data"]
            assert analysis["total"] > 25 and analysis["next_offset"] == 25
            assert len(analysis["annotations"]) == 25
            for annotation in analysis["annotations"]:
                assert annotation["status"] == "candidate"
                assert annotation["evidence"][0]["locator"]
                assert annotation["page_refs"]["app_page_start"] in range(1, 560)
                assert annotation["reading_context"] == {
                    "mode": "waqf",
                    "basis": "source_default",
                    "preceding": None,
                    "following": None,
                    "stop_after_word": None,
                }
            assert not any(a["status"] == "scholarly_verified" for a in analysis["annotations"])

            only = await call(
                c,
                "analyze_qaloun_tajwid",
                {
                    "selection": KAHF,
                    "reading_context": {"mode": "waqf"},
                    "rule_ids": ["qalqala"],
                },
            )
            assert {a["rule_id"] for a in only.structured_content["data"]["annotations"]} <= {
                "qalqala"
            }

            wasl = await call(
                c, "analyze_qaloun_tajwid", {"selection": KAHF, "reading_context": {"mode": "wasl"}}
            )
            assert wasl.structured_content["data"]["coverage"] == "partial"
            assert wasl.structured_content["data"]["unresolved"]

            summary = await call(
                c,
                "summarize_tajwid",
                {"surah": 18, "reading_context": {"mode": "waqf"}, "limit": 10},
            )
            data = summary.structured_content["data"]
            assert (
                data["total_ayat"] == 105
                and len(data["per_ayah"]) == 10
                and data["next_offset"] == 10
            )

            page = await call(
                c, "analyze_app_page", {"page": 263, "reading_context": {"mode": "waqf"}}
            )
            data = page.structured_content["data"]
            assert data["pagination_status"] == "verified_against_edition" and data["verses"]

            for bad in (
                ("summarize_tajwid", {"surah": 0, "reading_context": {"mode": "waqf"}}),
                ("analyze_app_page", {"page": 560, "reading_context": {"mode": "waqf"}}),
                (
                    "analyze_qaloun_tajwid",
                    {"selection": KAHF, "reading_context": {"mode": "waqf"}, "limit": 100000},
                ),
                (
                    "analyze_qaloun_tajwid",
                    {"selection": KAHF, "reading_context": {"mode": "waqf"}, "rule_ids": ["nope"]},
                ),
            ):
                result = await call(c, *bad)
                assert result.is_error and result.structured_content["status"] == "error"

    asyncio.run(run())


def test_book_a_families_and_letter_properties_over_stdio(tmp_path, real_env):
    """Madd, hamza, tafkhim and taqlil rules are reachable by family, plus the letter tool."""
    al_imran_1_2 = {**KAHF, "start": {**KAHF["start"], "surah": 3, "ayah": 1}, "end_ayah": 4}

    async def run():
        async with (
            asyncio.timeout(60),
            Client(params(tmp_path, **real_env), read_timeout_seconds=20) as c,
        ):
            for family, expected in (
                ("madd", {"madd_lazim_harfi_muthaqqal", "madd_munfasil", "madd_tabii"}),
                ("hamza", {"hamzat_wasl_article"}),
                ("tafkhim_tarqiq", {"lam_jalala_tafkhim", "alef_tarqiq"}),
                ("imala_taqlil", {"taqlil_tawrat"}),
            ):
                result = await call(
                    c,
                    "analyze_qaloun_tajwid",
                    {
                        "selection": al_imran_1_2,
                        "reading_context": {"mode": "waqf"},
                        "families": [family],
                        "limit": 500,
                    },
                )
                assert not result.is_error, family
                annotations = result.structured_content["data"]["annotations"]
                assert expected <= {a["rule_id"] for a in annotations}, (family, expected)
                assert all(a["status"] == "candidate" and a["evidence"] for a in annotations)
            munfasil = await call(
                c,
                "analyze_qaloun_tajwid",
                {
                    "selection": al_imran_1_2,
                    "reading_context": {"mode": "waqf"},
                    "rule_ids": ["madd_munfasil"],
                },
            )
            first = munfasil.structured_content["data"]["annotations"][0]
            assert first["variants"] == ["2_harakat", "3_harakat", "4_harakat"]
            assert first["rule_id"] == "madd_munfasil" and first["status"] == "candidate"

            letters = await call(c, "get_letter_properties", {"letters": ["ق", "ء"]})
            assert not letters.is_error
            qaf, hamza = letters.structured_content["data"]["letters"]
            assert qaf["makhraj_region"] == "tongue" and "qalqala" in qaf["other_characteristics"]
            assert hamza["makhraj_place"] == "deepest_throat"
            bad = await call(c, "get_letter_properties", {"letters": ["قط"]})
            assert bad.is_error and bad.structured_content["error"]["code"] == "INVALID_REFERENCE"

    asyncio.run(run())
