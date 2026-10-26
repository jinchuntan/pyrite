"""Malformed metadata stays in the task file while unrelated edits work."""

import json

import pytest

from pyrite.config import KBConfig
from pyrite.storage.repository import KBRepository
from tests._world import build_world


@pytest.mark.parametrize("value", ["abc", "[one, two]", "false", "0", "null"])
def test_non_mapping_task_metadata_is_reported_and_preserved(tmp_path, value):
    world = build_world(tmp_path, kbs=[KBConfig(name="demo", path=tmp_path / "kb")], rest=False)
    try:
        original = f"---\nid: item\ntype: task\ntitle: Before\nmetadata: {value} # keep this\ncustom: present\n---\nBody.\n"
        path = world.add_entry("demo", original)
        entry = KBRepository(world.config.get_kb("demo")).load("item")
        assert entry.entry_type == "task"
        assert entry.to_frontmatter()["metadata"] == entry._source_frontmatter["metadata"]
        get = world.cli("get", "item", "-k", "demo")
        assert get.exit_code == 0, get.output
        assert json.loads(get.stdout)["entry_type"] == "task"
        qa = world.cli("qa", "validate", "demo")
        findings = json.loads(qa.stdout)["issues"]
        assert any(i.get("field") == "metadata" and i["severity"] == "warning" for i in findings)
        update = world.cli("update", "item", "-k", "demo", "--title", "After")
        assert update.exit_code == 0, update.output
        assert "metadata" in str(json.loads(update.stdout).get("warnings", []))
        assert path.read_text() == original.replace("title: Before", "title: After")
    finally:
        world.close()
