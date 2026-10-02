"""Current Parker runtime blend, organized by function rather than research version."""
from music_intelligence.reasoning.legend_style_core import LegendBlend
from .profile import PARKER_ONLINE_PROFILE, PARKER_PROFILE_VIEW
from .conditional_prior import PARKER_SYMBOLIC_MOTION_PROFILE

PARKER_RUNTIME_BLEND = PARKER_PROFILE_VIEW.blend()

# Historical aliases remain for downstream compatibility only.
PARKER_V131_BLEND = LegendBlend((
    (PARKER_ONLINE_PROFILE, 1.0),
    (PARKER_SYMBOLIC_MOTION_PROFILE, 0.65),
))
PARKER_V132_BLEND = PARKER_RUNTIME_BLEND
