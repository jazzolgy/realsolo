"""v1.32 Parker runtime evidence blend."""
from music_intelligence.reasoning.legend_style_core import LegendBlend
from .parker_online_profile import PARKER_ONLINE_PROFILE
from .parker_statistical_profile import PARKER_SYMBOLIC_MOTION_PROFILE
from .parker_phrase_space_profile import PARKER_PHRASE_SPACE_PROFILE

PARKER_V132_BLEND = LegendBlend((
    (PARKER_ONLINE_PROFILE, 1.0),
    (PARKER_SYMBOLIC_MOTION_PROFILE, 0.65),
    (PARKER_PHRASE_SPACE_PROFILE, 0.55),
))
