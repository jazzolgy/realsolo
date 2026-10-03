"""Detector interfaces and model-independent composition."""
from .base import AudioObservationDetector
from .composite import CompositeObservationDetector
from .contracts import (
    InstrumentDetection,
    InstrumentDetector,
    OnsetDetection,
    OnsetDetector,
    PitchDetection,
    PitchDetector,
    TimbreDetection,
    TimbreDetector,
    UnpitchedDetection,
    UnpitchedDetector,
)
from .librosa_baseline import (
    LibrosaOnsetDetector,
    LibrosaPercussiveTokenDetector,
    LibrosaSourceLoader,
    LibrosaSpectralPeakPitchDetector,
    LibrosaTimbreDetector,
)
from .separation import SeparatedSource, SourceSeparator

__all__ = [
    "AudioObservationDetector",
    "CompositeObservationDetector",
    "InstrumentDetection",
    "InstrumentDetector",
    "LibrosaOnsetDetector",
    "LibrosaPercussiveTokenDetector",
    "LibrosaSourceLoader",
    "LibrosaSpectralPeakPitchDetector",
    "LibrosaTimbreDetector",
    "OnsetDetection",
    "OnsetDetector",
    "PitchDetection",
    "PitchDetector",
    "SeparatedSource",
    "SourceSeparator",
    "TimbreDetection",
    "TimbreDetector",
    "UnpitchedDetection",
    "UnpitchedDetector",
]
