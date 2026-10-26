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


@pytest.mark.parametrize("pattern", ["drafts", "drafts/", "drafts/**", "**/drafts/**"])
def test_exclusions_cover_collection_files_and_nested_directories(tmp_path, pattern):
    (tmp_path / "kb.yaml").write_text(f"exclude: ['{pattern}']\n")
    folder = tmp_path / "drafts"
    (folder / "nested").mkdir(parents=True)
    (folder / "nested" / "hidden.md").write_text("---\nid: hidden\ntitle: Hidden\n---\n")
    (folder / "__collection.yaml").write_text("title: Hidden collection\n")
    kept = tmp_path / "kept.md"
    kept.write_text("---\nid: kept\ntitle: Kept\n---\n")
    repo = KBRepository(KBConfig(name="demo", path=tmp_path))
    assert list(repo.list_all_files()) == [kept]
    assert repo.count() == 1


@pytest.mark.parametrize("exclude", [None, "drafts", ["valid", 1]])
def test_invalid_exclusion_lists_are_reported(exclude):
    from pyrite.schema.kb_schema import KBSchema

    with pytest.raises(ValueError, match="exclude must be a list of path patterns"):
        KBSchema.from_dict({"exclude": exclude})


@pytest.mark.parametrize("types", ["[]", "null"])
def test_broken_type_definitions_do_not_disable_exclusions(tmp_path, types):
    (tmp_path / "kb.yaml").write_text(f"types: {types}\nexclude: ['skip.md']\n")
    kept = tmp_path / "keep.md"
    kept.write_text("body")
    (tmp_path / "skip.md").write_text("body")
    assert list(KBRepository(KBConfig(name="demo", path=tmp_path)).list_files()) == [kept]


def test_unreadable_exclusions_keep_files_available_for_health_checks(tmp_path, caplog):
    (tmp_path / "kb.yaml").write_text("types: [broken\n")
    kept = tmp_path / "keep.md"
    kept.write_text("body")
    assert list(KBRepository(KBConfig(name="demo", path=tmp_path)).list_files()) == [kept]
    assert "Could not read exclusions" in caplog.text
