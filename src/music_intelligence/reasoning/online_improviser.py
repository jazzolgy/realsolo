"""v1.31 online improvisation commitment contract.

The player may plan intentions and candidate families in advance, but it must not
freeze a future note sequence and replay it as pseudo-improvisation.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Sequence
from .legend_style_core import CandidateEvent, CandidateScore, MusicalContextVector, LegendBlend


@dataclass(frozen=True)
class SoftPlan:
    horizon_beats: float
    intention: str
    soft_targets: tuple[str, ...] = ()
    candidate_families: tuple[str, ...] = ()
    register_direction: str = "stable"
    density_direction: str = "stable"
    exact_future_notes: tuple[int, ...] = ()

    def validate_for_improvisation(self) -> None:
        if self.horizon_beats < 0:
            raise ValueError("negative horizon")
        if self.exact_future_notes:
            raise ValueError("Slow Brain may not freeze exact future note sequences")


@dataclass
class PerformanceMemory:
    committed: list[CandidateEvent] = field(default_factory=list)

    def commit(self, event: CandidateEvent) -> None:
        self.committed.append(event)


class OnlineMusicalEvaluator:
    """Hot-path evaluator. It scores only events that have not yet been played."""

    def __init__(self, legend_blend: LegendBlend | None = None):
        self.legend_blend = legend_blend

    def evaluate(self, candidate: CandidateEvent, context: MusicalContextVector) -> CandidateScore:
        score = 0.0
        reasons: list[str] = []
        comp: dict[str, float] = {}

        if "chord_tone" in candidate.tags or "guide_tone" in candidate.tags:
            v = 0.28 if context.phrase_maturity < .35 else 0.14
            score += v
            comp["harmonic_identity"] = v
            reasons.append("harmonic identity")

        if {"close_approach", "neighbor", "passing"} & set(candidate.tags):
            v = 0.14
            score += v
            comp["melodic_connector"] = v
            reasons.append("close melodic connector")

        if "large_leap" in candidate.tags and context.recent_large_leaps > 0:
            v = -0.26 * min(2, context.recent_large_leaps)
            score += v
            comp["leap_budget"] = v
            reasons.append("recent leap budget")

        if "altered" in candidate.tags:
            obscured = (
                context.recent_chord_identity_strength < .30
                and context.recent_altered_density > .55
            )
            directed = (
                "directed_target" in candidate.tags
                or "resolution_path" in candidate.tags
            )
            if obscured and not directed:
                v = -0.16
                score += v
                comp["identity_occlusion"] = v
                reasons.append("dominant identity obscured")
            else:
                v = 0.08
                score += v
                comp["altered_color"] = v
                reasons.append("contextual altered color")

        if "anticipation" in candidate.tags and candidate.onset_offset_beats < 0:
            v = 0.12
            score += v
            comp["anticipation"] = v
            reasons.append("future-harmony anticipation")

        if "ensemble_space" in candidate.tags and context.ensemble_activity > .65:
            v = 0.20
            score += v
            comp["ensemble_handoff"] = v
            reasons.append("ensemble handoff")

        if self.legend_blend:
            active_tags = set(candidate.tags)
            if context.phrase_maturity < .33:
                active_tags.add("phrase_early")
            elif context.phrase_maturity < .67:
                active_tags.add("phrase_middle")
            else:
                active_tags.add("phrase_late")

            if candidate.pitch_midi is not None and context.previous_pitch_midi is not None:
                interval = candidate.pitch_midi - context.previous_pitch_midi
                abs_interval = abs(interval)

                if abs_interval <= 2:
                    active_tags.add("step_motion")
                if abs_interval <= 5:
                    active_tags.add("within_p4_motion")
                if abs_interval >= 7:
                    active_tags.add("wide_leap")

                prev = context.previous_interval_semitones
                if prev is not None and abs(prev) >= 7:
                    active_tags.add("after_wide_leap")
                    if prev * interval < 0:
                        active_tags.add("contrary_recovery")
                    if abs_interval <= 5:
                        active_tags.add("recovery_within_p4")

                recent = tuple(context.recent_pitches[-3:]) + (candidate.pitch_midi,)
                if len(recent) >= 3 and max(recent[-3:]) - min(recent[-3:]) > 12:
                    active_tags.add("compound_span_pressure")
                if len(recent) >= 4 and max(recent[-4:]) - min(recent[-4:]) > 12:
                    active_tags.add("compound_span_pressure")

            if candidate.duration_beats >= 1.0 and context.phrase_maturity >= .67:
                active_tags.add("structural_terminal_long_tone")

            for feature in active_tags:
                bias = self.legend_blend.feature_bias(feature, active_tags=active_tags)
                if bias:
                    score += bias
                    comp[f"legend:{feature}"] = bias

        return CandidateScore(candidate, score, comp, tuple(reasons))

    def choose_immediate(
        self,
        candidates: Sequence[CandidateEvent],
        context: MusicalContextVector,
    ) -> CandidateScore:
        if not candidates:
            raise ValueError("no candidates")
        return max((self.evaluate(c, context) for c in candidates), key=lambda x: x.total)


def perform_one_event(
    plan: SoftPlan,
    evaluator: OnlineMusicalEvaluator,
    candidates: Sequence[CandidateEvent],
    context: MusicalContextVector,
    memory: PerformanceMemory,
) -> CandidateScore:
    """Commit exactly one event; after this call the system must listen/re-plan."""
    plan.validate_for_improvisation()
    chosen = evaluator.choose_immediate(candidates, context)
    memory.commit(chosen.candidate)
    return chosen
