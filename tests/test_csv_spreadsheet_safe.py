"""CSV text escaping is opt-in and covers every serializer table shape."""

import ast
import csv
import io
from pathlib import Path

import pytest

from pyrite.config import KBConfig
from pyrite.formats import format_response, negotiate_format
from tests._world import build_world

SHAPES = ["results", "entries", "events", "tags", "kbs", "single", "projected", "fallback"]


@pytest.mark.parametrize("prefix", ["=", "+", "-", "@", "\t", "\r", "\n", "＝"])
@pytest.mark.parametrize("shape", SHAPES)
def test_safe_csv_escapes_each_table_shape(prefix, shape):
    value = prefix + '1,"two"\nnext'
    kwargs = {}
    if shape in ["single", "fallback", "projected"]:
        data = {"title": value}
        if shape == "single":
            kwargs["single_entry"] = True
        elif shape == "projected":
            data = {"results": [data]}
            kwargs["fields"] = ["title"]
    else:
        data = {shape: [{"id": "item", "title": value, "tag": value, "name": value}]}
    raw, _ = format_response(data, "csv", **kwargs)
    safe, media = format_response(data, "csv-safe", **kwargs)
    assert media == "text/csv"
    raw_rows = list(csv.reader(io.StringIO(raw)))
    safe_rows = list(csv.reader(io.StringIO(safe)))
    assert any(value in row for row in raw_rows)
    assert safe_rows == [
        ["'" + cell if cell == value else cell for cell in row] for row in raw_rows
    ]
    assert format_response(data, "csv", **kwargs)[0] == raw


@pytest.mark.parametrize(
    "route",
    ["/api/search?q=item", "/api/entries?kb=demo", "/api/entries/export?kb=demo&format=csv"],
)
def test_rest_csv_is_raw_until_the_request_opts_in(tmp_path, route):
    world = build_world(tmp_path, kbs=[KBConfig(name="demo", path=tmp_path / "kb")])
    try:
        world.add_entry("demo", '---\nid: item\ntitle: "=1+1"\ntype: note\n---\nBody item.\n')
        raw = world.client.get(route, headers={"Accept": "text/csv"})
        safe_route = (
            route.replace("format=csv", "format=csv-safe")
            if "/export" in route
            else route + "&csv_safe=true"
        )
        safe = world.client.get(safe_route, headers={"Accept": "text/csv"})
        assert raw.status_code == safe.status_code == 200
        assert any("=1+1" in row for row in csv.reader(io.StringIO(raw.text)))
        assert any("'=1+1" in row for row in csv.reader(io.StringIO(safe.text)))
    finally:
        world.close()


@pytest.mark.control(reason="Accept text/csv continues to select the raw format")
def test_media_type_negotiation_keeps_raw_csv():
    assert negotiate_format("text/csv") == "csv"


@pytest.mark.parametrize(
    "args",
    [
        ("get", "item", "-k", "demo"),
        ("list-entries", "-k", "demo"),
        ("search", "item", "-k", "demo"),
    ],
)
def test_cli_can_select_safe_csv(tmp_path, args):
    world = build_world(tmp_path, kbs=[KBConfig(name="demo", path=tmp_path / "kb")], rest=False)
    try:
        world.add_entry("demo", '---\nid: item\ntitle: "=1+1"\ntype: note\n---\nBody item.\n')
        result = world.cli(*args, "--format", "csv-safe")
        assert result.exit_code == 0, result.output
        assert any("'=1+1" in row for row in csv.reader(io.StringIO(result.stdout)))
    finally:
        world.close()


def test_safe_csv_escapes_headers_and_signed_numbers():
    raw = {"=header": "-2", "ordinary": {"nested": "=1"}}
    safe, _ = format_response(raw, "csv-safe", single_entry=True)
    rows = list(csv.reader(io.StringIO(safe)))
    assert rows[0] == ["'=header", "ordinary"]
    assert rows[1][0] == "'-2"
    import json

    assert json.loads(rows[1][1]) == {"nested": "=1"}


