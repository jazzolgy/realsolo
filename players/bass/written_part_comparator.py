"""Abstract comparator for written bass parts versus AI realizations.

The comparator intentionally avoids exact-note copying metrics. It compares
structural motion features that can be learned from a written bass part without
turning that part into a phrase library.

Feature families:
- root occupancy / root-motion support
- scalar/stepwise motion
- chromatic approach behavior
- enclosure behavior
- register center/span/slope
- direction reversal
- repeated-note rate
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class BassLineObservation:
    pitch_midi: int
    beat: float
    harmonic_root_pc: int | None = None
    structural_pitch_classes: frozenset[int] = frozenset()

    def validate(self) -> None:
        if not 0 <= self.pitch_midi <= 127:
            raise ValueError("pitch_midi must be in MIDI range")
        if self.harmonic_root_pc is not None and not 0 <= self.harmonic_root_pc <= 11:
            raise ValueError("harmonic_root_pc must be in 0..11")
        if any(not 0 <= pc <= 11 for pc in self.structural_pitch_classes):
            raise ValueError("structural pitch classes must be in 0..11")


@dataclass(frozen=True)
class BassLineAbstractProfile:
    event_count: int
    root_occupancy_rate: float
    structural_occupancy_rate: float
    scalar_motion_rate: float
    chromatic_approach_rate: float
    enclosure_rate: float
    repeated_pitch_rate: float
    direction_reversal_rate: float
    register_center: float | None
    register_span: int
    register_slope: float


@dataclass(frozen=True)
class BassLineComparison:
    reference: BassLineAbstractProfile
    generated: BassLineAbstractProfile
    feature_distance: float
    feature_deltas: tuple[tuple[str, float], ...]


def _sign(value: int) -> int:
    return 1 if value > 0 else -1 if value < 0 else 0


def analyze_bass_line(
    events: tuple[BassLineObservation, ...],
) -> BassLineAbstractProfile:
    if not events:
        return BassLineAbstractProfile(
            0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, None, 0, 0.0
        )
    for event in events:
        event.validate()

    pitches = [x.pitch_midi for x in events]
    intervals = [b - a for a, b in zip(pitches, pitches[1:])]
    count = len(events)

    roots = sum(
        e.harmonic_root_pc is not None and e.pitch_midi % 12 == e.harmonic_root_pc
        for e in events
    )
    structural = sum(
        bool(e.structural_pitch_classes)
        and e.pitch_midi % 12 in e.structural_pitch_classes
        for e in events
    )
    scalar = sum(0 < abs(x) <= 2 for x in intervals)

    # An event is a chromatic approach when it sits a semitone from the next
    # event and the next event is structurally supported by its own harmony.
    approaches = 0
    for current, nxt in zip(events, events[1:]):
        next_structural = (
            nxt.harmonic_root_pc is not None
            and nxt.pitch_midi % 12 == nxt.harmonic_root_pc
        ) or (
            bool(nxt.structural_pitch_classes)
            and nxt.pitch_midi % 12 in nxt.structural_pitch_classes
        )
        if next_structural and abs(nxt.pitch_midi - current.pitch_midi) == 1:
            approaches += 1

    # Three-event abstract enclosure: first two pitches straddle the third by
    # one or two semitones total and the arrival is structurally supported.
    enclosures = 0
    for a, b, target in zip(events, events[1:], events[2:]):
        arrival_structural = (
            target.harmonic_root_pc is not None
            and target.pitch_midi % 12 == target.harmonic_root_pc
        ) or (
            bool(target.structural_pitch_classes)
            and target.pitch_midi % 12 in target.structural_pitch_classes
        )
        if not arrival_structural:
            continue
        da = a.pitch_midi - target.pitch_midi
        db = b.pitch_midi - target.pitch_midi
        if da * db < 0 and abs(da) <= 2 and abs(db) <= 2:
            enclosures += 1

    repeats = sum(a == b for a, b in zip(pitches, pitches[1:]))
    reversals = 0
    previous_sign = 0
    for delta in intervals:
        current_sign = _sign(delta)
        if current_sign and previous_sign and current_sign != previous_sign:
            reversals += 1
        if current_sign:
            previous_sign = current_sign

    center = sum(pitches) / len(pitches)
    span = max(pitches) - min(pitches)
    slope = (
        (pitches[-1] - pitches[0]) / max(1, len(pitches) - 1)
        if len(pitches) >= 2 else 0.0
    )

    return BassLineAbstractProfile(
        event_count=count,
        root_occupancy_rate=roots / count,
        structural_occupancy_rate=structural / count,
        scalar_motion_rate=scalar / max(1, len(intervals)),
        chromatic_approach_rate=approaches / max(1, len(events) - 1),
        enclosure_rate=enclosures / max(1, len(events) - 2),
        repeated_pitch_rate=repeats / max(1, len(intervals)),
        direction_reversal_rate=reversals / max(1, len(intervals)),
        register_center=center,
        register_span=span,
        register_slope=slope,
    )


def compare_bass_lines(
    reference_events: tuple[BassLineObservation, ...],
    generated_events: tuple[BassLineObservation, ...],
) -> BassLineComparison:
    reference = analyze_bass_line(reference_events)
    generated = analyze_bass_line(generated_events)

    pairs = (
        ("root_occupancy_rate", reference.root_occupancy_rate, generated.root_occupancy_rate, 1.0),
        ("structural_occupancy_rate", reference.structural_occupancy_rate, generated.structural_occupancy_rate, 1.0),
        ("scalar_motion_rate", reference.scalar_motion_rate, generated.scalar_motion_rate, 1.0),
        ("chromatic_approach_rate", reference.chromatic_approach_rate, generated.chromatic_approach_rate, 1.0),
        ("enclosure_rate", reference.enclosure_rate, generated.enclosure_rate, 1.0),
        ("repeated_pitch_rate", reference.repeated_pitch_rate, generated.repeated_pitch_rate, 1.0),
        ("direction_reversal_rate", reference.direction_reversal_rate, generated.direction_reversal_rate, 1.0),
        ("register_span", float(reference.register_span), float(generated.register_span), 12.0),
        ("register_slope", reference.register_slope, generated.register_slope, 4.0),
    )
    if reference.register_center is not None and generated.register_center is not None:
        pairs += ((
            "register_center",
            reference.register_center,
            generated.register_center,
            12.0,
        ),)

    deltas: list[tuple[str, float]] = []
    normalized: list[float] = []
    for name, ref, gen, scale in pairs:
        delta = gen - ref
        deltas.append((name, delta))
        normalized.append(min(1.0, abs(delta) / scale))

    return BassLineComparison(
        reference=reference,
        generated=generated,
        feature_distance=sum(normalized) / max(1, len(normalized)),
        feature_deltas=tuple(deltas),
    )
