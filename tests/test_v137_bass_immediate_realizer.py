from music_intelligence.bass import (
    BassContext,
    BassHarmonicRole,
    BassMode,
    generate_immediate_bass_candidates,
)
from music_intelligence.harmony.jazz_harmony_core import (
    HarmonicEvidence,
    HarmonicFrame,
    HarmonySource,
)


def ev(source, root, symbol, pcs):
    return HarmonicEvidence(
        source=source,
        root_pc=root,
        symbol=symbol,
        pitch_classes=frozenset(pcs),
    )


def test_walking_generates_immediate_root_and_chord_candidates():
    frame = HarmonicFrame(
        expected=ev(HarmonySource.EXPECTED, 0, "Cmaj7", {0, 4, 7, 11}),
    )
    items = generate_immediate_bass_candidates(
        frame,
        BassContext(mode=BassMode.WALKING, beat_in_measure=0),
    )
    assert items
    assert any(x.harmonic_role is BassHarmonicRole.ROOT for x in items)
    assert all(x.event.duration_beats == 1.0 for x in items)
    assert all(28 <= x.event.pitch_midi <= 55 for x in items)


def test_inferred_harmony_has_precedence_without_reimplementing_harmony():
    frame = HarmonicFrame(
        expected=ev(HarmonySource.EXPECTED, 0, "C7", {0, 4, 7, 10}),
        inferred=ev(HarmonySource.INFERRED, 2, "Dm7", {0, 2, 5, 9}),
    )
    items = generate_immediate_bass_candidates(frame, BassContext())
    roots = [x for x in items if x.harmonic_role is BassHarmonicRole.ROOT]
    assert roots[0].target_pitch_class == 2


def test_shared_pitch_evidence_prevents_false_perfect_fifth():
    frame = HarmonicFrame(
        expected=ev(HarmonySource.EXPECTED, 2, "Dm7b5", {0, 2, 5, 8}),
    )
    items = generate_immediate_bass_candidates(frame, BassContext())
    assert not any(
        x.harmonic_role is BassHarmonicRole.FIFTH and x.target_pitch_class == 9
        for x in items
    )


def test_late_measure_can_prepare_next_harmony_but_not_a_future_line():
    frame = HarmonicFrame(
        expected=ev(HarmonySource.EXPECTED, 2, "Dm7", {0, 2, 5, 9}),
        next_expected=ev(HarmonySource.EXPECTED, 7, "G7", {2, 5, 7, 11}),
    )
    items = generate_immediate_bass_candidates(
        frame,
        BassContext(mode=BassMode.WALKING, beat_in_measure=3.0, previous_pitch_midi=38),
    )
    roles = {x.harmonic_role for x in items}
    assert BassHarmonicRole.CHROMATIC_APPROACH in roles
    assert BassHarmonicRole.ANTICIPATION in roles
    assert all(not hasattr(x, "future_line") for x in items)


def test_two_feel_realizes_longer_immediate_action():
    frame = HarmonicFrame(
        expected=ev(HarmonySource.EXPECTED, 5, "F7", {0, 3, 5, 9}),
    )
    items = generate_immediate_bass_candidates(
        frame,
        BassContext(mode=BassMode.TWO_FEEL, beat_in_measure=0.0),
    )
    assert items
    assert all(x.event.duration_beats == 2.0 for x in items)


def test_pedal_mode_stays_on_current_root():
    frame = HarmonicFrame(
        expected=ev(HarmonySource.EXPECTED, 7, "G7", {2, 5, 7, 11}),
    )
    items = generate_immediate_bass_candidates(
        frame,
        BassContext(mode=BassMode.PEDAL, beat_in_measure=1.0),
    )
    assert len(items) == 1
    assert items[0].harmonic_role is BassHarmonicRole.PEDAL
    assert items[0].target_pitch_class == 7
