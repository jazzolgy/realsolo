"""Historical compatibility blend. Canonical runtime blend lives in legends.parker.profile."""
from music_intelligence.reasoning.legend_style_core import LegendBlend
from music_intelligence.legends.parker.profile import PARKER_ONLINE_PROFILE
from music_intelligence.legends.parker.conditional_prior import PARKER_SYMBOLIC_MOTION_PROFILE
PARKER_V131_BLEND = LegendBlend(((PARKER_ONLINE_PROFILE, 1.0), (PARKER_SYMBOLIC_MOTION_PROFILE, .65)))
