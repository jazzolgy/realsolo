"""Shared, instrument-neutral jazz harmony intelligence."""

from .jazz_harmony_core import (
    HarmonicAffordance,
    HarmonicEvidence,
    HarmonicFrame,
    HarmonicIntent,
    HarmonySource,
    TensionChoice,
    build_basic_affordances,
)
from .functional_graph import (
    FunctionFamily,
    FunctionalEdge,
    FunctionalNode,
    HarmonicFunctionGraph,
    MetricStress,
    ResolutionKind,
    dominant_expected_resolution,
    infer_dominant_family,
    make_resolution_edge,
)
from .contextual_tension import (
    MusicalLayer,
    TensionAssessment,
    TensionContext,
    TensionUse,
    assess_tension,
)

__all__ = [
    "HarmonicAffordance",
    "HarmonicEvidence",
    "HarmonicFrame",
    "HarmonicIntent",
    "HarmonySource",
    "TensionChoice",
    "build_basic_affordances",
    "FunctionFamily",
    "FunctionalEdge",
    "FunctionalNode",
    "HarmonicFunctionGraph",
    "MetricStress",
    "ResolutionKind",
    "dominant_expected_resolution",
    "infer_dominant_family",
    "make_resolution_edge",
    "MusicalLayer",
    "TensionAssessment",
    "TensionContext",
    "TensionUse",
    "assess_tension",
]
