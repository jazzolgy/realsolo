from fractions import Fraction

from music_intelligence.transcribe import (
    NotationEngine,
    NotationEngineConfig,
    PerformanceCommitment,
)
from music_intelligence.transcribe.allocation import StaffProfile
from music_intelligence.transcribe.events import (
    CommittedPerformanceEvent,
    PerformedPitch,
    PerformanceTimeSpan,
)
from music_intelligence.transcribe.score import ScorePart, assemble_score


def test_standalone_engine_projects_a_source_neutral_event_and_exports_musicxml():
    engine = NotationEngine(NotationEngineConfig(meter_numerator=4, meter_denominator=4))
    event = CommittedPerformanceEvent(
        event_id="standalone:note",
        player_id="upload",
        instrument="violin",
        commitment=PerformanceCommitment.PLAYED,
        time=PerformanceTimeSpan(
            onset_seconds=0.0,
            offset_seconds=.5,
            transport_beat=0.0,
            transport_offset_beat=1.0,
        ),
        pitch=PerformedPitch(nominal_midi=69),
        dynamic=.55,
    )

    projection = engine.project_pitched_event(
        event,
        part_id="vln",
        staffs=(StaffProfile("staff", "vln"),),
    )
    part = ScorePart(
        "vln",
        "Violin",
        "violin",
        ("staff",),
        projection.score_events,
        profile_id="violin",
    )
    score = assemble_score(score_id="standalone:score", title="Take", parts=(part,))

    xml = engine.musicxml(score)
    report = engine.audit(score)

    assert "<score-partwise" in xml
    assert "<sign>G</sign>" in xml
    assert "<mf" in xml
    assert report.has_errors is False


def test_engine_facade_does_not_require_realsolo_player_objects():
    engine = NotationEngine()
    assert engine.resolve_instrument("viola").display_name == "Viola"
    assert engine.resolve_instrument("french_horn").transposition.chromatic_semitones == -7
