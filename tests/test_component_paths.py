"""Component references name real paths and documented public symbols."""

import ast
import re
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
PACKAGE_COVERED_FILES = {
    "pyrite/plugins/registry.py": "pyrite/plugins/",
    "pyrite/models/core_types.py": "pyrite/models/",
    "pyrite/schema/field_aliases.py": "pyrite/schema/",
    "pyrite/cli/__init__.py": "pyrite/cli/",
    "pyrite/storage/database.py": "pyrite/storage/",
    "pyrite/storage/queries.py": "pyrite/storage/",
    "pyrite/server/api.py": "pyrite/server/",
}


def _components():
    return {
        yaml.safe_load(doc.read_text().split("---", 2)[1])["path"]: doc
        for doc in (ROOT / "kb/components").glob("*.md")
    }


@pytest.mark.parametrize("path", sorted(_components()))
def test_each_component_path_exists(path):
    target = ROOT / path
    assert target.exists(), path
    assert target.is_dir() if path.endswith("/") else target.is_file()


def test_architecture_file_rows_have_a_component():
    paths = _components()
    architecture = (ROOT / ".claude/skills/pyrite-dev/architecture.md").read_text()
    rows = re.findall(r"^\| `([^`]+)` \|", architecture, flags=re.MULTILINE)
    missing = set()
    for path in rows:
        if path in paths:
            continue
        if path.endswith("/") or "*" in path:
            assert any(p.endswith("/") and path.startswith(p) for p in paths), path
        else:
            missing.add(path)
            package = PACKAGE_COVERED_FILES.get(path)
            assert package in paths and path.startswith(package), path
    assert missing == set(PACKAGE_COVERED_FILES), "remove allowances once exact components exist"


@pytest.mark.parametrize(
    "component", ["entry-writer", "file-operations", "kb-resolver", "index-health"]
)
def test_documented_public_symbols_exist(component):
    doc = ROOT / "kb/components" / f"{component}.md"
    text = doc.read_text()
    meta = yaml.safe_load(text.split("---", 2)[1])
    tree = ast.parse((ROOT / meta["path"]).read_text())
    names = {n.name for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.ClassDef))}
    names.update(
        alias.asname or alias.name
        for n in tree.body
        if isinstance(n, ast.ImportFrom)
        for alias in n.names
    )
    names.update(
        target.id
        for n in tree.body
        if isinstance(n, ast.Assign)
        for target in n.targets
        if isinstance(target, ast.Name)
    )
    public = text.split("## Public functions", 1)
    if len(public) == 1:
        return  # other component layouts are covered by the path check
    section = public[1].split("## Who calls", 1)[0]
    for name in re.findall(r"^- `([\w]+)(?:\([^`]*\))?`", section, flags=re.MULTILINE):
        assert name in names, f"{doc.name}: {name} is no longer in {meta['path']}"
