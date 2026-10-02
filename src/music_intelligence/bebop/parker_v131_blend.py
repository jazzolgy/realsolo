"""v1.31 Parker runtime blend with explicit evidence hierarchy."""
from music_intelligence.reasoning.legend_style_core import LegendBlend
from .parker_online_profile import PARKER_ONLINE_PROFILE
from .parker_statistical_profile import PARKER_SYMBOLIC_MOTION_PROFILE

# Research/expert tendencies retain full weight. Pedagogical symbolic evidence is
# bounded and cannot overrule live ensemble evidence.
PARKER_V131_BLEND = LegendBlend((
    (PARKER_ONLINE_PROFILE, 1.0),
    (PARKER_SYMBOLIC_MOTION_PROFILE, 0.65),
))
