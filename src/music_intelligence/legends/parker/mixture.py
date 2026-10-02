"""Current Parker runtime blend, organized by function rather than research version."""
from music_intelligence.reasoning.legend_style_core import LegendBlend
from .profile import PARKER_ONLINE_PROFILE
from .conditional_prior import PARKER_SYMBOLIC_MOTION_PROFILE
from .phrase_prior import PARKER_PHRASE_SPACE_PROFILE

PARKER_RUNTIME_BLEND = LegendBlend((
    (PARKER_ONLINE_PROFILE, 1.0),
    (PARKER_SYMBOLIC_MOTION_PROFILE, 0.65),
    (PARKER_PHRASE_SPACE_PROFILE, 0.55),
))

# Historical aliases remain for downstream compatibility only.
PARKER_V131_BLEND = LegendBlend((
    (PARKER_ONLINE_PROFILE, 1.0),
    (PARKER_SYMBOLIC_MOTION_PROFILE, 0.65),
))
PARKER_V132_BLEND = PARKER_RUNTIME_BLEND
