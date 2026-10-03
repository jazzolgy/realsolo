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



def split_note_for_readability(
    span: ScoreSpan,
    source_event_ids: tuple[str, ...],
    *,
    grid: QuantizationGrid = QuantizationGrid(),
) -> tuple[NotatedAtom, ...]:
    """Split only where ties make simple-meter rhythm materially easier to read.

    Barline crossings are always tied.  Within a bar, an off-beat note that
    crosses the next quarter-note beat is split at that beat so syncopation
    remains visible.  Beat-aligned dotted values are intentionally preserved.
    """

    bar_atoms = split_note_across_bars(
        span,
        source_event_ids,
        grid=grid,
    )
    out: list[NotatedAtom] = []

    for bar_atom in bar_atoms:
        start = bar_atom.span.onset
        end = bar_atom.span.offset
        starts_on_quarter = start.denominator == 1
        next_quarter = (floor(start) + 1)

        if (
            not starts_on_quarter
            and start < next_quarter < end
            and bar_atom.span.duration > Fraction(1, 2)
        ):
            first = NotatedAtom(
                kind=NotatedAtomKind.NOTE,
                span=ScoreSpan(start, Fraction(next_quarter) - start),
                source_event_ids=source_event_ids,
                tie_from_previous=bar_atom.tie_from_previous,
                tie_to_next=True,
                tuplet=bar_atom.tuplet,
            )
            second = NotatedAtom(
                kind=NotatedAtomKind.NOTE,
                span=ScoreSpan(Fraction(next_quarter), end - Fraction(next_quarter)),
                source_event_ids=source_event_ids,
                tie_from_previous=True,
                tie_to_next=bar_atom.tie_to_next,
                tuplet=bar_atom.tuplet,
            )
            first.validate()
            second.validate()
            out.extend((first, second))
        else:
            out.append(bar_atom)

    return tuple(out)


def written_note_type_and_dots(
    duration: Fraction,
    *,
    tuplet: TupletRatio | None = None,
) -> tuple[str | None, int]:
    """Map score duration to a MusicXML written note type and dot count.

    Tuplet durations are converted back to their displayed written value before
    choosing the type, e.g. a 1/3-quarter triplet note displays as an eighth.
    """

    if duration <= 0:
        raise ValueError("duration must be positive")

    written = duration
    if tuplet is not None:
        tuplet.validate()
        written = duration * Fraction(tuplet.actual, tuplet.normal)

    base_types = (
        (Fraction(4), "whole"),
        (Fraction(2), "half"),
        (Fraction(1), "quarter"),
        (Fraction(1, 2), "eighth"),
        (Fraction(1, 4), "16th"),
        (Fraction(1, 8), "32nd"),
        (Fraction(1, 16), "64th"),
        (Fraction(1, 32), "128th"),
    )
    for base, name in base_types:
        if written == base:
            return name, 0
        if written == base * Fraction(3, 2):
            return name, 1
        if written == base * Fraction(7, 4):
            return name, 2
    return None, 0

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
