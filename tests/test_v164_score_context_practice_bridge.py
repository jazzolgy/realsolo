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
from players.bass import (
    BassMode,
    BassPracticePulse,
    BassPracticeSong,
    run_scorebook_practice,
)


def ev(root, symbol, pcs):
    return HarmonicEvidence(
        source=HarmonySource.EXPECTED,
        root_pc=root,
        symbol=symbol,
        pitch_classes=frozenset(pcs),
    )


def song(title):
    return next(x for x in SEED_SONG_LOCATORS if x.title == title)


def test_practice_harness_accepts_core_score_context_directly():
    snap = resolve_score_context(
        song("Along Came Betty"),
        ScorePosition(page=8),
    )
    c = ev(0, "Cm7", {0,3,7,10})
    f = ev(5, "F7", {5,9,0,3})
    practice = BassPracticeSong(
        "score.test.betty-context",
        "Betty Context Bridge",
        tuple(
            BassPracticePulse(
                frame=HarmonicFrame(expected=c, next_expected=f),
                beat_in_measure=float(beat),
                absolute_beat=float(beat),
                mode=BassMode.WALKING,
                local_key_pitch_classes=frozenset({0,2,3,5,7,9,10}),
                score_context=snap,
            )
            for beat in range(4)
        ),
    )
    session = run_scorebook_practice(practice, passes=1)
    assert session.passes[0].metrics.event_count == 4
    reasons = tuple(
        reason
        for step in session.passes[0].results
        for reason in step.candidate.reasons
    )
    assert any("scorebook walking evidence" in r for r in reasons)
