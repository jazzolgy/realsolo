"""Tempo-conditioned jazz drum timing priors.

These priors are deliberately modest and inspectable.  They are not a claim
that one swing ratio or one inter-instrument phase relation defines jazz swing.

Research basis:
- Friberg & Sundström (2002): ride-cymbal swing ratio varies substantially with
  tempo, from strongly unequal at slow tempi toward nearly even at fast tempi.
- Hofmann et al. timing analyses: ride/bass often act as a shared timing
  reference, while pedal hi-hat/snare can occupy distinct phase relationships.
- MTD perception studies caution against treating larger random timing error as
  inherently more swinging.

The eventual learned prior should come from licensed performance data (for
example GMD) and drummer/style-conditioned profiles.
"""
from __future__ import annotations

from dataclasses import dataclass

from music_intelligence.reasoning.groove_context import GrooveFeel, GrooveTemporalContext


@dataclass(frozen=True)
class SwingTimingPrior:
    bpm: float
    swing_ratio: float
    ride_bias_ms: float = 0.0
    pedal_hihat_relative_ms: float = -8.0
    snare_relative_ms: float = 6.0
    max_humanize_ms: float = 12.0

    @property
    def offbeat_fraction(self) -> float:
        """Location of the swung eighth inside one quarter-note beat."""
        return self.swing_ratio / (self.swing_ratio + 1.0)

    def validate(self) -> None:
        if self.bpm <= 0:
            raise ValueError("bpm must be positive")
        if self.swing_ratio < 1.0:
            raise ValueError("swing_ratio must be >= 1.0")
        if not 0.5 <= self.offbeat_fraction < 1.0:
            raise ValueError("invalid swing offbeat fraction")
        if not 0.0 <= self.max_humanize_ms <= 30.0:
            raise ValueError("max_humanize_ms must stay deliberately modest")


# These anchors are an engineering baseline, not a transcription of any one
# drummer.  They encode only the well-supported monotonic tempo relationship.
_SWING_ANCHORS: tuple[tuple[float, float], ...] = (
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
            alpha = (x - x0) / (x1 - x0)
            return y0 + alpha * (y1 - y0)
    raise AssertionError("unreachable interpolation state")


def tempo_conditioned_swing_prior(bpm: float) -> SwingTimingPrior:
    """Return a conservative baseline prior for swing-time realization.

    The exact anchor values are provisional engineering choices constrained by
    published qualitative/quantitative trends.  Learned drummer/style profiles
    should eventually replace or offset them.
    """
    if bpm <= 0:
        raise ValueError("bpm must be positive")
    ratio = _interpolate(float(bpm), _SWING_ANCHORS)

    # Faster tempi get less absolute timing freedom.  This is intentionally
    # bounded; "humanization" is not modeled as arbitrary jitter.
    max_humanize = _interpolate(
        float(bpm),
        ((60.0, 14.0), (140.0, 11.0), (220.0, 8.0), (360.0, 5.0)),
    )
    prior = SwingTimingPrior(
        bpm=float(bpm),
        swing_ratio=ratio,
        max_humanize_ms=max_humanize,
    )
    prior.validate()
    return prior


def ride_positions_in_two_beat_cell(prior: SwingTimingPrior) -> tuple[float, float, float]:
    """Canonical ride anchors for one two-beat swing cell.

    This returns intention-level timing locations only.  It does not generate a
    bar or schedule future events.
    """
    prior.validate()
    return (0.0, 1.0, 1.0 + prior.offbeat_fraction)


def is_ride_anchor(
    position_in_bar_beats: float,
    prior: SwingTimingPrior,
    tolerance_beats: float = 0.04,
) -> bool:
    if tolerance_beats < 0:
        raise ValueError("tolerance_beats may not be negative")
    phase = position_in_bar_beats % 2.0
    return any(abs(phase - target) <= tolerance_beats for target in ride_positions_in_two_beat_cell(prior))


def bounded_timing_offset_ms(
    base_bias_ms: float,
    role_relative_ms: float,
    expressive_offset_ms: float,
    prior: SwingTimingPrior,
) -> float:
    """Combine timing intentions without permitting arbitrary humanize jitter."""
    prior.validate()
    expressive = max(-prior.max_humanize_ms, min(prior.max_humanize_ms, expressive_offset_ms))
    return base_bias_ms + role_relative_ms + expressive


def swing_prior_from_groove(
    groove: GrooveTemporalContext | None,
    *,
    fallback_bpm: float,
) -> SwingTimingPrior:
    """Project the shared ensemble groove into the drummer's timing prior.

    Drums may add role-relative offsets, but they must not invent a conflicting
    swing ratio when Shared has already established one.
    """
    base=tempo_conditioned_swing_prior(fallback_bpm)
    if groove is None:
        return base
    groove.validate()
    if groove.feel not in {GrooveFeel.SWING, GrooveFeel.SHUFFLE}:
        return base
    prior=SwingTimingPrior(
        bpm=groove.tempo_bpm,
        swing_ratio=max(1.0, groove.effective_swing_ratio),
        ride_bias_ms=base.ride_bias_ms,
        pedal_hihat_relative_ms=base.pedal_hihat_relative_ms,
        snare_relative_ms=base.snare_relative_ms,
        max_humanize_ms=base.max_humanize_ms,
    )
    prior.validate()
    return prior
