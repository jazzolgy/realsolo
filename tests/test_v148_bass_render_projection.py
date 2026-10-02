from music_intelligence.bass import (
    BassContext,
    BassMode,
    generate_immediate_bass_candidates,
    project_bass_candidate_to_render_event,
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


def test_render_projection_maps_expression_without_changing_note_identity():
    frame = HarmonicFrame(
        expected=ev(HarmonySource.EXPECTED, 0, "Cm7", {0,3,7,10}),
    )
    candidate = generate_immediate_bass_candidates(
        frame,
        BassContext(mode=BassMode.WALKING, beat_in_measure=0.0),
    )[0]
    rendered = project_bass_candidate_to_render_event(candidate, tempo_bpm=120.0)
    assert rendered.pitch_midi == candidate.event.pitch_midi
    assert rendered.duration_beats != 0
    assert 1 <= rendered.velocity <= 127
    assert abs(rendered.onset_offset_beats) <= .25


def test_faster_tempo_converts_same_ms_to_larger_beat_fraction():
    frame = HarmonicFrame(
        expected=ev(HarmonySource.EXPECTED, 0, "Cm7", {0,3,7,10}),
    )
    candidate = generate_immediate_bass_candidates(
        frame,
        BassContext(mode=BassMode.WALKING, beat_in_measure=0.0),
    )[0]
    a = project_bass_candidate_to_render_event(candidate, tempo_bpm=100.0)
    b = project_bass_candidate_to_render_event(candidate, tempo_bpm=200.0)
    if candidate.expression.microtiming_ms != 0:
        assert abs(b.onset_offset_beats) > abs(a.onset_offset_beats)
