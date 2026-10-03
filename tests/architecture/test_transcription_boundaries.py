import ast
import json
from dataclasses import fields
from pathlib import Path

from music_intelligence.transcribe.events import (
    PERFORMANCE_EVIDENCE_CONTRACT_VERSION,
    CommittedPerformanceEvent,
    ConfidenceBundle,
    EventAlternative,
    EvidenceRef,
    PerformanceTimeSpan,
    PerformedPitch,
)


def test_performance_evidence_contract_matches_v1_snapshot():
    expected = json.loads(
        Path("tests/contracts/performance_evidence_v1_expected.json").read_text(
            encoding="utf-8"
        )
    )
    assert expected["contract_version"] == PERFORMANCE_EVIDENCE_CONTRACT_VERSION

    actual_types = {
        "CommittedPerformanceEvent": CommittedPerformanceEvent,
        "ConfidenceBundle": ConfidenceBundle,
        "PerformanceTimeSpan": PerformanceTimeSpan,
        "PerformedPitch": PerformedPitch,
        "EvidenceRef": EvidenceRef,
        "EventAlternative": EventAlternative,
    }
    for name, cls in actual_types.items():
        actual_names = {field.name for field in fields(cls)}
        missing = set(expected[name]) - actual_names
        assert missing == set(), (
            f"BREAKING CONTRACT DRIFT in {name}; removed/renamed fields: "
            f"{sorted(missing)}"
        )


def _imports_from(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    imports = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module)
    return imports


def test_transcription_does_not_depend_on_audio_evidence_internals():
    forbidden_prefixes = (
        "music_intelligence.audio_evidence.observation",
        "music_intelligence.audio_evidence.posterior",
        "music_intelligence.audio_evidence.detectors",
        "music_intelligence.audio_evidence.separation",
    )
    offenders = []
    root = Path("src/music_intelligence/transcribe")
    for path in root.glob("*.py"):
        for imported in _imports_from(path):
            if imported.startswith(forbidden_prefixes):
                offenders.append(f"{path.name}: {imported}")

    assert offenders == [], (
        "Transcription must consume Performance Evidence, not Audio Evidence "
        f"internals: {offenders}"
    )


def test_architecture_ownership_file_is_machine_readable():
    ownership = json.loads(
        Path("docs/ARCHITECTURE_OWNERSHIP.yaml").read_text(encoding="utf-8")
    )
    transcription = ownership["domains"]["transcription_notation"]
    assert "src/music_intelligence/transcribe/**" in transcription["owns"]
    assert "PerformanceEvidence" in transcription["consumes"]
