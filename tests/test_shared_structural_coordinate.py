from music_intelligence.learning.score_alignment import (
    AudioScoreAlignment,
    MusicalScoreCoordinate,
    PerformancePhase,
    ScoreAlignedEvidence,
    same_musical_position,
)


def make(eid, chorus, role):
    return ScoreAlignedEvidence(
        evidence_id=eid,
        alignment=AudioScoreAlignment(
            source_id="autumn_leaves_take",
            start_s=10.0 * chorus,
            end_s=10.0 * chorus + 0.5,
            coordinate=MusicalScoreCoordinate(
                song_id="autumn_leaves",
                section="A",
                section_bar=6,
                bar=14,
                beat=4.0,
                subdivision=2.0 / 3.0,
                form_length_bars=32,
                form_bar=14,
                chorus_index=chorus,
                performance_phase=PerformancePhase.SOLO,
                harmonic_function="ii-V",
                harmonic_position="dominant_approach",
                cadence_position="pre_cadential",
                phrase_position="ending",
            ),
        ),
        feature_schema="shared.learning.v2",
        role=role,
        motif_state="return",
        ensemble_state="piano_phrase_ending_bass_foreground_rising",
    )


def test_full_structural_coordinate_matches_across_choruses():
    a = make("a", 1, "support")
    b = make("b", 3, "setup")
    assert same_musical_position(a, b)
    assert not same_musical_position(a, b, ignore_chorus=False)


def test_subdivision_and_section_bar_are_validated():
    ev = make("a", 2, "setup")
    ev.validate()
    c = ev.alignment.coordinate
    assert c.section_bar == 6
    assert c.subdivision == 2.0 / 3.0
    assert c.harmonic_position == "dominant_approach"
    assert c.cadence_position == "pre_cadential"
    assert ev.role == "setup"
    assert ev.motif_state == "return"
    assert ev.ensemble_state.startswith("piano_phrase_ending")
