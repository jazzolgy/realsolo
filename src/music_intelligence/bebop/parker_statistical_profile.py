"""Compatibility shim. Canonical implementation: music_intelligence.legends.parker.conditional_prior."""
from music_intelligence.legends.parker.conditional_prior import (
    PARKER_SYMBOLIC_MOTION_PROFILE,
    build_symbolic_motion_profile as build_parker_statistical_profile,
)
__all__ = ["PARKER_SYMBOLIC_MOTION_PROFILE", "build_parker_statistical_profile"]
