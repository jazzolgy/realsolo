from music_intelligence.drums.pattern_corpus import (
    PatternUse,
    get_pattern,
    hits_at_current_position,
    patterns_with_tags,
)
from music_intelligence.drums.pattern_runtime import pattern_gesture_now
from music_intelligence.drums.model import DrummerRuntimeContext, DrumVoice


def test_source_patterns_keep_rights_metadata():
    pattern = get_pattern("riley_bop_ride_basic_01")
    assert pattern.exact_source_pattern is True
    assert PatternUse.REFERENCE in pattern.source.allowed_uses
    assert PatternUse.TRAINING not in pattern.source.allowed_uses


def test_whole_pattern_can_be_stored_but_runtime_exposes_only_now():
    pattern = get_pattern("spagnardi_upbeat4_four16_setup")
    assert len(pattern.hits) == 4
    current = hits_at_current_position(pattern, 0.25)
    assert len(current) == 1
    assert current[0].onset_beats == 0.25


def test_source_pattern_tags_can_be_queried():
    setups = patterns_with_tags("big_band", "setup")
    assert len(setups) >= 3


def test_riley_swing_offbeat_is_tempo_warped_at_runtime():
    pattern = get_pattern("riley_bop_ride_basic_01")
    medium = pattern_gesture_now(
        pattern,
        DrummerRuntimeContext(position_in_bar_beats=1.6666666667, tempo_bpm=140),
        tolerance_beats=0.02,
    )
    fast = pattern_gesture_now(
        pattern,
        DrummerRuntimeContext(position_in_bar_beats=1.6666666667, tempo_bpm=300),
        tolerance_beats=0.02,
    )
    assert medium is not None
    assert fast is None
    assert any(hit.voice is DrumVoice.RIDE for hit in medium.hits)


def test_style_gating_prevents_big_band_setup_in_bop_only_plan():
    from music_intelligence.drums.model import DrummerSoftPlan
    from music_intelligence.drums.pattern_runtime import source_pattern_candidates

    plan = DrummerSoftPlan(style_tags=frozenset({"jazz", "bop"}))
    ctx = DrummerRuntimeContext(
        position_in_bar_beats=0.0,
        phrase_position=0.95,
        section_transition=True,
    )
    candidates = source_pattern_candidates(plan, ctx)
    assert all("big_band" not in g.tags for g in candidates)


def test_big_band_plan_can_retrieve_big_band_setup():
    from music_intelligence.drums.model import DrummerSoftPlan
    from music_intelligence.drums.pattern_runtime import source_pattern_candidates

    plan = DrummerSoftPlan(style_tags=frozenset({"jazz", "big_band"}))
    ctx = DrummerRuntimeContext(
        position_in_bar_beats=0.0,
        phrase_position=0.95,
        section_transition=True,
    )
    candidates = source_pattern_candidates(plan, ctx)
    assert any("big_band" in g.tags for g in candidates)


def test_plainfield_clave_patterns_are_stored_with_direction():
    son32 = get_pattern("plainfield_son_clave_3_2")
    son23 = get_pattern("plainfield_son_clave_2_3")
    rumba32 = get_pattern("plainfield_rumba_clave_3_2")
    assert len(son32.hits) == 5
    assert "3_2" in son32.tags
    assert "2_3" in son23.tags
    assert "rumba_clave" in rumba32.tags


def test_afro_cuban_plan_can_retrieve_clave_but_bop_plan_cannot():
    from music_intelligence.drums.model import DrummerSoftPlan
    from music_intelligence.drums.pattern_runtime import source_pattern_candidates

    ctx = DrummerRuntimeContext(position_in_bar_beats=0.0)
    latin = source_pattern_candidates(
        DrummerSoftPlan(style_tags=frozenset({"afro_cuban"})), ctx
    )
    bop = source_pattern_candidates(
        DrummerSoftPlan(style_tags=frozenset({"jazz", "bop"})), ctx
    )
    assert any("clave" in g.tags for g in latin)
    assert all("clave" not in g.tags for g in bop)


def test_two_bar_clave_can_address_second_bar_via_pattern_phase():
    from music_intelligence.drums.model import DrummerSoftPlan
    from music_intelligence.drums.pattern_runtime import source_pattern_candidates

    plan = DrummerSoftPlan(style_tags=frozenset({"afro_cuban"}))
    # Bar-relative position is beat 2, but corpus phase is beat 6 of the 8-beat clave.
    ctx = DrummerRuntimeContext(
        position_in_bar_beats=2.0,
        pattern_phase_beats=6.0,
    )
    candidates = source_pattern_candidates(plan, ctx)
    assert any(
        "plainfield_son_clave_3_2" in g.tags
        for g in candidates
    )
