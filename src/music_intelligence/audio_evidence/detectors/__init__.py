"""Detector interfaces and model-independent composition."""
from .acoustic_instrument_prior import AcousticInstrumentPriorDetector
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
from .learned_instrument import (
    DetectorFeatureEncoder,
    InstrumentFeatureVector,
    InstrumentFeatureEncoder,
    InstrumentProbabilityBackend,
    LearnedInstrumentClassifier,
)
from .librosa_baseline import (
    LibrosaOnsetDetector,
    LibrosaPercussiveTokenDetector,
    LibrosaSourceLoader,
    LibrosaSpectralPeakPitchDetector,
    LibrosaTimbreDetector,
)
from .separation import SeparatedSource, SourceSeparator
from .stem_prior import StemMetadataInstrumentDetector
from .torchscript_instrument import TorchScriptInstrumentBackend

__all__ = [
    "AcousticInstrumentPriorDetector",
    "AudioObservationDetector",
    "CompositeObservationDetector",
    "DemucsCLISeparator",
    "DetectorFeatureEncoder",
    "InstrumentDetection",
    "InstrumentFeatureEncoder",
    "InstrumentFeatureVector",
    "InstrumentProbabilityBackend",
    "InstrumentDetector",
    "LibrosaHPSSSeparator",
    "LibrosaOnsetDetector",
    "LibrosaPercussiveTokenDetector",
    "LibrosaSourceLoader",
    "LibrosaSpectralPeakPitchDetector",
    "LibrosaTimbreDetector",
    "LearnedInstrumentClassifier",
    "OnsetDetection",
    "OnsetDetector",
    "PitchDetection",
    "PitchDetector",
    "SeparatedSource",
    "SourceSeparator",
    "StemMetadataInstrumentDetector",
    "TimbreDetection",
    "TorchScriptInstrumentBackend",
    "TimbreDetector",
    "UnpitchedDetection",
    "UnpitchedDetector",
]
