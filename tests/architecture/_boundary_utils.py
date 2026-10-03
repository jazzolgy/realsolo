from __future__ import annotations

import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def python_files_under(relative: str):
    root = ROOT / relative
    if not root.exists():
        return ()
    return tuple(root.rglob("*.py"))


def imported_modules(path: Path) -> tuple[str, ...]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    modules: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            modules.append(node.module)
    return tuple(modules)


def forbidden_imports(relative: str, forbidden_prefixes: tuple[str, ...]):
    findings = []
    for path in python_files_under(relative):
        for module in imported_modules(path):
            if any(
                module == prefix or module.startswith(prefix + ".")
                for prefix in forbidden_prefixes
            ):
                findings.append((path.relative_to(ROOT).as_posix(), module))
    return findings
