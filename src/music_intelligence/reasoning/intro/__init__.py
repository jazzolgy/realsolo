"""Shared Intro Intelligence for RealSolo.

The intro layer decides *when and why* ensemble entry is musically appropriate.
It does not generate instrument-specific notes. Player modules remain responsible
for physical realization after a shared entry decision.
"""

from .representation import (
    EntryAction,
    EntryDecision,
    IntroMode,
    IntroModeHypothesis,
    IntroObservation,
    IntroPhase,
    IntroState,
    MeterHypothesis,
)
from .runtime import IntroRuntime, IntroTickResult

__all__ = [
    "EntryAction",
    "EntryDecision",
    "IntroMode",
    "IntroModeHypothesis",
    "IntroObservation",
    "IntroPhase",
    "IntroRuntime",
    "IntroState",
    "IntroTickResult",
    "MeterHypothesis",
]
