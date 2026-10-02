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
    provenance: tuple[str, ...] = ("performance_initialization",),
) -> GrooveTemporalContext:
    if not isinstance(feel, GrooveFeel):
        feel=GrooveFeel(str(feel).lower())
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
        provenance=provenance,
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