# Every legacy CSV-capable CLI declaration (the shared format option is JSON/YAML/Rich).
CLI_CSV_EMITTERS = {
    ("pyrite/cli/__init__.py", "auth_status"),
    ("pyrite/cli/__init__.py", "auth_whoami"),
    ("pyrite/cli/__init__.py", "list_kbs"),
    ("pyrite/cli/browse_commands.py", "backlinks_cmd"),
    ("pyrite/cli/browse_commands.py", "batch_read"),
    ("pyrite/cli/browse_commands.py", "list_entries_cmd"),
    ("pyrite/cli/browse_commands.py", "orient_kb"),
    ("pyrite/cli/browse_commands.py", "recent_entries"),
    ("pyrite/cli/browse_commands.py", "tags_cmd"),
    ("pyrite/cli/browse_commands.py", "timeline"),
    ("pyrite/cli/collection_commands.py", "list_collections"),
    ("pyrite/cli/collection_commands.py", "query_entries"),
    ("pyrite/cli/entry_commands.py", "get_entry"),
    ("pyrite/cli/extension_commands.py", "extension_init"),
    ("pyrite/cli/extension_commands.py", "extension_install"),
    ("pyrite/cli/extension_commands.py", "extension_list"),
    ("pyrite/cli/extension_commands.py", "extension_uninstall"),
    ("pyrite/cli/index_commands.py", "index_health"),
    ("pyrite/cli/index_commands.py", "index_stats"),
    ("pyrite/cli/init_command.py", "init_kb"),
    ("pyrite/cli/kb_commands.py", "kb_discover"),
    ("pyrite/cli/kb_commands.py", "kb_health"),
    ("pyrite/cli/kb_commands.py", "kb_list"),
    ("pyrite/cli/kb_commands.py", "kb_reindex"),
    ("pyrite/cli/kb_commands.py", "kb_validate"),
    ("pyrite/cli/kb_commands.py", "schema_add_type"),
    ("pyrite/cli/kb_commands.py", "schema_remove_type"),
    ("pyrite/cli/kb_commands.py", "schema_set"),
    ("pyrite/cli/kb_commands.py", "schema_show"),
    ("pyrite/cli/qa_commands.py", "qa_assess"),
    ("pyrite/cli/qa_commands.py", "qa_compact"),
    ("pyrite/cli/qa_commands.py", "qa_stale"),
    ("pyrite/cli/qa_commands.py", "qa_status"),
    ("pyrite/cli/qa_commands.py", "qa_validate"),
    ("pyrite/cli/repo_commands.py", "repo_list_extended"),
    ("pyrite/cli/repo_commands.py", "repo_status"),
    ("pyrite/cli/search_commands.py", "search"),
    ("pyrite/read_cli.py", "backlinks_cmd"),
    ("pyrite/read_cli.py", "get_entry"),
    ("pyrite/read_cli.py", "list_kbs"),
    ("pyrite/read_cli.py", "tags_cmd"),
    ("pyrite/read_cli.py", "timeline"),
}


def _csv_declarations():
    root = Path(__file__).resolve().parents[1]
    found = {}
    for path in [*(root / "pyrite/cli").glob("*.py"), root / "pyrite/read_cli.py"]:
        for fn in ast.walk(ast.parse(path.read_text())):
            if not isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            for default in [*fn.args.defaults, *fn.args.kw_defaults]:
                if default is None:
                    continue
                for node in ast.walk(default):
                    if (
                        isinstance(node, ast.Constant)
                        and isinstance(node.value, str)
                        and "Output format" in node.value
                        and "csv" in node.value
                    ):
                        found[(str(path.relative_to(root)), fn.name)] = node.value
    return found


def test_csv_command_inventory_matches_source():
    assert set(_csv_declarations()) == CLI_CSV_EMITTERS


@pytest.mark.parametrize("emitter", sorted(CLI_CSV_EMITTERS))
def test_every_csv_command_advertises_the_opt_in(emitter):
    assert "csv-safe" in _csv_declarations()[emitter]
