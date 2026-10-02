from fractions import Fraction

from music_intelligence.reasoning.ensemble_state import CommitmentState
from music_intelligence.transcribe.dynamics import (
    DynamicTrajectoryKind,
    infer_dynamic_trajectory,
    score_spanner_from_dynamic_trajectory,
)
from music_intelligence.transcribe.events import (
    CommittedPerformanceEvent,
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


def test_gradual_rise_prefers_crescendo_hairpin():
    events = (
        _perf("a", 0.0, .30),
        _perf("b", .5, .36),
        _perf("c", 1.0, .43),
        _perf("d", 1.5, .52),
    )

    candidate = infer_dynamic_trajectory(events)

    assert candidate.kind is DynamicTrajectoryKind.CRESCENDO
    assert candidate.total_delta > 0
    assert candidate.monotonic_ratio == 1.0


def test_gradual_fall_prefers_diminuendo_hairpin():
    events = (
        _perf("a", 0.0, .70),
        _perf("b", .5, .63),
        _perf("c", 1.0, .56),
        _perf("d", 1.5, .47),
    )

    candidate = infer_dynamic_trajectory(events)

    assert candidate.kind is DynamicTrajectoryKind.DIMINUENDO


def test_sudden_short_jump_prefers_discrete_dynamic_change():
    events = (
        _perf("a", 0.0, .30),
        _perf("b", .5, .31),
        _perf("c", 1.0, .62),
    )

    candidate = infer_dynamic_trajectory(events)

    assert candidate.kind is DynamicTrajectoryKind.STEP_CHANGE


def test_small_or_inconsistent_motion_adds_no_extra_notation():
    events = (
        _perf("a", 0.0, .50),
        _perf("b", .5, .54),
        _perf("c", 1.0, .49),
        _perf("d", 1.5, .53),
    )

    candidate = infer_dynamic_trajectory(events)

    assert candidate.kind is DynamicTrajectoryKind.NONE


def test_hairpin_candidate_maps_to_score_spanner_endpoints():
    events = (
        _perf("a", 0.0, .30),
        _perf("b", .5, .36),
        _perf("c", 1.0, .44),
        _perf("d", 1.5, .53),
    )
    candidate = infer_dynamic_trajectory(events)
    score_events = (
        _score("a", 0),
        _score("b", 1),
        _score("c", 2),
        _score("d", 3),
    )

    spanner = score_spanner_from_dynamic_trajectory(
        candidate,
        part_id="vln",
        score_events=score_events,
    )

    assert spanner is not None
    assert spanner.kind is ScoreSpannerKind.CRESCENDO
    assert spanner.start_event_id == "score:a"
    assert spanner.end_event_id == "score:d"
