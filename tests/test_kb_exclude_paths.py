"""Configured exclusions apply to the shared KB walk and its consumers."""

import json

import pytest

from pyrite.config import KBConfig
from pyrite.storage.repository import KBRepository
from tests._world import build_world


@pytest.mark.parametrize(
    "surface", ["files", "entries", "count", "index", "qa", "export", "schema"]
)
def test_excluded_files_do_not_enter_kb_walks(tmp_path, surface):
    root = tmp_path / "kb"
    root.mkdir()
    (root / "kb.yaml").write_text("name: demo\nexclude: ['drafts/**', '*.scratch.md']\n")
    for name in ["keep.md", "drafts/skip.md", "nested/skip.scratch.md"]:
        path = root / name
        path.parent.mkdir(exist_ok=True)
        path.write_text(f"---\nid: {path.stem}\ntitle: {path.stem}\ntype: note\n---\nBody.\n")
    world = build_world(tmp_path, kbs=[KBConfig(name="demo", path=root)], rest=False)
    try:
        repo = KBRepository(world.config.get_kb("demo"))
        if surface == "files":
            assert [p.name for p in repo.list_files()] == ["keep.md"]
        elif surface == "entries":
            assert [e.id for e, _ in repo.list_entries()] == ["keep"]
        elif surface == "count":
            assert repo.count() == 1
        elif surface == "index":
            assert [e["id"] for e in world.db.list_entries(kb_name="demo")] == ["keep"]
        elif surface == "qa":
            result = world.cli("qa", "validate", "demo")
            assert {i["entry_id"] for i in json.loads(result.stdout)["issues"]} <= {"keep", ""}
        elif surface == "schema":
            from pyrite.cli.schema_commands import _collect_md_files

            assert _collect_md_files([root]) == [root / "keep.md"]
        else:
            output = tmp_path / "export"
            result = world.cli("export", "site", "-k", "demo", "-o", str(output))
            assert result.exit_code == 0, result.output
            assert not list(output.rglob("skip*.md"))
    finally:
        world.close()
