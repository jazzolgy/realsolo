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
