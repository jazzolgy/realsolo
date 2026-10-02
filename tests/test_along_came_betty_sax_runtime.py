from music_intelligence.corpus import (
    ALONG_CAME_BETTY_EVIDENCE,
    ALONG_CAME_BETTY_LOCATOR,
    ScorePerformancePhase,
    ScorePosition,
    harmonic_frame_from_score,
    parse_score_chord_symbol,
    resolve_score_context,
)
from players.sax.chart_runtime import build_sax_chart_tick

def _snap(bar,beat,phase=ScorePerformancePhase.SOLO):
    return resolve_score_context(
        ALONG_CAME_BETTY_LOCATOR,
        ScorePosition(page=7,bar=bar,beat=beat),
        ALONG_CAME_BETTY_EVIDENCE,
        phase=phase,
    )

def test_half_bar_harmony_is_beat_resolved():
    assert _snap(2,1.0).chords==("Bm7",)
    assert _snap(2,2.5).chords==("Bm7",)
    assert _snap(2,3.0).chords==("E7",)
    assert _snap(2,4.0).chords==("E7",)

def test_score_chord_parser_handles_along_came_betty_vocab():
    assert parse_score_chord_symbol("Bbm7").quality=="minor7"
    assert parse_score_chord_symbol("Am7b5").quality=="half_diminished7"
    assert parse_score_chord_symbol("Eb7#9").quality=="dominant7_sharp9"
    assert parse_score_chord_symbol("Gm7/F").bass_pc==5

def test_score_harmony_keeps_expected_and_next_separate():
    f=harmonic_frame_from_score(_snap(2,1.0),next_snapshot=_snap(2,3.0))
    assert f.expected.symbol=="Bm7"
    assert f.next_expected.symbol=="E7"
    assert f.observed is None and f.inferred is None

def test_head_requires_written_material_not_generated_solo():
    p=build_sax_chart_tick(_snap(1,1.0,ScorePerformancePhase.HEAD))
    assert p.requires_written_material
    assert p.shared_solo is None
    assert p.realizations==()

def test_open_solo_reaches_shared_solo_and_sax_realizer():
    p=build_sax_chart_tick(_snap(2,1.0),next_score_snapshot=_snap(2,3.0),previous_pitch_midi=59,phrase_position=.35,tension=.4)
    assert p.shared_solo is not None
    assert p.groove is not None and p.groove.feel.value=="swing"
    assert p.groove.tempo_bpm==110
    assert p.realizations
    assert any(x.feasibility.feasible for x in p.realizations)
    assert all(not hasattr(x.realization.event,"future_notes") for x in p.realizations)

def test_future_half_bar_harmony_reaches_immediate_candidate_tags():
    p=build_sax_chart_tick(_snap(2,1.0),next_score_snapshot=_snap(2,3.0),previous_pitch_midi=59,phrase_position=.4)
    tags=set()
    for x in p.realizations: tags.update(x.realization.event.tags)
    assert "next_harmony_target" in tags or "anticipation" in tags
