"""Shared ensemble-level groove timing contract.

A groove is not owned by any one instrument.  The shared context describes the
ensemble pulse reference; players realize that pulse differently according to
their instrument and role.

Important: "swing" does not mean that every subdivision is forcibly long-short.
It means that swing-eligible offbeats are interpreted against the same temporal
reference while quarter-note pulse, straight sixteenths, tuplets, displacement,
and other local rhythmic devices may remain locally straight when appropriate.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from music_intelligence.learning.engine import LearningPriorView
from .learning_prior_runtime import categorical_prior_bias, strongest_category
from .contextual_prior_gating import (
    PriorGatingContext,
    domain_prior_gate_scale,
)


class GrooveCoordinationMode(str, Enum):
    LOCKED = "locked"
    ELASTIC = "elastic"
    HUMAN_DRIFT = "human_drift"


class GrooveFeel(str, Enum):
    SWING = "swing"
    STRAIGHT = "straight"
    BOSSA = "bossa"
    FUNK = "funk"
    SALSA = "salsa"
    SHUFFLE = "shuffle"
    UNKNOWN = "unknown"


_SWING_RATIO_ANCHORS: tuple[tuple[float, float], ...] = (
    (60.0, 3.2),
    (100.0, 2.6),
    (140.0, 2.0),
    (200.0, 1.55),
    (280.0, 1.18),
    (360.0, 1.05),
)


def _interpolate(x: float, anchors: tuple[tuple[float, float], ...]) -> float:
    if x <= anchors[0][0]:
        return anchors[0][1]
    if x >= anchors[-1][0]:
        return anchors[-1][1]
    for (x0, y0), (x1, y1) in zip(anchors, anchors[1:]):
        if x0 <= x <= x1:
            alpha=(x-x0)/(x1-x0)
            return y0+alpha*(y1-y0)
    raise AssertionError("unreachable interpolation state")


@dataclass(frozen=True)
class GrooveTemporalContext:
    feel: GrooveFeel = GrooveFeel.UNKNOWN
    tempo_bpm: float = 120.0
    meter_numerator: int = 4
    meter_denominator: int = 4
    groove_strength: float = 1.0
    swing_ratio: float | None = None
    grammar_id: str = ""
    subdivision_hint: str = ""
    confidence: float = 1.0
    coordination_mode: GrooveCoordinationMode = GrooveCoordinationMode.ELASTIC
    phase_elasticity: float = 0.55
    swing_elasticity: float = 0.35
    tempo_elasticity: float = 0.0
    provenance: tuple[str, ...] = ("shared_groove_context",)

    def validate(self) -> None:
        if self.tempo_bpm <= 0:
            raise ValueError("tempo_bpm must be positive")
        if self.meter_numerator <= 0 or self.meter_denominator <= 0:
            raise ValueError("meter values must be positive")
        if not 0.0 <= self.groove_strength <= 1.0:
            raise ValueError("groove_strength must be within 0..1")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be within 0..1")
        if self.swing_ratio is not None and self.swing_ratio <= 0:
            raise ValueError("swing_ratio must be positive")
        for name, value in (
            ("phase_elasticity", self.phase_elasticity),
            ("swing_elasticity", self.swing_elasticity),
            ("tempo_elasticity", self.tempo_elasticity),
        ):
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{name} must be within 0..1")

    @property
    def effective_swing_ratio(self) -> float:
        self.validate()
        if self.swing_ratio is not None:
            return self.swing_ratio
        return _interpolate(self.tempo_bpm, _SWING_RATIO_ANCHORS)

    @property
    def swing_offbeat_fraction(self) -> float:
        """Performed location of a nominal eighth-note offbeat within one beat."""
        ratio=self.effective_swing_ratio
        return ratio/(ratio+1.0)

    def eligible_for_swing_warp(self) -> bool:
        return self.feel in {GrooveFeel.SWING, GrooveFeel.SHUFFLE}


def build_groove_context(
    feel: GrooveFeel | str,
    *,
    tempo_bpm: float,
    meter_numerator: int = 4,
    meter_denominator: int = 4,
    groove_strength: float = 1.0,
    swing_ratio: float | None = None,
    grammar_id: str = "",
    subdivision_hint: str = "",
    confidence: float = 1.0,
    coordination_mode: GrooveCoordinationMode = GrooveCoordinationMode.ELASTIC,
    phase_elasticity: float = 0.55,
    swing_elasticity: float = 0.35,
    tempo_elasticity: float = 0.0,
    provenance: tuple[str, ...] = ("performance_initialization",),
    groove_prior: LearningPriorView | None = None,
    prior_gating_context: PriorGatingContext | None = None,
) -> GrooveTemporalContext:
    if not isinstance(feel, GrooveFeel):
        feel=GrooveFeel(str(feel).lower())

    prior_scale = (
        domain_prior_gate_scale(prior_gating_context)
        if prior_gating_context is not None
        else 1.0
    )
    learned_grammar = strongest_category(groove_prior, "best_groove_grammar")
    learned_reason = ""
    if not grammar_id and learned_grammar is not None and prior_scale > 0.0:
        grammar_id = learned_grammar[0]
        learned_reason = f"learned_groove_grammar:{grammar_id}"

    learned_match = categorical_prior_bias(
        groove_prior,
        "best_groove_grammar",
        grammar_id,
        max_bonus=.10,
    )
    if learned_match.active:
        confidence = min(
            1.0,
            confidence + learned_match.confidence_delta * prior_scale,
        )

    effective_provenance = provenance
    if learned_reason:
        effective_provenance = provenance + (learned_reason,)
    if learned_match.active:
        effective_provenance = effective_provenance + (
            "weighted_groove_prior",
            f"contextual_prior_gate:{prior_scale:.3f}",
        )

    out=GrooveTemporalContext(
        feel=feel,
        tempo_bpm=tempo_bpm,
        meter_numerator=meter_numerator,
        meter_denominator=meter_denominator,
        groove_strength=groove_strength,
        swing_ratio=swing_ratio,
        grammar_id=grammar_id,
        subdivision_hint=subdivision_hint,
        confidence=confidence,
        coordination_mode=coordination_mode,
        phase_elasticity=phase_elasticity,
        swing_elasticity=swing_elasticity,
        tempo_elasticity=tempo_elasticity,
        provenance=effective_provenance,
    )
    out.validate()
    return out


def groove_warped_fraction(
    nominal_fraction: float,
    groove: GrooveTemporalContext | None,
    *,
    swing_eligible: bool = True,
) -> float:
    """Map a nominal within-beat fraction to the shared performed pulse.

    Only the conventional eighth offbeat (0.5) is warped here. Other tuplets,
    sixteenths and asymmetric subdivisions retain their identity unless a later
    style-specific grammar explicitly maps them.
    """
    fraction=nominal_fraction % 1.0
    if groove is None or not swing_eligible:
        return fraction
    groove.validate()
    if not groove.eligible_for_swing_warp() or groove.groove_strength <= 0:
        return fraction
    if abs(fraction-0.5) > 0.08:
        return fraction
    target=groove.swing_offbeat_fraction
    return fraction + groove.groove_strength*(target-fraction)


def groove_timing_offset_beats(
    beat_position: float,
    groove: GrooveTemporalContext | None,
    *,
    swing_eligible: bool = True,
) -> float:
    """Return the local timing displacement needed to align with shared groove."""
    nominal=beat_position % 1.0
    warped=groove_warped_fraction(nominal, groove, swing_eligible=swing_eligible)
    return warped-nominal


def groove_timing_offset_ms(
    beat_position: float,
    groove: GrooveTemporalContext | None,
    *,
    swing_eligible: bool = True,
) -> float:
    if groove is None:
        return 0.0
    groove.validate()
    beats=groove_timing_offset_beats(
        beat_position,
        groove,
        swing_eligible=swing_eligible,
    )
    return beats*(60000.0/groove.tempo_bpm)


@dataclass(frozen=True)
class PlayerTimingProfile:
    role: str
    base_phase_ms: float = 0.0
    phrase_push_ms: float = 0.0
    phrase_release_ms: float = 0.0
    swing_ratio_bias: float = 0.0
    lock_strength: float = 0.7

    def validate(self) -> None:
        if not -40.0 <= self.base_phase_ms <= 40.0:
            raise ValueError("base_phase_ms outside supported range")
        if not -40.0 <= self.phrase_push_ms <= 40.0:
            raise ValueError("phrase_push_ms outside supported range")
        if not -40.0 <= self.phrase_release_ms <= 40.0:
            raise ValueError("phrase_release_ms outside supported range")
        if not -0.5 <= self.swing_ratio_bias <= 0.5:
            raise ValueError("swing_ratio_bias outside supported range")
        if not 0.0 <= self.lock_strength <= 1.0:
            raise ValueError("lock_strength must be within 0..1")


_DEFAULT_PLAYER_TIMING: dict[str, PlayerTimingProfile] = {
    "drums": PlayerTimingProfile("drums", base_phase_ms=-1.5, phrase_push_ms=-2.5, phrase_release_ms=1.5, swing_ratio_bias=-.03, lock_strength=.90),
    "bass": PlayerTimingProfile("bass", base_phase_ms=4.0, phrase_push_ms=-1.0, phrase_release_ms=2.5, swing_ratio_bias=.02, lock_strength=.86),
    "piano": PlayerTimingProfile("piano", base_phase_ms=8.0, phrase_push_ms=-3.0, phrase_release_ms=5.0, swing_ratio_bias=-.05, lock_strength=.66),
    "tenor_sax": PlayerTimingProfile("tenor_sax", base_phase_ms=-5.0, phrase_push_ms=-6.0, phrase_release_ms=7.0, swing_ratio_bias=.05, lock_strength=.52),
    "solo_sax": PlayerTimingProfile("solo_sax", base_phase_ms=-5.0, phrase_push_ms=-6.0, phrase_release_ms=7.0, swing_ratio_bias=.05, lock_strength=.52),
    "solo": PlayerTimingProfile("solo", base_phase_ms=-4.0, phrase_push_ms=-5.0, phrase_release_ms=6.0, swing_ratio_bias=.04, lock_strength=.50),
}


def player_timing_profile(role: str) -> PlayerTimingProfile:
    return _DEFAULT_PLAYER_TIMING.get(role, PlayerTimingProfile(role))
    

def player_phase_offset_beats(
    role: str,
    groove: GrooveTemporalContext | None,
    *,
    phrase_maturity: float = 0.5,
) -> float:
    """Return bounded role/phrase placement relative to the shared pulse.

    LOCKED collapses every player onto the reference. ELASTIC/HUMAN_DRIFT keep
    the reference but allow role-specific placement. This is deterministic and
    phrase-shaped rather than per-note random jitter.
    """
    if groove is None:
        return 0.0
    groove.validate()
    if groove.coordination_mode is GrooveCoordinationMode.LOCKED:
        return 0.0
    profile=player_timing_profile(role)
    profile.validate()
    maturity=max(0.0,min(1.0,phrase_maturity))
    # Early phrase can lean forward; phrase ending can relax behind.
    push=(1.0-maturity)*profile.phrase_push_ms
    release=maturity*profile.phrase_release_ms
    raw_ms=profile.base_phase_ms+push+release
    elasticity=groove.phase_elasticity*(1.0-profile.lock_strength*.45)
    ms=raw_ms*elasticity
    return ms/(60000.0/groove.tempo_bpm)


def player_swing_offbeat_fraction(
    role: str,
    groove: GrooveTemporalContext | None,
) -> float:
    if groove is None:
        return .5
    groove.validate()
    if not groove.eligible_for_swing_warp():
        return .5
    base=groove.swing_offbeat_fraction
    if groove.coordination_mode is GrooveCoordinationMode.LOCKED:
        return base
    profile=player_timing_profile(role)
    biased_ratio=max(1.0,groove.effective_swing_ratio+profile.swing_ratio_bias*groove.swing_elasticity)
    return biased_ratio/(biased_ratio+1.0)


@dataclass(frozen=True)
class EnsembleTempoState:
    reference_tempo_bpm: float
    current_tempo_bpm: float
    target_tempo_bpm: float

    def validate(self) -> None:
        if min(self.reference_tempo_bpm,self.current_tempo_bpm,self.target_tempo_bpm) <= 0:
            raise ValueError("tempo values must be positive")


def evolve_ensemble_tempo(
    state: EnsembleTempoState,
    groove: GrooveTemporalContext,
    *,
    collective_push: float = 0.0,
    phrase_release: float = 0.0,
) -> EnsembleTempoState:
    """Move the shared reference tempo slowly in HUMAN_DRIFT mode.

    collective_push and phrase_release are semantic -1..1 / 0..1 signals from
    ensemble reasoning, not random noise. ELASTIC and LOCKED keep the reference
    tempo fixed.
    """
    state.validate()
    groove.validate()
    if groove.coordination_mode is not GrooveCoordinationMode.HUMAN_DRIFT:
        return EnsembleTempoState(
            state.reference_tempo_bpm,
            state.reference_tempo_bpm,
            state.reference_tempo_bpm,
        )
    push=max(-1.0,min(1.0,collective_push))
    release=max(0.0,min(1.0,phrase_release))
    max_span=max(.6,min(4.0,state.reference_tempo_bpm*.025))*groove.tempo_elasticity
    desired=state.reference_tempo_bpm + max_span*(.72*push-.35*release)
    # Inertia: tempo center moves gradually instead of twitching every event.
    target=state.target_tempo_bpm + .18*(desired-state.target_tempo_bpm)
    current=state.current_tempo_bpm + .12*(target-state.current_tempo_bpm)
    return EnsembleTempoState(state.reference_tempo_bpm,current,target)
