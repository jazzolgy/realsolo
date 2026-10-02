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
