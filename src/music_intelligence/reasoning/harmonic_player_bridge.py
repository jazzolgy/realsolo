"""v1.42 player-facing harmonic guidance bridge.

The Harmony Core produces instrument-neutral HarmonicActionOptions. Players
still own concrete realization. This bridge maps current player candidates to
those options without forcing one instrument to share another instrument's
surface grammar.

It supports both monophonic CandidateEvent and PolyphonicEventCandidate via
semantic tags. The bridge adds harmonic guidance as one score component rather
than replacing instrument/style/ensemble evaluation.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping, Sequence

from music_intelligence.harmony.orchestrator import (
    HarmonicActionOption,
    HarmonicReasoningResult,
)

from .legend_style_core import CandidateEvent, CandidateScore
from .polyphonic_event import PolyphonicEventCandidate
from .polyphonic_online import PolyphonicCandidateScore


@dataclass(frozen=True)
class HarmonicCandidateGuidance:
    score_delta: float
    matched_option_ids: tuple[str, ...] = ()
    components: Mapping[str, float] = field(default_factory=dict)
    reasons: tuple[str, ...] = ()


def _tags(candidate: CandidateEvent | PolyphonicEventCandidate) -> frozenset[str]:
    return candidate.tags


def _option_match_strength(
    option: HarmonicActionOption,
    tags: frozenset[str],
) -> float:
    """Semantic bridge from player tags to harmonic action families.

    The mapping is intentionally broad. Instrument branches are free to add
    richer tags while Harmony Core remains instrument-neutral.
    """
    role = option.harmonic_role.lower()
    intent = option.intent.value
    strength = 0.0

    if intent == "stabilize":
        if tags & {
            "chord_tone", "guide_tone", "harmonic_identity",
            "root", "third", "seventh", "stable_harmony",
        }:
            strength = max(strength, .95)

    if intent == "connect":
        if tags & {
            "guide_tone", "resolution_path", "directed_target",
            "close_approach", "passing", "neighbor", "voice_leading",
            "common_tone", "structural_target",
        }:
            strength = max(strength, .95)

    if intent == "color":
        if tags & {
            "tension", "color_tone", "extension", "modal_color",
            "upper_structure", "quartal_color",
        }:
            strength = max(strength, .82)

    if intent == "intensify":
        if tags & {
            "altered", "chromatic", "high_tension", "outside",
            "b9", "sharp9", "b13", "tritone_pressure",
        }:
            strength = max(strength, .92)

    if intent == "delay_resolution":
        if tags & {
            "suspension", "delay_resolution", "held_tension",
            "deceptive", "avoid_immediate_resolution",
        }:
            strength = max(strength, .88)

    if intent == "reharmonize":
        if tags & {
            "reharmonization", "substitute_dominant", "modal_interchange",
            "interpolation", "chromatic_approach_harmony",
        }:
            strength = max(strength, .95)

    if intent == "outside_and_return":
        if tags & {
            "outside", "side_slip", "sequence_outside",
            "return_path", "long_range_target",
        }:
            strength = max(strength, .90)

    if intent == "anticipate":
        if tags & {
            "anticipation", "future_harmony", "next_chord_target",
            "next_chord_guide_tone",
        }:
            strength = max(strength, .95)

    # Role-specific matches can strengthen an otherwise generic intent match.
    role_tokens = set(role.replace("/", "_").replace("-", "_").split("_"))
    if role_tokens & tags:
        strength = max(strength, .72)

    return strength


def harmonic_guidance_for_candidate(
    candidate: CandidateEvent | PolyphonicEventCandidate,
    harmony: HarmonicReasoningResult,
    *,
    max_delta: float = .30,
) -> HarmonicCandidateGuidance:
    tags = _tags(candidate)
    total = 0.0
    components: dict[str, float] = {}
    reasons: list[str] = []
    matched: list[str] = []

    for option in harmony.action_options:
        match = _option_match_strength(option, tags)
        if match <= 0:
            continue

        # Both weight and confidence matter; compatibility was already folded
        # into the option by the orchestrator.
        contribution = option.weight * option.confidence * match
        if contribution == 0:
            continue

        total += contribution
        components[f"harmony:{option.option_id}"] = contribution
        matched.append(option.option_id)
        reasons.append(
            f"matches harmonic action {option.option_id}"
        )

    # High uncertainty should reduce how strongly Harmony Core can bias a
    # player's concrete realization.
    certainty = max(0.0, 1.0 - harmony.uncertainty)
    total *= .55 + .45 * certainty

    total = max(-max_delta, min(max_delta, total))
    return HarmonicCandidateGuidance(
        score_delta=total,
        matched_option_ids=tuple(matched),
        components=components,
        reasons=tuple(reasons),
    )


def apply_harmonic_guidance_to_monophonic_score(
    base: CandidateScore,
    harmony: HarmonicReasoningResult,
) -> CandidateScore:
    guidance = harmonic_guidance_for_candidate(base.candidate, harmony)
    components = dict(base.components)
    components.update(guidance.components)
    if guidance.score_delta:
        components["harmonic_guidance_total"] = guidance.score_delta
    return CandidateScore(
        candidate=base.candidate,
        total=base.total + guidance.score_delta,
        components=components,
        reasons=base.reasons + guidance.reasons,
    )


def apply_harmonic_guidance_to_polyphonic_score(
    base: PolyphonicCandidateScore,
    harmony: HarmonicReasoningResult,
) -> PolyphonicCandidateScore:
    guidance = harmonic_guidance_for_candidate(base.candidate, harmony)
    components = dict(base.components)
    components.update(guidance.components)
    if guidance.score_delta:
        components["harmonic_guidance_total"] = guidance.score_delta
    return PolyphonicCandidateScore(
        candidate=base.candidate,
        total=base.total + guidance.score_delta,
        components=components,
        reasons=base.reasons + guidance.reasons,
    )


def rerank_monophonic_with_harmony(
    scores: Sequence[CandidateScore],
    harmony: HarmonicReasoningResult,
) -> tuple[CandidateScore, ...]:
    return tuple(sorted(
        (
            apply_harmonic_guidance_to_monophonic_score(score, harmony)
            for score in scores
        ),
        key=lambda x: x.total,
        reverse=True,
    ))


def rerank_polyphonic_with_harmony(
    scores: Sequence[PolyphonicCandidateScore],
    harmony: HarmonicReasoningResult,
) -> tuple[PolyphonicCandidateScore, ...]:
    return tuple(sorted(
        (
            apply_harmonic_guidance_to_polyphonic_score(score, harmony)
            for score in scores
        ),
        key=lambda x: x.total,
        reverse=True,
    ))
