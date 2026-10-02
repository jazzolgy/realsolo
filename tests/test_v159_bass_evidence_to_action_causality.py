from dataclasses import replace

from music_intelligence.corpus.scorebooks import (
    ScoreEvidence,
    ScoreEvidenceKind,
)
from music_intelligence.harmony.jazz_harmony_core import (
    HarmonicEvidence,
    HarmonicFrame,
    HarmonySource,
)
from players.bass import (
    BassContext,
    BassMode,
    generate_immediate_bass_candidates,
)
from players.bass.scorebook_evidence import (
    BassScoreEvidenceDirective,
    derive_bass_score_evidence,
)
from players.bass.written_part_comparator import (
    BassLineObservation,
    analyze_bass_line,
    written_part_prior_from_profile,
)


def ev(root, symbol, pcs):
    return HarmonicEvidence(
        source=HarmonySource.EXPECTED,
        root_pc=root,
        symbol=symbol,
        pitch_classes=frozenset(pcs),
    )


def score_for_role(items, role):
    values = [x.score for x in items if x.harmonic_role.value == role]
    assert values, role
    return max(values)


def test_bass_walks_evidence_changes_candidate_ranking_causally():
    frame = HarmonicFrame(
        expected=ev(0, "Cm7", {0,3,7,10}),
        next_expected=ev(5, "F7", {5,9,0,3}),
    )
    neutral = generate_immediate_bass_candidates(
        frame,
        BassContext(
            mode=BassMode.WALKING,
            beat_in_measure=1.0,
            previous_pitch_midi=36,
            local_key_pitch_classes=frozenset({0,2,3,5,7,9,10}),
        ),
    )
    directive = derive_bass_score_evidence((
        ScoreEvidence(
            ScoreEvidenceKind.BASS_INSTRUCTION,
            "bass walks",
            confidence=1.0,
            provenance=("score:newreal2:along_came_betty",),
        ),
    ))
    informed = generate_immediate_bass_candidates(
        frame,
        BassContext(
            mode=BassMode.WALKING,
            beat_in_measure=1.0,
            previous_pitch_midi=36,
            local_key_pitch_classes=frozenset({0,2,3,5,7,9,10}),
            score_evidence=directive,
        ),
    )
    assert score_for_role(informed, "diatonic_passing") > score_for_role(neutral, "diatonic_passing")


def test_two_feel_evidence_reinforces_root_fifth_and_restrains_color():
    frame = HarmonicFrame(
        expected=ev(0, "Cm7", {0,3,7,10}),
        next_expected=ev(5, "F7", {5,9,0,3}),
    )
    neutral = generate_immediate_bass_candidates(
        frame,
        BassContext(mode=BassMode.TWO_FEEL, beat_in_measure=2.0, previous_pitch_midi=36),
    )
    directive = derive_bass_score_evidence((
        ScoreEvidence(ScoreEvidenceKind.FEEL_CHANGE, "two feel", confidence=1.0),
    ))
    informed = generate_immediate_bass_candidates(
        frame,
        BassContext(
            mode=BassMode.TWO_FEEL,
            beat_in_measure=2.0,
            previous_pitch_midi=36,
            score_evidence=directive,
        ),
    )
    assert score_for_role(informed, "fifth") > score_for_role(neutral, "fifth")
    assert score_for_role(informed, "chord_tone") < score_for_role(neutral, "chord_tone")


def test_written_part_presence_alone_does_not_bias_notes():
    directive = derive_bass_score_evidence((
        ScoreEvidence(
            ScoreEvidenceKind.WRITTEN_BASS_PART,
            "dedicated bass page",
            confidence=1.0,
        ),
    ))
    assert directive.written_part_available is True
    assert directive.written_part_prior is None
    assert directive.preferred_mode is None


def test_written_part_abstract_profile_can_bias_scalar_route_without_copying_notes():
    written = (
        BassLineObservation(36, 0.0, 0, frozenset({0,3,7,10})),
        BassLineObservation(38, 1.0, 0, frozenset({0,3,7,10})),
        BassLineObservation(39, 2.0, 0, frozenset({0,3,7,10})),
        BassLineObservation(41, 3.0, 5, frozenset({5,9,0,3})),
    )
    prior = written_part_prior_from_profile(analyze_bass_line(written))
    directive = replace(
        BassScoreEvidenceDirective(written_part_available=True),
        written_part_prior=prior,
    )
    frame = HarmonicFrame(
        expected=ev(0, "Cm7", {0,3,7,10}),
        next_expected=ev(5, "F7", {5,9,0,3}),
    )
    neutral = generate_immediate_bass_candidates(
        frame,
        BassContext(
            mode=BassMode.WALKING,
            beat_in_measure=1.0,
            previous_pitch_midi=36,
            local_key_pitch_classes=frozenset({0,2,3,5,7,9,10}),
        ),
    )
    informed = generate_immediate_bass_candidates(
        frame,
        BassContext(
            mode=BassMode.WALKING,
            beat_in_measure=1.0,
            previous_pitch_midi=36,
            local_key_pitch_classes=frozenset({0,2,3,5,7,9,10}),
            score_evidence=directive,
        ),
    )
    assert score_for_role(informed, "diatonic_passing") > score_for_role(neutral, "diatonic_passing")
