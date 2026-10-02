from music_intelligence.bass import (
    BassContext,
    BassMode,
    generate_immediate_bass_candidates,
)
from music_intelligence.bass.immediate_realizer import BassHarmonicRole
from music_intelligence.harmony.jazz_harmony_core import (
    HarmonicEvidence,
    HarmonicFrame,
    HarmonySource,
)


def ev(root, symbol, pcs):
    return HarmonicEvidence(
        source=HarmonySource.EXPECTED,
        root_pc=root,
        symbol=symbol,
        pitch_classes=frozenset(pcs),
    )


def test_walking_consumes_shared_diatonic_connection_affordance():
    frame = HarmonicFrame(
        expected=ev(0, "Cm7", {0,3,7,10}),
        next_expected=ev(5, "F7", {5,9,0,3}),
    )
    items = generate_immediate_bass_candidates(
        frame,
        BassContext(
            mode=BassMode.WALKING,
            beat_in_measure=1.0,
            previous_pitch_midi=36,  # C2
            local_key_pitch_classes=frozenset({0,2,3,5,7,9,10}),
        ),
    )
    assert any(x.harmonic_role is BassHarmonicRole.DIATONIC_PASSING for x in items)
    assert any("shared_scale_linear" in x.event.tags for x in items)


def test_contextual_scale_color_requires_explicit_local_key():
    frame = HarmonicFrame(expected=ev(0, "Cm7", {0,3,7,10}))
    without_key = generate_immediate_bass_candidates(
        frame,
        BassContext(
            mode=BassMode.WALKING,
            beat_in_measure=1.0,
            previous_pitch_midi=36,
        ),
    )
    with_key = generate_immediate_bass_candidates(
        frame,
        BassContext(
            mode=BassMode.WALKING,
            beat_in_measure=1.0,
            previous_pitch_midi=36,
            local_key_pitch_classes=frozenset({0,2,3,5,7,9,10}),
        ),
    )
    assert all(x.harmonic_role is not BassHarmonicRole.SCALE_COLOR for x in without_key)
    assert any(x.harmonic_role is BassHarmonicRole.SCALE_COLOR for x in with_key)


def test_two_feel_does_not_consume_scale_color_routes():
    frame = HarmonicFrame(
        expected=ev(0, "Cm7", {0,3,7,10}),
        next_expected=ev(5, "F7", {5,9,0,3}),
    )
    items = generate_immediate_bass_candidates(
        frame,
        BassContext(
            mode=BassMode.TWO_FEEL,
            beat_in_measure=2.0,
            previous_pitch_midi=36,
            local_key_pitch_classes=frozenset({0,2,3,5,7,9,10}),
        ),
    )
    assert all(x.harmonic_role not in {
        BassHarmonicRole.DIATONIC_PASSING,
        BassHarmonicRole.NEIGHBOR,
        BassHarmonicRole.SCALE_COLOR,
    } for x in items)
