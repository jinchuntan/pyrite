"""Every link writer discloses an undeclared relation without changing it."""

import json

import pytest

from pyrite.config import KBConfig
from tests._world import build_world


@pytest.mark.parametrize("surface", ["cli", "bidi", "create", "bulk", "mcp"])
@pytest.mark.parametrize(
    "relation",
    [
        "typo_relation",
        pytest.param(
            "related_to", marks=pytest.mark.control(reason="declared relations already work")
        ),
        pytest.param(
            "related", marks=pytest.mark.control(reason="legacy relation aliases already work")
        ),
    ],
)
def test_link_writers_report_undeclared_relations(tmp_path, surface, relation):
    world = build_world(tmp_path, kbs=[KBConfig(name="demo", path=tmp_path / "kb")], rest=False)
    try:
        for entry_id in ["source", "target"]:
            world.add_entry(
                "demo", f"---\nid: {entry_id}\ntitle: {entry_id}\ntype: note\n---\nBody.\n"
            )
        if surface == "mcp":
            body = world.mcp()._dispatch_tool(
                "kb_link",
                {
                    "source_id": "source",
                    "source_kb": "demo",
                    "target_id": "target",
                    "relation": relation,
                },
            )
            warnings = body.get("warnings", [])
        else:
            if surface == "create":
                args = ("create", "-k", "demo", "--title", "New", "--link", f"target:{relation}")
            elif surface == "bulk":
                spec = tmp_path / "links.yaml"
                spec.write_text(f"- source: source\n  target: target\n  relation: {relation}\n")
                args = ("links", "bulk-create", str(spec), "-k", "demo")
            else:
                args = ("link", "source", "target", "-k", "demo", "-r", relation)
                if surface == "bidi":
                    args += ("--bidi",)
            result = world.cli(*args)
            assert result.exit_code == 0, result.output
            body = json.loads(result.stdout)
            warnings = (
                body["results"][0].get("warnings", [])
                if surface == "bulk"
                else body.get("warnings", [])
            )
        if relation == "typo_relation":
            assert any(
                w.get("code") == "UNDECLARED_RELATION"
                and w["relation"] == relation
                and "related_to" in w["declared"]
                for w in warnings
            )
            qa = json.loads(world.cli("qa", "validate", "demo").stdout)
            assert any(i["rule"] == "undeclared_relation" for i in qa["issues"])
        else:
            assert not warnings
    finally:
        world.close()
