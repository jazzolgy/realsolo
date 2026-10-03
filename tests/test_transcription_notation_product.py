from fractions import Fraction

from music_intelligence.transcribe.allocation import StaffProfile
from music_intelligence.transcribe.events import (
    CommittedPerformanceEvent,
    PerformedPitch,
    PerformanceCommitment,
    PerformanceTimeSpan,
)
from music_intelligence.transcribe.product import (
    TranscriptionNotationEngine,
    TranscriptionNotationConfig,
)


def _event():
    return CommittedPerformanceEvent(
        event_id="take1:piano:1",
        player_id="source",
        instrument="piano",
        commitment=PerformanceCommitment.PLAYED,
        time=PerformanceTimeSpan(
            onset_seconds=0.50,
            offset_seconds=0.96,
            transport_beat=1.02,
            transport_offset_beat=1.96,
        ),
        pitch=PerformedPitch(nominal_midi=61),
        voice_role="melody",
    )


def test_combined_engine_runs_transcription_and_notation_decisions_together():
    engine = TranscriptionNotationEngine()
    result = engine.transcribe_event(
        _event(),
        staffs=(
            StaffProfile(
                "piano:upper",
                "piano",
                frozenset({"melody"}),
                55,
                108,
            ),
            StaffProfile(
                "piano:lower",
                "piano",
                frozenset({"bass"}),
                21,
                67,
            ),
        ),
    )

    assert result.event_id == "take1:piano:1"
    assert result.intent.source_event_ids == ("take1:piano:1",)
    assert len(result.rhythm_candidates) >= 4
    assert result.preferred_rhythm in result.rhythm_candidates
    assert result.spelling_candidates[0].written_pitch.name in {"C#4", "Db4"}
    assert result.allocation_candidates[0].staff_id == "piano:upper"


def test_product_engine_remains_source_neutral():
    class Source:
        def performance_events(self):
            return (_event(),)

    results = TranscriptionNotationEngine().transcribe_source(Source())
    assert len(results) == 1
    assert results[0].event_id == "take1:piano:1"


def test_config_rejects_negative_product_scoring_weights():
    try:
        TranscriptionNotationConfig(readability_weight=-1).validate()
    except ValueError as exc:
        assert "readability_weight" in str(exc)
    else:
        raise AssertionError("negative scoring weights must be rejected")
