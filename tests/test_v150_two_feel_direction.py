from music_intelligence.bass import (
    BassContext,
    BassMode,
    generate_immediate_bass_candidates,
)
from music_intelligence.bass.performance_grammar import MetricRole
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


def test_second_two_feel_pulse_has_direction_role():
    c = ev(0, "Cm7", {0,3,7,10})
    f = ev(5, "F7", {5,9,0,3})
    first = generate_immediate_bass_candidates(
        HarmonicFrame(expected=c, next_expected=f),
        BassContext(mode=BassMode.TWO_FEEL, beat_in_measure=0.0),
    )
    second = generate_immediate_bass_candidates(
        HarmonicFrame(expected=c, next_expected=f),
        BassContext(mode=BassMode.TWO_FEEL, beat_in_measure=2.0),
    )
    assert first[0].grammar.metric_role is MetricRole.TWO_FEEL_ANCHOR
    assert all(x.grammar.metric_role is MetricRole.TWO_FEEL_DIRECTION for x in second)


def test_second_two_feel_pulse_can_include_next_root_anticipation():
    c = ev(0, "Cm7", {0,3,7,10})
    f = ev(5, "F7", {5,9,0,3})
    items = generate_immediate_bass_candidates(
        HarmonicFrame(expected=c, next_expected=f),
        BassContext(mode=BassMode.TWO_FEEL, beat_in_measure=2.0),
    )
    assert any("anticipation" in x.event.tags for x in items)
