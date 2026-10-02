"""Readable score-time quantization utilities.

This is intentionally a small deterministic vertical slice.  It operates on
score-beat evidence already supplied by transport / UMR; it does not estimate
tempo from audio and it does not contain player groove policy.
"""
from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from math import floor

from .notation import NotatedAtom, NotatedAtomKind, ScoreSpan, TupletRatio


@dataclass(frozen=True)
class QuantizationGrid:
    """Allowed written subdivisions in quarter-note beat units."""

    step: Fraction = Fraction(1, 2)
    meter_numerator: int = 4
    meter_denominator: int = 4

    def validate(self) -> None:
        if self.step <= 0:
            raise ValueError("quantization step must be positive")
        if self.meter_numerator <= 0 or self.meter_denominator <= 0:
            raise ValueError("meter values must be positive")

    @property
    def bar_length_quarter_beats(self) -> Fraction:
        return Fraction(
            self.meter_numerator * 4,
            self.meter_denominator,
        )


def _nearest_multiple(value: Fraction, step: Fraction) -> Fraction:
    quotient = value / step
    lower_n = quotient.numerator // quotient.denominator
    upper_n = lower_n + 1
    lower = step * lower_n
    upper = step * upper_n
    # Stable tie break toward the earlier/simple location.
    return lower if value - lower <= upper - value else upper


def quantize_score_span(
    onset_beat: float | Fraction,
    offset_beat: float | Fraction,
    *,
    grid: QuantizationGrid = QuantizationGrid(),
) -> ScoreSpan:
    """Quantize a performed beat span to an exact readable score span."""

    grid.validate()
    onset = Fraction(onset_beat).limit_denominator(4096)
    offset = Fraction(offset_beat).limit_denominator(4096)
    if onset < 0 or offset <= onset:
        raise ValueError("offset_beat must be greater than non-negative onset_beat")

    q_onset = _nearest_multiple(onset, grid.step)
    q_offset = _nearest_multiple(offset, grid.step)
    if q_offset <= q_onset:
        q_offset = q_onset + grid.step

    span = ScoreSpan(q_onset, q_offset - q_onset)
    span.validate()
    return span


def split_note_across_bars(
    span: ScoreSpan,
    source_event_ids: tuple[str, ...],
    *,
    grid: QuantizationGrid = QuantizationGrid(),
) -> tuple[NotatedAtom, ...]:
    """Split a note at barlines and connect pieces with ties."""

    span.validate()
    grid.validate()
    if not source_event_ids:
        raise ValueError("source_event_ids are required")

    bar = grid.bar_length_quarter_beats
    atoms: list[NotatedAtom] = []
    cursor = span.onset
    end = span.offset

    while cursor < end:
        next_bar = (floor(cursor / bar) + 1) * bar
        segment_end = min(end, next_bar)
        atoms.append(
            NotatedAtom(
                kind=NotatedAtomKind.NOTE,
                span=ScoreSpan(cursor, segment_end - cursor),
                source_event_ids=source_event_ids,
                tie_from_previous=bool(atoms),
                tie_to_next=segment_end < end,
            )
        )
        cursor = segment_end

    for atom in atoms:
        atom.validate()
    return tuple(atoms)


def rest_for_gap(start: Fraction, end: Fraction) -> NotatedAtom | None:
    """Represent a positive score-time gap as a rest; zero/negative gaps vanish."""

    if end <= start:
        return None
    rest = NotatedAtom(
        kind=NotatedAtomKind.REST,
        span=ScoreSpan(start, end - start),
    )
    rest.validate()
    return rest


def tuplet_note(
    *,
    onset: Fraction,
    duration: Fraction,
    source_event_ids: tuple[str, ...],
    actual: int,
    normal: int,
) -> NotatedAtom:
    """Build one note atom carrying an arbitrary N:M tuplet relationship."""

    atom = NotatedAtom(
        kind=NotatedAtomKind.NOTE,
        span=ScoreSpan(onset, duration),
        source_event_ids=source_event_ids,
        tuplet=TupletRatio(actual=actual, normal=normal),
    )
    atom.validate()
    return atom
