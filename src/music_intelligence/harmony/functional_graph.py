"""v1.35 functional relationship graph for shared jazz harmony.

The graph describes relationships and expectations, not a chord-to-scale
lookup. A dominant may keep its functional identity even when its actual
resolution is deceptive. Harmonic rhythm / metric stress are explicit context
because Berklee's dominant taxonomy depends partly on placement and continuation.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Iterable


class FunctionFamily(str, Enum):
    TONIC = "tonic"
    PREDOMINANT = "predominant"
    PRIMARY_DOMINANT = "primary_dominant"
    SECONDARY_DOMINANT = "secondary_dominant"
    EXTENDED_DOMINANT = "extended_dominant"
    SUBSTITUTE_DOMINANT = "substitute_dominant"
    EXTENDED_SUBSTITUTE_DOMINANT = "extended_substitute_dominant"
    SPECIAL_FUNCTION_DOMINANT = "special_function_dominant"
    MODAL_TONIC = "modal_tonic"
    MODAL_NONTONIC = "modal_nontonic"
    NONFUNCTIONAL = "nonfunctional"
    UNKNOWN = "unknown"


class ResolutionKind(str, Enum):
    DOWN_PERFECT_FIFTH = "down_perfect_fifth"
    DOWN_HALF_STEP = "down_half_step"
    DECEPTIVE = "deceptive"
    CONTINUATION = "continuation"
    MODAL_RETURN = "modal_return"
    NONE = "none"


class MetricStress(str, Enum):
    STRONG = "strong"
    WEAK = "weak"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class FunctionalNode:
    node_id: str
    root_pc: int | None
    symbol: str | None
    family: FunctionFamily
    key_context: str | None = None
    target_degree: str | None = None
    metric_stress: MetricStress = MetricStress.UNKNOWN
    confidence: float = 1.0
    provenance: tuple[str, ...] = ()

    def validate(self) -> None:
        if self.root_pc is not None and not 0 <= self.root_pc <= 11:
            raise ValueError("root_pc must be in 0..11")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be within 0..1")


@dataclass(frozen=True)
class FunctionalEdge:
    source_id: str
    target_id: str
    expected_resolution: ResolutionKind
    actual_resolution: ResolutionKind | None = None
    root_motion_semitones: int | None = None
    preserves_source_function: bool = True
    confidence: float = 1.0
    provenance: tuple[str, ...] = ()
    note: str = ""

    @property
    def is_deceptive(self) -> bool:
        return self.actual_resolution is ResolutionKind.DECEPTIVE

    def validate(self) -> None:
        if not self.source_id or not self.target_id:
            raise ValueError("edge endpoints are required")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be within 0..1")


@dataclass
class HarmonicFunctionGraph:
    nodes: dict[str, FunctionalNode] = field(default_factory=dict)
    edges: list[FunctionalEdge] = field(default_factory=list)

    def add_node(self, node: FunctionalNode) -> None:
        node.validate()
        if node.node_id in self.nodes:
            raise ValueError(f"duplicate node_id: {node.node_id}")
        self.nodes[node.node_id] = node

    def add_edge(self, edge: FunctionalEdge) -> None:
        edge.validate()
        if edge.source_id not in self.nodes or edge.target_id not in self.nodes:
            raise ValueError("edge references unknown node")
        self.edges.append(edge)

    def outgoing(self, node_id: str) -> tuple[FunctionalEdge, ...]:
        return tuple(x for x in self.edges if x.source_id == node_id)

    def expected_targets(self, node_id: str) -> tuple[str, ...]:
        return tuple(x.target_id for x in self.outgoing(node_id))

    def dominant_chain(self) -> tuple[FunctionalNode, ...]:
        families = {
            FunctionFamily.PRIMARY_DOMINANT,
            FunctionFamily.SECONDARY_DOMINANT,
            FunctionFamily.EXTENDED_DOMINANT,
            FunctionFamily.SUBSTITUTE_DOMINANT,
            FunctionFamily.EXTENDED_SUBSTITUTE_DOMINANT,
        }
        return tuple(n for n in self.nodes.values() if n.family in families)


def dominant_expected_resolution(family: FunctionFamily) -> ResolutionKind:
    if family in {
        FunctionFamily.SUBSTITUTE_DOMINANT,
        FunctionFamily.EXTENDED_SUBSTITUTE_DOMINANT,
    }:
        return ResolutionKind.DOWN_HALF_STEP
    if family in {
        FunctionFamily.PRIMARY_DOMINANT,
        FunctionFamily.SECONDARY_DOMINANT,
        FunctionFamily.EXTENDED_DOMINANT,
    }:
        return ResolutionKind.DOWN_PERFECT_FIFTH
    return ResolutionKind.NONE


def infer_dominant_family(
    *,
    root_is_diatonic: bool | None,
    target_is_tonic: bool = False,
    metric_stress: MetricStress = MetricStress.UNKNOWN,
    continues_dominant_chain: bool = False,
    shares_primary_tritone: bool = False,
    special_function: str | None = None,
) -> FunctionFamily:
    """Bounded Berklee-style dominant-family inference.

    It returns one useful hypothesis from explicit context and should coexist
    with alternative analyses in UMR.
    """
    if special_function:
        return FunctionFamily.SPECIAL_FUNCTION_DOMINANT
    if shares_primary_tritone:
        return (
            FunctionFamily.EXTENDED_SUBSTITUTE_DOMINANT
            if continues_dominant_chain
            else FunctionFamily.SUBSTITUTE_DOMINANT
        )
    if target_is_tonic and not continues_dominant_chain:
        return FunctionFamily.PRIMARY_DOMINANT
    if continues_dominant_chain or metric_stress is MetricStress.STRONG:
        return FunctionFamily.EXTENDED_DOMINANT
    if root_is_diatonic is True or metric_stress is MetricStress.WEAK:
        return FunctionFamily.SECONDARY_DOMINANT
    return FunctionFamily.UNKNOWN


def root_motion_pc(source_root: int, target_root: int) -> int:
    raw = (target_root - source_root) % 12
    return raw if raw <= 6 else raw - 12


def make_resolution_edge(
    source: FunctionalNode,
    target: FunctionalNode,
    *,
    actual_deceptive: bool = False,
    confidence: float = 1.0,
    provenance: Iterable[str] = (),
) -> FunctionalEdge:
    expected = dominant_expected_resolution(source.family)
    actual = ResolutionKind.DECEPTIVE if actual_deceptive else expected
    motion = None
    if source.root_pc is not None and target.root_pc is not None:
        motion = root_motion_pc(source.root_pc, target.root_pc)
    return FunctionalEdge(
        source.node_id,
        target.node_id,
        expected_resolution=expected,
        actual_resolution=actual,
        root_motion_semitones=motion,
        preserves_source_function=True,
        confidence=confidence,
        provenance=tuple(provenance),
        note=(
            "Deceptive destination does not retroactively erase the dominant hypothesis."
            if actual_deceptive else ""
        ),
    )
