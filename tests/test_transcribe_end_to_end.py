from music_intelligence.reasoning.ensemble_state import CommitmentState
from music_intelligence.transcribe import (
    CommittedPerformanceEvent,
    PerformedPitch,
    PerformanceTimeSpan,
)
from music_intelligence.transcribe.allocation import StaffProfile
from music_intelligence.transcribe.musicxml import score_to_musicxml
from music_intelligence.transcribe.projection import project_pitched_event
from music_intelligence.transcribe.score import ScorePart, assemble_score
from music_intelligence.transcribe.spelling import PitchSpellingContext


def test_committed_sax_event_reaches_readable_musicxml_without_mutating_performance():
    performed = CommittedPerformanceEvent(
        event_id="sax:performed:1",
        player_id="sax",
        instrument="tenor_sax",
        commitment=CommitmentState.PLAYED,
        time=PerformanceTimeSpan(
            onset_seconds=12.021,
            offset_seconds=12.503,
            transport_beat=4.018,
            transport_offset_beat=4.497,
        ),
        pitch=PerformedPitch(
            nominal_midi=70,
            frequency_hz=466.1,
            cents_offset=-1.2,
            continuous_pitch_ref="curve:sax:1",
        ),
        voice_role="melody",
        articulation=("accent",),
        provenance=("player/sax", "played"),
    )

    projection = project_pitched_event(
        performed,
        part_id="sax",
        staffs=(
            StaffProfile(
                "sax:staff",
                "sax",
                role_tags=frozenset({"melody"}),
                nominal_low_midi=45,
                nominal_high_midi=92,
            ),
        ),
        spelling_context=PitchSpellingContext(key_fifths=-2),
    )
    part = ScorePart(
        "sax",
        "Tenor Sax",
        "tenor_sax",
        ("sax:staff",),
        projection.score_events,
    )
    score = assemble_score(score_id="take:1", title="AI Ensemble Take", parts=(part,))
    xml = score_to_musicxml(score)

    assert "<score-partwise" in xml
    assert "<step>B</step>" in xml
    assert "<alter>-1</alter>" in xml
    assert "accent" in xml

    # Original physical evidence remains untouched and auditable.
    assert performed.time.onset_seconds == 12.021
    assert performed.time.transport_beat == 4.018
    assert performed.pitch.continuous_pitch_ref == "curve:sax:1"
    assert len(projection.rhythm_candidates) > 1
    assert len(projection.spelling_candidates) > 1
