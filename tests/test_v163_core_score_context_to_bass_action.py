from music_intelligence.corpus import (
    SEED_SONG_LOCATORS,
    ScorePosition,
    resolve_score_context,
)
from music_intelligence.harmony.jazz_harmony_core import (
    HarmonicEvidence,
    HarmonicFrame,
    HarmonySource,
)
from players.bass import BassContext, BassMode, generate_immediate_bass_candidates
from players.bass.scorebook_evidence import derive_bass_score_context


def ev(root, symbol, pcs):
    return HarmonicEvidence(
        source=HarmonySource.EXPECTED,
        root_pc=root,
        symbol=symbol,
        pitch_classes=frozenset(pcs),
    )


def song(title):
    return next(x for x in SEED_SONG_LOCATORS if x.title == title)


def best(items, role):
    vals=[x.score for x in items if x.harmonic_role.value == role]
    assert vals
    return max(vals)


def test_betty_score_context_changes_canonical_bass_ranking_end_to_end():
    snap = resolve_score_context(
        song("Along Came Betty"),
        ScorePosition(page=8),
    )
    directive = derive_bass_score_context(snap)
    assert directive.preferred_mode == "walking"
    assert directive.walking_pressure > 0

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
    assert best(informed, "diatonic_passing") > best(neutral, "diatonic_passing")


def test_actual_proof_context_marks_written_part_without_forcing_walking():
    snap = resolve_score_context(
        song("Actual Proof"),
        ScorePosition(page=2),
    )
    directive = derive_bass_score_context(snap)
    assert directive.written_part_available is True
    assert directive.preferred_mode is None
    assert directive.walking_pressure == 0.0
