"""Context-sensitive gating for hierarchical learned priors.

Live musical context may attenuate learned/style/legend priors without mutating
or deleting them. This keeps current musical evidence authoritative while
preserving learned tendencies as soft guidance.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .hierarchical_priors import HierarchicalPriorSet, PriorLayerWeights


class PerformanceMode(str, Enum):
    IMPROVISATION = "improvisation"
    HEAD = "head"
    INTRO = "intro"
    OUTRO = "outro"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class PriorGatingContext:
    performance_mode: PerformanceMode = PerformanceMode.IMPROVISATION
    ensemble_complexity: float = 0.5
    live_context_confidence: float = 0.5
    written_material_priority: float = 0.0
    structural_constraint: float = 0.0

    def validate(self) -> None:
        for name in (
            "ensemble_complexity",
            "live_context_confidence",
            "written_material_priority",
            "structural_constraint",
        ):
            value=getattr(self,name)
            if not 0.0<=value<=1.0:
                raise ValueError(f"{name} must be within 0..1")


@dataclass(frozen=True)
class PriorGateResult:
    weights: PriorLayerWeights
    reasons: tuple[str,...] = ()


def derive_prior_gate(
    base: PriorLayerWeights,
    context: PriorGatingContext,
) -> PriorGateResult:
    """Attenuate prior layers when live/structural evidence should dominate.

    This function never increases a layer above its configured base weight.
    """

    base.validate()
    context.validate()

    domain=base.domain
    genre=base.genre
    style=base.style
    legend=base.legend
    reasons=[]

    # Written material (especially a head) should dominate learned improvisation
    # habits. Domain priors are attenuated, while genre/style/legend are reduced
    # more strongly.
    if context.written_material_priority>0:
        p=context.written_material_priority
        domain*=1.0-.75*p
        genre*=1.0-.90*p
        style*=1.0-.90*p
        legend*=1.0-.92*p
        reasons.append("written material priority attenuates learned improvisation priors")

    # Dense/complex ensemble state should favor immediate listening over historic
    # stylistic habits.
    if context.ensemble_complexity>0:
        c=context.ensemble_complexity
        domain*=1.0-.20*c
        genre*=1.0-.35*c
        style*=1.0-.45*c
        legend*=1.0-.50*c
        reasons.append("ensemble complexity shifts authority toward live interaction")

    # When current observations are highly reliable, priors should become less
    # assertive rather than compete with strong live evidence.
    if context.live_context_confidence>0:
        q=context.live_context_confidence
        domain*=1.0-.15*q
        genre*=1.0-.25*q
        style*=1.0-.30*q
        legend*=1.0-.35*q
        reasons.append("high-confidence live evidence attenuates historical priors")

    # Strong structural/form constraints should reduce stylistic freedom.
    if context.structural_constraint>0:
        s=context.structural_constraint
        domain*=1.0-.25*s
        genre*=1.0-.35*s
        style*=1.0-.45*s
        legend*=1.0-.50*s
        reasons.append("structural constraints reduce prior freedom")

    return PriorGateResult(
        PriorLayerWeights(
            domain=max(0.0,domain),
            genre=max(0.0,genre),
            style=max(0.0,style),
            legend=max(0.0,legend),
        ),
        tuple(reasons),
    )


def gated_prior_set(
    priors: HierarchicalPriorSet | None,
    context: PriorGatingContext,
) -> HierarchicalPriorSet | None:
    if priors is None:
        return None
    priors.validate()
    gated=derive_prior_gate(priors.weights,context)
    return HierarchicalPriorSet(
        domain_prior=priors.domain_prior,
        genre_prior=priors.genre_prior,
        style_prior=priors.style_prior,
        legend_blend=priors.legend_blend,
        weights=gated.weights,
    )


def head_gating_context(
    *,
    mode: str,
    ensemble_complexity: float = 0.5,
    live_context_confidence: float = 0.8,
) -> PriorGatingContext:
    """Map Head Fidelity mode into prior attenuation without importing head_fidelity."""

    normalized=mode.lower()
    if normalized=="strict":
        written=1.0
        structural=1.0
    elif normalized=="natural":
        written=.88
        structural=.85
    elif normalized=="loose":
        written=.60
        structural=.55
    else:
        raise ValueError("head mode must be strict, natural or loose")
    return PriorGatingContext(
        performance_mode=PerformanceMode.HEAD,
        ensemble_complexity=ensemble_complexity,
        live_context_confidence=live_context_confidence,
        written_material_priority=written,
        structural_constraint=structural,
    )


def improvisation_gating_context(
    *,
    ensemble_complexity: float,
    live_context_confidence: float,
    structural_constraint: float = 0.0,
) -> PriorGatingContext:
    """Build a gating context for open improvisation from live evidence."""

    return PriorGatingContext(
        performance_mode=PerformanceMode.IMPROVISATION,
        ensemble_complexity=ensemble_complexity,
        live_context_confidence=live_context_confidence,
        written_material_priority=0.0,
        structural_constraint=structural_constraint,
    )


def domain_prior_gate_scale(context: PriorGatingContext) -> float:
    """Return a 0..1 attenuation scale for a standalone domain prior."""

    result = derive_prior_gate(
        PriorLayerWeights(domain=1.0, genre=0.0, style=0.0, legend=0.0),
        context,
    )
    return max(0.0, min(1.0, result.weights.domain))
