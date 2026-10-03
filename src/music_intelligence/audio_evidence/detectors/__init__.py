"""Detector interfaces and model-independent composition."""
from .base import AudioObservationDetector
from .composite import CompositeObservationDetector
from .demucs_adapter import DemucsCLISeparator
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
from .hpss_separator import LibrosaHPSSSeparator
from .librosa_baseline import (
    LibrosaOnsetDetector,
    LibrosaPercussiveTokenDetector,
    LibrosaSourceLoader,
    LibrosaSpectralPeakPitchDetector,
    LibrosaTimbreDetector,
)
from .separation import SeparatedSource, SourceSeparator
from .stem_prior import StemMetadataInstrumentDetector

__all__ = [
    "AudioObservationDetector",
    "CompositeObservationDetector",
    "DemucsCLISeparator",
    "InstrumentDetection",
    "InstrumentDetector",
    "LibrosaHPSSSeparator",
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
    "StemMetadataInstrumentDetector",
    "TimbreDetection",
    "TimbreDetector",
    "UnpitchedDetection",
    "UnpitchedDetector",
]
