"""Entry-file enumeration for commands that inspect or export KB files."""

from pathlib import Path

from ..config import KBConfig
from ..storage.repository import KBRepository


def listed_markdown_files(kb: KBConfig, folder: Path | None = None) -> list[Path]:
    """Visible Markdown files, optionally restricted to a collection folder."""
    paths = KBRepository(kb).list_files()
    return sorted(p for p in paths if folder is None or p.is_relative_to(folder.resolve()))


def filter_listed_paths(paths: list[Path], kbs: list[KBConfig]) -> list[Path]:
    """Keep paths included by a KB walk, reading each KB's exclusions once."""
    repositories = [KBRepository(kb) for kb in kbs]
    return [path for path in paths if any(repo._listed(path.resolve()) for repo in repositories)]


def collect_markdown_files(paths: list[Path]) -> list[Path]:
    """Expand directory arguments, honoring their enclosing KB's exclusions.

    Explicit files and directories outside a KB keep schema validate's existing
    behavior, so callers can inspect an excluded file by naming it directly.
    """
    result: list[Path] = []
    for path in paths:
        if path.is_file() and path.suffix == ".md":
            result.append(path)
        elif path.is_dir():
            root = next((d for d in (path, *path.parents) if (d / "kb.yaml").is_file()), None)
            if root is None:
                result.extend(sorted(path.rglob("*.md")))
            else:
                result.extend(listed_markdown_files(KBConfig(name=root.name, path=root), path))
    return result
