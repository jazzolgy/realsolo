"""Player-neutral runtime policy projection facade.

This module does not add a new musical decision engine. It normalizes already
computed learning/style/legend/motif signals into one bounded soft-policy
contract that Players may realize with their own instrument grammar.

No concrete pitch, voicing, string, limb, or rendered event may appear here.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Mapping

from .contextual_prior_gating import PriorGatingContext, gated_prior_set
from .hierarchical_priors import HierarchicalPriorSet, legend_feature_bias
from .motif.policy import MotifPolicyDecision
from .solo_grammar import SoloDevelopmentOperation


class MusicalPolicyAxis(str, Enum):
    MOTIF_REPEAT = "motif_repeat"
    MOTIF_VARIATION = "motif_variation"
    RHYTHMIC_DISPLACEMENT = "rhythmic_displacement"
    CONTINUITY = "continuity"
    HARMONIC_RETARGET = "harmonic_retarget"
    SPACE = "space"
    FOREGROUND_ENTRY = "foreground_entry"
    DENSITY_DIRECTION = "density_direction"
    REGISTER_DIRECTION = "register_direction"


# Canonical policy features are already-semantic 0..1 tendencies. The facade
# deliberately ignores arbitrary raw learning metrics.
_CANONICAL_FEATURES: dict[MusicalPolicyAxis, str] = {
    MusicalPolicyAxis.MOTIF_REPEAT: "policy.motif_repeat",
    MusicalPolicyAxis.MOTIF_VARIATION: "policy.motif_variation",
    MusicalPolicyAxis.RHYTHMIC_DISPLACEMENT: "policy.rhythmic_displacement",
    MusicalPolicyAxis.CONTINUITY: "policy.continuity",
    MusicalPolicyAxis.HARMONIC_RETARGET: "policy.harmonic_retarget",
    MusicalPolicyAxis.SPACE: "policy.space",
    MusicalPolicyAxis.FOREGROUND_ENTRY: "policy.foreground_entry",
    MusicalPolicyAxis.DENSITY_DIRECTION: "policy.density_direction",
    MusicalPolicyAxis.REGISTER_DIRECTION: "policy.register_direction",
}


_LEGEND_FEATURES: dict[MusicalPolicyAxis, tuple[str, ...]] = {
    MusicalPolicyAxis.MOTIF_REPEAT: (
        "solo.rhythmic_motif_persistence",
        "solo.productive_repetition",
    ),
    MusicalPolicyAxis.MOTIF_VARIATION: (
        "solo.subdivision_variation",
    ),
    MusicalPolicyAxis.RHYTHMIC_DISPLACEMENT: (
        "solo.rhythmic_displacement",
    ),
    MusicalPolicyAxis.CONTINUITY: (
        "solo.linear_scale_arpeggio_motion",
    ),
    MusicalPolicyAxis.HARMONIC_RETARGET: (
        "solo.linear_scale_arpeggio_motion",
    ),
}


_MOTIF_OPERATION_AXES: dict[SoloDevelopmentOperation, tuple[tuple[MusicalPolicyAxis, float], ...]] = {
    SoloDevelopmentOperation.REPEAT: ((MusicalPolicyAxis.MOTIF_REPEAT, .12),),
    SoloDevelopmentOperation.RECAP: ((MusicalPolicyAxis.MOTIF_REPEAT, .10),),
    SoloDevelopmentOperation.VARY: ((MusicalPolicyAxis.MOTIF_VARIATION, .12),),
    SoloDevelopmentOperation.FRAGMENT: ((MusicalPolicyAxis.MOTIF_VARIATION, .10),),
    SoloDevelopmentOperation.SEQUENCE: (
        (MusicalPolicyAxis.CONTINUITY, .11),
        (MusicalPolicyAxis.HARMONIC_RETARGET, .04),
    ),
    SoloDevelopmentOperation.DISPLACE: ((MusicalPolicyAxis.RHYTHMIC_DISPLACEMENT, .13),),
    SoloDevelopmentOperation.ADD_SPACE: ((MusicalPolicyAxis.SPACE, .14),),
    SoloDevelopmentOperation.INTERNAL_REST: ((MusicalPolicyAxis.SPACE, .14),),
    SoloDevelopmentOperation.CHANGE_REGISTER: ((MusicalPolicyAxis.REGISTER_DIRECTION, .12),),
    SoloDevelopmentOperation.REORCHESTRATE: ((MusicalPolicyAxis.REGISTER_DIRECTION, .10),),
    SoloDevelopmentOperation.TARGET_NEXT_HARMONY: ((MusicalPolicyAxis.HARMONIC_RETARGET, .11),),
    SoloDevelopmentOperation.RESOLVE: ((MusicalPolicyAxis.HARMONIC_RETARGET, .08),),
    SoloDevelopmentOperation.EXTEND: ((MusicalPolicyAxis.CONTINUITY, .09),),
}


@dataclass(frozen=True)
class PolicyContribution:
    axis: MusicalPolicyAxis
    source: str
    value: float
    reason: str = ""
    provenance: tuple[str, ...] = ()

    def validate(self) -> None:
        if not self.source:
            raise ValueError("policy contribution source is required")
        if not -1.0 <= self.value <= 1.0:
            raise ValueError("policy contribution value must be within -1..1")


@dataclass(frozen=True)
class MusicalPolicyProjection:
    """Instrument-neutral soft policy for one musical moment."""

    motif_repeat_bias: float = 0.0
    motif_variation_bias: float = 0.0
    rhythmic_displacement_bias: float = 0.0
    continuity_bias: float = 0.0
    harmonic_retarget_bias: float = 0.0
    space_bias: float = 0.0
    foreground_entry_bias: float = 0.0
    density_direction: float = 0.0
    register_direction: float = 0.0
    confidence: float = 0.0
    contributions: tuple[PolicyContribution, ...] = ()
    provenance: tuple[str, ...] = ()

    def validate(self) -> None:
        for name in (
            "motif_repeat_bias",
            "motif_variation_bias",
            "rhythmic_displacement_bias",
            "continuity_bias",
            "harmonic_retarget_bias",
            "space_bias",
            "foreground_entry_bias",
            "density_direction",
            "register_direction",
        ):
            value = getattr(self, name)
            if not -1.0 <= value <= 1.0:
                raise ValueError(f"{name} must be within -1..1")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be within 0..1")
        for contribution in self.contributions:
            contribution.validate()

    def axis_value(self, axis: MusicalPolicyAxis) -> float:
        return {
            MusicalPolicyAxis.MOTIF_REPEAT: self.motif_repeat_bias,
            MusicalPolicyAxis.MOTIF_VARIATION: self.motif_variation_bias,
            MusicalPolicyAxis.RHYTHMIC_DISPLACEMENT: self.rhythmic_displacement_bias,
            MusicalPolicyAxis.CONTINUITY: self.continuity_bias,
            MusicalPolicyAxis.HARMONIC_RETARGET: self.harmonic_retarget_bias,
            MusicalPolicyAxis.SPACE: self.space_bias,
            MusicalPolicyAxis.FOREGROUND_ENTRY: self.foreground_entry_bias,
            MusicalPolicyAxis.DENSITY_DIRECTION: self.density_direction,
            MusicalPolicyAxis.REGISTER_DIRECTION: self.register_direction,
        }[axis]


def _clip(value: float, bound: float = .35) -> float:
    return max(-bound, min(bound, value))


def _learned_axis_contributions(
    priors: HierarchicalPriorSet,
) -> tuple[PolicyContribution, ...]:
    out: list[PolicyContribution] = []
    for axis, feature in _CANONICAL_FEATURES.items():
        for layer, prior, layer_weight in (
            ("domain", priors.domain_prior, priors.weights.domain),
            ("genre", priors.genre_prior, priors.weights.genre),
            ("style", priors.style_prior, priors.weights.style),
        ):
            if prior is None or layer_weight <= 0:
                continue
            if feature not in prior.numeric_features and feature not in prior.feedback_bias:
                continue
            # Canonical policy features are normalized directional preferences:
            # 0.5 is neutral; values above/below it push the axis +/-.
            value = prior.feature_bias(feature, center=.5, scale=.20) * layer_weight
            value = _clip(value, .20)
            if value:
                out.append(PolicyContribution(
                    axis=axis,
                    source=f"learning:{layer}",
                    value=value,
                    reason=f"{layer} canonical policy feature {feature}",
                    provenance=(f"learning_prior:{prior.domain.value}", feature),
                ))
    return tuple(out)


def _legend_axis_contributions(
    priors: HierarchicalPriorSet,
    *,
    active_tags: tuple[str, ...],
) -> tuple[PolicyContribution, ...]:
    out: list[PolicyContribution] = []
    for axis, features in _LEGEND_FEATURES.items():
        for feature in features:
            bias = legend_feature_bias(priors, feature=feature, active_tags=active_tags)
            if not bias.active:
                continue
            out.append(PolicyContribution(
                axis=axis,
                source="legend",
                value=_clip(bias.score_delta, .20),
                reason=bias.reason,
                provenance=(f"legend_feature:{feature}",),
            ))
    return tuple(out)


def _motif_contributions(
    decision: MotifPolicyDecision | None,
) -> tuple[PolicyContribution, ...]:
    if decision is None:
        return ()
    mappings = _MOTIF_OPERATION_AXES.get(decision.development_operation, ())
    if not mappings:
        return ()

    # The operation has already been selected by Motif Policy. We only expose
    # that decision as a modest soft signal; we do not decide it again.
    confidence = max(0.25, min(1.0, decision.evaluation.total))
    return tuple(
        PolicyContribution(
            axis=axis,
            source="motif_policy",
            value=_clip(value * confidence, .16),
            reason=f"motif policy selected {decision.development_operation.value}",
            provenance=decision.candidate.identity.provenance,
        )
        for axis, value in mappings
    )


def project_musical_policy(
    *,
    priors: HierarchicalPriorSet | None = None,
    gating_context: PriorGatingContext | None = None,
    motif_decision: MotifPolicyDecision | None = None,
    active_tags: tuple[str, ...] = (),
) -> MusicalPolicyProjection:
    """Normalize existing intelligence outputs into one player-neutral contract.

    This function neither selects notes nor changes any upstream learner,
    hierarchy, gating rule, legend logic, or motif policy.
    """

    working = priors
    provenance: list[str] = []
    if working is not None:
        working.validate()
        if gating_context is not None:
            working = gated_prior_set(working, gating_context)
            provenance.append("contextual_prior_gating")
        provenance.append("hierarchical_priors")

    contributions: list[PolicyContribution] = []
    if working is not None:
        contributions.extend(_learned_axis_contributions(working))
        contributions.extend(_legend_axis_contributions(working, active_tags=active_tags))
    contributions.extend(_motif_contributions(motif_decision))

    sums: dict[MusicalPolicyAxis, float] = {axis: 0.0 for axis in MusicalPolicyAxis}
    for contribution in contributions:
        contribution.validate()
        sums[contribution.axis] += contribution.value

    # Final projection remains deliberately soft. Player grammar and current
    # evidence stay authoritative.
    values = {axis: _clip(value) for axis, value in sums.items()}

    source_count = len({c.source for c in contributions})
    confidence = 0.0
    if contributions:
        confidence = min(
            1.0,
            .30 + .12 * source_count + .04 * min(6, len(contributions)),
        )
    if motif_decision is not None:
        provenance.append(f"motif:{motif_decision.candidate.identity.motif_id}")

    projection = MusicalPolicyProjection(
        motif_repeat_bias=values[MusicalPolicyAxis.MOTIF_REPEAT],
        motif_variation_bias=values[MusicalPolicyAxis.MOTIF_VARIATION],
        rhythmic_displacement_bias=values[MusicalPolicyAxis.RHYTHMIC_DISPLACEMENT],
        continuity_bias=values[MusicalPolicyAxis.CONTINUITY],
        harmonic_retarget_bias=values[MusicalPolicyAxis.HARMONIC_RETARGET],
        space_bias=values[MusicalPolicyAxis.SPACE],
        foreground_entry_bias=values[MusicalPolicyAxis.FOREGROUND_ENTRY],
        density_direction=values[MusicalPolicyAxis.DENSITY_DIRECTION],
        register_direction=values[MusicalPolicyAxis.REGISTER_DIRECTION],
        confidence=confidence,
        contributions=tuple(contributions),
        provenance=tuple(provenance),
    )
    projection.validate()
    return projection
