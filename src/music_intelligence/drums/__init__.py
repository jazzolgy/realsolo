"""Instrument-specific AI Drummer realization layer."""

from .comping import CompingPropensity, comping_propensity
from .model import (
    DrumGesture,
    DrumHit,
    DrummerRuntimeContext,
    DrummerSoftPlan,
    DrumVoice,
    GestureRole,
    Limb,
    TimeFeel,
)
from .pattern_corpus import (
    PATTERN_CORPUS,
    PatternHit,
    PatternUse,
    SourceRights,
    StoredDrumPattern,
    get_pattern,
    hits_at_current_position,
    patterns_with_tags,
)
from .pattern_runtime import pattern_gesture_now, source_pattern_candidates
from .online_drummer import (
    DrummerPerformanceMemory,
    ScoredDrumGesture,
    build_immediate_candidates,
    perform_one_gesture,
    score_gesture,
)
from .timing import (
    SwingTimingPrior,
    bounded_timing_offset_ms,
    is_ride_anchor,
    ride_positions_in_two_beat_cell,
    tempo_conditioned_swing_prior,
)

__all__ = [
    "CompingPropensity",
    "comping_propensity",
    "DrumGesture",
    "DrumHit",
    "DrummerRuntimeContext",
    "DrummerSoftPlan",
    "DrumVoice",
    "GestureRole",
    "Limb",
    "TimeFeel",
    "PATTERN_CORPUS",
    "PatternHit",
    "PatternUse",
    "SourceRights",
    "StoredDrumPattern",
    "get_pattern",
    "hits_at_current_position",
    "patterns_with_tags",
    "pattern_gesture_now",
    "source_pattern_candidates",
    "DrummerPerformanceMemory",
    "ScoredDrumGesture",
    "build_immediate_candidates",
    "perform_one_gesture",
    "score_gesture",
    "SwingTimingPrior",
    "bounded_timing_offset_ms",
    "is_ride_anchor",
    "ride_positions_in_two_beat_cell",
    "tempo_conditioned_swing_prior",
]
