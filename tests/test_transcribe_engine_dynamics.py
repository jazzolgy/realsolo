from fractions import Fraction

from music_intelligence.reasoning.ensemble_state import CommitmentState
from music_intelligence.transcribe import (
    CommittedPerformanceEvent,
    NotationEngine,
    PerformedPitch,
    PerformanceTimeSpan,
)
from music_intelligence.transcribe.notation import NotatedAtomKind, ScoreSpan
from music_intelligence.transcribe.score import ScoreEvent, ScoreSpannerKind
from music_intelligence.transcribe.spelling import WrittenPitch


def _perf(event_id, onset, dynamic):
    return CommittedPerformanceEvent(
        event_id=event_id,
        player_id="vln",
        instrument="violin",
        commitment=CommitmentState.PLAYED,
        time=PerformanceTimeSpan(onset, onset + .5),
        pitch=PerformedPitch(nominal_midi=69),
        dynamic=dynamic,
    )


def _score(event_id, onset):
    return ScoreEvent(
        event_id=f"score:{event_id}",
        part_id="vln",
        staff_id="staff",
        voice_id="v1",
        kind=NotatedAtomKind.NOTE,
        span=ScoreSpan(Fraction(onset), Fraction(1)),
        source_event_ids=(event_id,),
        written_pitch=WrittenPitch("A", 0, 4),
    )


def test_engine_facade_infers_and_maps_dynamic_hairpin():
    engine = NotationEngine()
    events = (
        _perf("a", 0.0, .30),
        _perf("b", .5, .37),
        _perf("c", 1.0, .45),
        _perf("d", 1.5, .54),
    )

    candidate = engine.dynamic_trajectory(events)
    spanner = engine.dynamic_spanner(
        candidate,
        part_id="vln",
        score_events=(
            _score("a", 0),
            _score("b", 1),
            _score("c", 2),
            _score("d", 3),
        ),
    )

    assert spanner is not None
    assert spanner.kind is ScoreSpannerKind.CRESCENDO
