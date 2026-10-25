"""An optional epic filter resolves only among KBs the caller can read."""

import pytest

from pyrite.config import KBConfig
from tests._world import build_world


@pytest.fixture
def world(tmp_path):
    result = build_world(
        tmp_path,
        kbs=[KBConfig(name=n, path=tmp_path / n, kb_type="software") for n in ("alpha", "beta")],
        rest=False,
    )
    for kb in ("alpha", "beta"):
        result.add_entry(
            kb,
            "---\nid: epic\ntype: backlog_item\ntitle: Epic\nkind: epic\n"
            "links:\n  - target: child\n    relation: has_subtask\n---\n\nAn epic.\n",
        )
        result.add_entry(
            kb, "---\nid: child\ntype: backlog_item\ntitle: Child\nkind: feature\n---\n\nWork.\n"
        )
    try:
        yield result
    finally:
        result.close()


@pytest.mark.parametrize("kb", [None, "", " "])
def test_epic_resolves_in_the_only_readable_kb(world, kb):
    args = {"epic": "epic"}
    if kb is not None:
        args["kb_name"] = kb
    result = world.mcp()._dispatch_tool("sw_backlog", args, readable_kbs={"alpha"})

    assert "error" not in result, result
    assert [(i["kb_name"], i["id"]) for i in result["items"]] == [("alpha", "child")]


@pytest.mark.parametrize(("epic", "code"), [("epic", "AMBIGUOUS"), ("absent", "ENTRY_NOT_FOUND")])
def test_epic_filter_refuses_an_ambiguous_or_missing_id(world, epic, code):
    result = world.mcp()._dispatch_tool("sw_backlog", {"epic": epic})

    assert result["error_code"] == code, result
    if code == "AMBIGUOUS":
        assert result["candidate_kbs"] == ["alpha", "beta"]


@pytest.mark.control(reason="listing without an epic and with a named KB keeps working")
def test_no_epic_and_named_kb_keep_their_scope(world):
    server = world.mcp()
    all_items = server._dispatch_tool("sw_backlog", {}, readable_kbs={"alpha"})
    assert {i["id"] for i in all_items["items"]} == {"epic", "child"}
    named = server._dispatch_tool("sw_backlog", {"epic": "epic", "kb_name": "beta"})
    assert [(i["kb_name"], i["id"]) for i in named["items"]] == [("beta", "child")]
