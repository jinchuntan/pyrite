"""CSV text escaping is opt-in and covers every serializer table shape."""

import csv
import io

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
