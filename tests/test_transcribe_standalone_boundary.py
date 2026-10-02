from pathlib import Path

from music_intelligence.reasoning.ensemble_state import CommitmentState
from music_intelligence.transcribe.events import (
    CommittedPerformanceEvent,
    PerformanceCommitment,
    PerformedPitch,
    PerformanceTimeSpan,
)


def _event(commitment):
    return CommittedPerformanceEvent(
        event_id="standalone:1",
        player_id="source",
        instrument="violin",
        commitment=commitment,
        time=PerformanceTimeSpan(0.0, 0.5),
        pitch=PerformedPitch(nominal_midi=69),
    )


def test_standalone_commitment_enum_is_accepted():
    event = _event(PerformanceCommitment.COMMITTED)
    event.validate()


def test_realsolo_commitment_enum_is_accepted_without_contract_import_dependency():
    event = _event(CommitmentState.PLAYED)
    event.validate()


def test_transcribe_package_does_not_import_realsolo_reasoning_package():
    root = Path("src/music_intelligence/transcribe")
    offenders = []
    for path in root.glob("*.py"):
        text = path.read_text(encoding="utf-8")
        if "music_intelligence.reasoning" in text:
            offenders.append(path.name)
    assert offenders == []
