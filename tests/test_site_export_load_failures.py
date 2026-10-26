"""A site export reports unreadable source files and its partial outcome."""

import os

import pytest

from pyrite.config import KBConfig
from tests._world import build_world


@pytest.mark.parametrize("valid_count", [0, 1])
@pytest.mark.parametrize("broken_count", [1, 2])
def test_site_export_names_each_unreadable_file(tmp_path, valid_count, broken_count):
    world = build_world(tmp_path, kbs=[KBConfig(name="demo", path=tmp_path / "kb")], rest=False)
    try:
        kb = "demo"
        for index in range(valid_count):
            world.add_entry(
                kb, f"---\nid: good-{index}\ntitle: Good {index}\ntype: note\n---\nBody.\n"
            )
        for index in range(broken_count):
            path = world.add_entry(
                kb, f"---\nid: bad-{index}\ntitle: Before\ntype: note\n---\nBody.\n"
            )
            path.write_text(
                f"---\nid: bad-{index}\ntitle: [cannot, load]\ntype: note\n---\nBody.\n"
            )
        result = world.cli("export", "site", "-k", kb, "-o", str(tmp_path / "export"))
        assert result.exit_code == (3 if valid_count else 1), result.output
        for index in range(broken_count):
            assert f"bad-{index}.md" in result.output
        assert "title must be a string, got a list" in result.output
        assert "entr(ies)" not in result.output
        assert f"{broken_count} {'entry' if broken_count == 1 else 'entries'}" in result.output
        assert len(list((tmp_path / "export").rglob("good-*.md"))) == valid_count
    finally:
        world.close()


@pytest.mark.skipif(not hasattr(os, "mkfifo"), reason="requires a FIFO")
@pytest.mark.timeout(15)  # a FIFO must be reported, never waited on
def test_site_export_reports_a_non_regular_file(tmp_path):
    world = build_world(tmp_path, kbs=[KBConfig(name="demo", path=tmp_path / "kb")], rest=False)
    try:
        os.mkfifo(world.kb_path("demo") / "pipe.md")
        result = world.cli("export", "site", "-k", "demo", "-o", str(tmp_path / "export"))
        assert result.exit_code == 1, result.output
        assert "pipe.md: Not a regular file" in result.output
    finally:
        world.close()
