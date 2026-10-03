"""Architecture preflight for the Transcription + Notation workstream.

Usage:
    python scripts/transcription_architecture_preflight.py

The command is diagnostic: it reports branch drift and ownership overlap before
development begins. Hard dependency/contract rules live in pytest architecture
guards.
"""
from __future__ import annotations

import ast
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TRANSCRIBE_ROOT = ROOT / "src/music_intelligence/transcribe"
OWNERSHIP = ROOT / "docs/ARCHITECTURE_OWNERSHIP.yaml"
CONTRACT_FIXTURE = ROOT / "tests/contracts/performance_evidence_v1_expected.json"

FORBIDDEN_AUDIO_PREFIXES = (
    "music_intelligence.audio_evidence.observation",
    "music_intelligence.audio_evidence.posterior",
    "music_intelligence.audio_evidence.detectors",
    "music_intelligence.audio_evidence.separation",
)


def _git(*args: str) -> str:
    result = subprocess.run(
        ("git", *args),
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def _imports_from(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    imports: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module)
    return imports


def main() -> int:
    ownership = json.loads(OWNERSHIP.read_text(encoding="utf-8"))
    fixture = json.loads(CONTRACT_FIXTURE.read_text(encoding="utf-8"))

    branch = _git("branch", "--show-current") or "(detached)"
    head = _git("rev-parse", "--short=12", "HEAD") or "(unknown)"
    main_head = _git("rev-parse", "--short=12", "main") or "(main unavailable)"
    changed = [
        line
        for line in _git("diff", "--name-only", "main...HEAD").splitlines()
        if line
    ]

    external_changes = [
        path
        for path in changed
        if not (
            path.startswith("src/music_intelligence/transcribe/")
            or path.startswith("transcribe/")
            or path.startswith("tests/test_transcribe")
            or path.startswith("tests/architecture/")
            or path.startswith("tests/contracts/")
            or path.startswith("docs/")
            or path.startswith("scripts/transcription_")
            or path == "CORE_CHANGE_REQUEST.md"
            or path == "WORKSTREAM.md"
        )
    ]

    forbidden_imports: list[str] = []
    for path in TRANSCRIBE_ROOT.glob("*.py"):
        for imported in _imports_from(path):
            if imported.startswith(FORBIDDEN_AUDIO_PREFIXES):
                forbidden_imports.append(f"{path.name}: {imported}")

    print("Architecture Preflight — Transcription + Notation")
    print(f"branch: {branch}")
    print(f"head: {head}")
    print(f"main: {main_head}")
    print(f"performance evidence contract: {fixture['contract_version']}")
    print(f"changed files vs main: {len(changed)}")
    print(f"outside transcription ownership: {len(external_changes)}")
    if external_changes:
        print("overlap review required:")
        for path in external_changes[:30]:
            print(f"  - {path}")
        if len(external_changes) > 30:
            print(f"  ... and {len(external_changes) - 30} more")

    if forbidden_imports:
        print("FORBIDDEN Audio Evidence internal dependencies:")
        for item in forbidden_imports:
            print(f"  - {item}")
        return 2

    domain = ownership["domains"]["transcription_notation"]
    print("owns:")
    for path in domain["owns"]:
        print(f"  - {path}")
    print("boundary audit: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
