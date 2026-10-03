from __future__ import annotations

import ast
from dataclasses import fields
from pathlib import Path
import tomllib

import pytest

ROOT = Path(__file__).resolve().parents[2]
OWNERSHIP_PATH = ROOT / "docs" / "ARCHITECTURE_OWNERSHIP.toml"


def ownership() -> dict:
    with OWNERSHIP_PATH.open("rb") as fh:
        return tomllib.load(fh)


def python_files(root: Path):
    if not root.exists():
        return ()
    return tuple(path for path in root.rglob("*.py") if "__pycache__" not in path.parts)


def imported_modules(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                modules.add(node.module)
    return modules


def test_declared_owned_roots_do_not_overlap():
    config = ownership()
    roots: list[tuple[str, str]] = []
    for name, stream in config["workstreams"].items():
        for root in stream.get("owned_roots", []):
            roots.append((name, root.rstrip("/") + "/"))

    for index, (name_a, root_a) in enumerate(roots):
        for name_b, root_b in roots[index + 1 :]:
            assert not (
                root_a.startswith(root_b) or root_b.startswith(root_a)
            ), f"owned roots overlap: {name_a}:{root_a} vs {name_b}:{root_b}"


def test_audio_evidence_import_boundary():
    config = ownership()["workstreams"]["audio_evidence"]
    package = ROOT / "src" / "music_intelligence" / "audio_evidence"
    forbidden = tuple(config["forbidden_import_prefixes"])

    violations: list[str] = []
    for path in python_files(package):
        for module in imported_modules(path):
            if module.startswith(forbidden):
                violations.append(f"{path.relative_to(ROOT)} -> {module}")

    assert not violations, "Audio Evidence crossed architecture boundary:\n" + "\n".join(violations)


def test_transcription_does_not_depend_on_audio_evidence_internals():
    config = ownership()["workstreams"]["transcription_notation"]
    package = ROOT / "src" / "music_intelligence" / "transcribe"
    forbidden = tuple(config["forbidden_import_prefixes"])

    violations: list[str] = []
    for path in python_files(package):
        for module in imported_modules(path):
            if module.startswith(forbidden):
                violations.append(f"{path.relative_to(ROOT)} -> {module}")

    assert not violations, "Transcription depends on Audio Evidence internals:\n" + "\n".join(violations)


def test_audio_evidence_does_not_duplicate_core_or_notation_modules():
    config = ownership()["workstreams"]["audio_evidence"]
    package = ROOT / "src" / "music_intelligence" / "audio_evidence"
    forbidden = set(config["forbidden_module_names"])
    if not package.exists():
        return

    violations = [
        str(path.relative_to(ROOT))
        for path in package.rglob("*.py")
        if path.stem.lower() in forbidden
    ]
    violations += [
        str(path.relative_to(ROOT))
        for path in package.rglob("*")
        if path.is_dir() and path.name.lower() in forbidden
    ]

    assert not violations, "Audio Evidence duplicated Core/Notation semantics:\n" + "\n".join(sorted(set(violations)))


def test_performance_evidence_contract_snapshot_when_available():
    events_path = ROOT / "src" / "music_intelligence" / "transcribe" / "events.py"
    if not events_path.exists():
        pytest.skip("Performance Evidence contract is not present on this branch")

    from music_intelligence.transcribe import events

    contract = ownership()["contracts"]["performance_evidence"]
    assert events.CONTRACT_VERSION == contract["schema_version"]

    actual = {item.name for item in fields(events.CommittedPerformanceEvent)}
    required = set(contract["required_observation_posterior_fields"])
    missing = required - actual
    assert not missing, (
        "Performance Evidence contract drifted; missing required observation/posterior "
        f"fields: {sorted(missing)}"
    )
