from music_intelligence.reasoning.ensemble_state import CommitmentState
from music_intelligence.transcribe import (
    CommittedPerformanceEvent,
    PerformedPitch,
    MusicalCoordinate,
    PerformanceTimeSpan,
    PerceptualDynamics,
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


def test_score_projection_prefers_perceptual_dynamic():
    performed = CommittedPerformanceEvent(event_id="piano:dyn:1", player_id="piano", instrument="piano", commitment=CommitmentState.PLAYED, time=PerformanceTimeSpan(onset_seconds=1.0, offset_seconds=1.5, transport_beat=0.0, transport_offset_beat=1.0), pitch=PerformedPitch(nominal_midi=60), dynamic=.92, dynamics=PerceptualDynamics(dynamic_absolute_ordinal=.24, dynamic_confidence=.88, dynamic_evidence=("calibrated",)))
    projection = project_pitched_event(performed, part_id="piano", staffs=(StaffProfile("piano:upper", "piano"),))
    assert projection.score_events[0].dynamic_marking == "p"



def test_score_projection_preserves_canonical_musical_coordinate_and_factorized_dynamics():
    coordinate = MusicalCoordinate(
        form="AABA",
        section="B",
        chorus=2,
        bar_in_section=5,
        beat=3,
        subdivision=__import__("fractions").Fraction(2, 3),
        confidence=.91,
        uncertainty=("rubato beat boundary",),
    )
    dynamics = PerceptualDynamics(
        dynamic_absolute_ordinal=.68,
        dynamic_relative_to_track=.57,
        dynamic_relative_to_section=.74,
        dynamic_relative_to_phrase=.81,
        dynamic_confidence=.86,
        dynamic_evidence=(
            "source-calibrated",
            "spectral-brightness",
            "attack-sharpness",
            "ensemble-density",
            "phrase-context",
        ),
    )
    performed = CommittedPerformanceEvent(
        event_id="piano:coordinate:1",
        player_id="piano",
        instrument="piano",
        commitment=CommitmentState.PLAYED,
        time=PerformanceTimeSpan(
            onset_seconds=37.412,
            offset_seconds=37.801,
            transport_beat=18.67,
            transport_offset_beat=19.31,
        ),
        pitch=PerformedPitch(nominal_midi=72),
        musical_coordinate=coordinate,
        dynamics=dynamics,
        provenance=("audio-alignment:37.412",),
    )

    projection = project_pitched_event(
        performed,
        part_id="piano",
        staffs=(StaffProfile("piano:upper", "piano"),),
    )

    assert projection.score_events
    for score_event in projection.score_events:
        assert score_event.musical_coordinate == coordinate
        assert score_event.dynamics == dynamics
        assert score_event.musical_coordinate.section == "B"
        assert score_event.musical_coordinate.subdivision == __import__("fractions").Fraction(2, 3)
        assert score_event.dynamics.dynamic_relative_to_phrase == .81

    # Physical time remains source/alignment evidence; it is not substituted
    # for the canonical form/section/chorus/bar/beat/subdivision coordinate.
    assert performed.time.onset_seconds == 37.412
    assert projection.score_events[0].musical_coordinate.beat == 3
