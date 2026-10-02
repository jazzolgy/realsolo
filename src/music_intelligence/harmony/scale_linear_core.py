"""Shared Scale & Linear Connection Intelligence v0.1.

Instrument-neutral route intelligence learned from method-book practice and
standard-chart evaluation.

This is NOT a chord->one-scale lookup table.

It exposes immediate linear affordances that may connect the current musical
state toward harmonic/phrase targets while keeping exact future notes open.
Bass, piano, soloist, arranging, and transcription layers may all consume the
same semantic routes and realize them differently.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .jazz_harmony_core import HarmonicFrame


class LinearRouteKind(str, Enum):
    CHORDAL = "chordal"
    DIATONIC_PASSING = "diatonic_passing"
    CHROMATIC_PASSING = "chromatic_passing"
    NEIGHBOR = "neighbor"
    ENCLOSURE = "enclosure"
    SCALE_FRAGMENT = "scale_fragment"
    ARPEGGIO_FRAGMENT = "arpeggio_fragment"
    COMMON_TONE = "common_tone"
    APPROACH = "approach"
    ANTICIPATION = "anticipation"


class LinearDirection(str, Enum):
    ASCENDING = "ascending"
    DESCENDING = "descending"
    STABLE = "stable"
    EITHER = "either"


@dataclass(frozen=True)
class ScaleField:
    """Contextual pitch-class field, never a compulsory scale name."""
    pitch_classes: frozenset[int]
    structural_pitch_classes: frozenset[int] = frozenset()
    color_pitch_classes: frozenset[int] = frozenset()
    avoid_or_contextual_pitch_classes: frozenset[int] = frozenset()
    confidence: float = 1.0
    provenance: tuple[str, ...] = ()

    def validate(self) -> None:
        for group in (
            self.pitch_classes,
            self.structural_pitch_classes,
            self.color_pitch_classes,
            self.avoid_or_contextual_pitch_classes,
        ):
            if any(not 0 <= pc <= 11 for pc in group):
                raise ValueError("pitch classes must be in 0..11")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be within 0..1")


@dataclass(frozen=True)
class LinearConnectionAffordance:
    route: LinearRouteKind
    immediate_pitch_classes: frozenset[int]
    target_pitch_classes: frozenset[int] = frozenset()
    direction: LinearDirection = LinearDirection.EITHER
    weight: float = 0.0
    tension_delta: float = 0.0
    requires_resolution: bool = False
    context_tags: frozenset[str] = frozenset()
    provenance: tuple[str, ...] = ()
    note: str = ""

    def validate(self) -> None:
        if any(not 0 <= pc <= 11 for pc in self.immediate_pitch_classes):
            raise ValueError("immediate pitch classes must be in 0..11")
        if any(not 0 <= pc <= 11 for pc in self.target_pitch_classes):
            raise ValueError("target pitch classes must be in 0..11")
        if not -1.0 <= self.tension_delta <= 1.0:
            raise ValueError("tension_delta must be within -1..1")


def _active_evidence(frame: HarmonicFrame):
    return frame.inferred or frame.observed or frame.expected


def build_contextual_scale_field(
    frame: HarmonicFrame,
    *,
    local_key_pitch_classes: frozenset[int] = frozenset(),
) -> ScaleField:
    """Merge explicit harmonic evidence into one contextual pitch field.

    The result is intentionally evidence-driven. If no local-key information is
    supplied, the engine does not invent a seven-note scale from a chord symbol.
    """
    frame.validate()
    ev = _active_evidence(frame)
    chord_pcs = ev.pitch_classes if ev is not None else frozenset()
    root = ev.root_pc if ev is not None else None

    structural = set(chord_pcs)
    field = set(chord_pcs) | set(local_key_pitch_classes)
    color = set(local_key_pitch_classes) - structural

    # The root is structural evidence even when the upstream extractor supplied
    # only a root and no full pitch-class set.
    if root is not None:
        structural.add(root)
        field.add(root)

    out = ScaleField(
        pitch_classes=frozenset(field),
        structural_pitch_classes=frozenset(structural),
        color_pitch_classes=frozenset(color),
        confidence=(ev.confidence if ev is not None else .5),
        provenance=(
            "shared_scale_linear_intelligence",
            "explicit_harmonic_evidence",
        ),
    )
    out.validate()
    return out


def _pc_step(source: int, delta: int) -> int:
    return (source + delta) % 12


def _directed_distance(source: int, target: int) -> tuple[int, int]:
    up = (target - source) % 12
    down = (source - target) % 12
    return up, down


def build_linear_connection_affordances(
    frame: HarmonicFrame,
    *,
    current_pitch_class: int | None,
    target_pitch_classes: frozenset[int] = frozenset(),
    local_key_pitch_classes: frozenset[int] = frozenset(),
) -> tuple[LinearConnectionAffordance, ...]:
    """Build immediate, instrument-neutral connection choices.

    The engine never returns a fixed multi-note future line. It exposes the next
    *kind* of movement and immediate pitch-class options. The consuming player
    commits one event, listens again, then asks the engine again.
    """
    frame.validate()
    field = build_contextual_scale_field(
        frame,
        local_key_pitch_classes=local_key_pitch_classes,
    )
    ev = _active_evidence(frame)
    next_ev = frame.next_expected
    out: list[LinearConnectionAffordance] = []

    structural = field.structural_pitch_classes
    if structural:
        out.append(LinearConnectionAffordance(
            LinearRouteKind.CHORDAL,
            structural,
            target_pitch_classes=target_pitch_classes,
            weight=.18,
            context_tags=frozenset({"structural"}),
            provenance=("shared_scale_linear_intelligence",),
            note="Remain inside current structural harmony without prescribing voicing.",
        ))

    if current_pitch_class is not None:
        if current_pitch_class in field.pitch_classes:
            out.append(LinearConnectionAffordance(
                LinearRouteKind.COMMON_TONE,
                frozenset({current_pitch_class}),
                target_pitch_classes=target_pitch_classes,
                direction=LinearDirection.STABLE,
                weight=.06,
                provenance=("shared_scale_linear_intelligence",),
            ))

        # Stepwise field motion. Only pitch classes explicitly supported by the
        # current contextual field are emitted as diatonic/scale continuations.
        up1, up2 = _pc_step(current_pitch_class, 1), _pc_step(current_pitch_class, 2)
        dn1, dn2 = _pc_step(current_pitch_class, -1), _pc_step(current_pitch_class, -2)
        asc = frozenset(pc for pc in (up1, up2) if pc in field.pitch_classes)
        desc = frozenset(pc for pc in (dn1, dn2) if pc in field.pitch_classes)
        if asc:
            out.append(LinearConnectionAffordance(
                LinearRouteKind.DIATONIC_PASSING,
                asc,
                target_pitch_classes=target_pitch_classes,
                direction=LinearDirection.ASCENDING,
                weight=.10,
                provenance=("shared_scale_linear_intelligence", "method_book_abstraction"),
            ))
        if desc:
            out.append(LinearConnectionAffordance(
                LinearRouteKind.DIATONIC_PASSING,
                desc,
                target_pitch_classes=target_pitch_classes,
                direction=LinearDirection.DESCENDING,
                weight=.10,
                provenance=("shared_scale_linear_intelligence", "method_book_abstraction"),
            ))

        # Neighbor motion remains local. A chromatic neighbor is allowed as a
        # tension event even if it is outside the contextual field.
        out.append(LinearConnectionAffordance(
            LinearRouteKind.NEIGHBOR,
            frozenset({_pc_step(current_pitch_class, -1), _pc_step(current_pitch_class, 1)}),
            target_pitch_classes=frozenset({current_pitch_class}),
            weight=.035,
            tension_delta=.12,
            requires_resolution=True,
            provenance=("shared_scale_linear_intelligence", "method_book_abstraction"),
        ))

    # Future-harmony awareness creates approach/anticipation possibilities.
    future_targets = set(target_pitch_classes)
    if next_ev is not None:
        future_targets.update(next_ev.pitch_classes)
        if next_ev.root_pc is not None:
            future_targets.add(next_ev.root_pc)

    if future_targets:
        approach_pcs: set[int] = set()
        enclosure_pcs: set[int] = set()
        for target in future_targets:
            approach_pcs.update({_pc_step(target, -1), _pc_step(target, 1)})
            enclosure_pcs.update({_pc_step(target, -1), _pc_step(target, 1)})

        out.append(LinearConnectionAffordance(
            LinearRouteKind.APPROACH,
            frozenset(approach_pcs),
            target_pitch_classes=frozenset(future_targets),
            weight=.09,
            tension_delta=.10,
            requires_resolution=True,
            context_tags=frozenset({"future_target_known"}),
            provenance=("shared_scale_linear_intelligence", "method_book_abstraction"),
            note="Approach is one available route, not a compulsory last-beat formula.",
        ))
        out.append(LinearConnectionAffordance(
            LinearRouteKind.ENCLOSURE,
            frozenset(enclosure_pcs),
            target_pitch_classes=frozenset(future_targets),
            weight=.045,
            tension_delta=.14,
            requires_resolution=True,
            context_tags=frozenset({"future_target_known", "multi_event_intention"}),
            provenance=("shared_scale_linear_intelligence", "method_book_abstraction"),
            note="Enclosure expresses an intention; exact future notes remain uncommitted.",
        ))
        out.append(LinearConnectionAffordance(
            LinearRouteKind.ANTICIPATION,
            frozenset(future_targets),
            target_pitch_classes=frozenset(future_targets),
            weight=.06,
            tension_delta=-.02,
            context_tags=frozenset({"future_target_known"}),
            provenance=("shared_scale_linear_intelligence",),
        ))

    # Scale/arpeggio fragment semantics are exposed only when enough explicit
    # evidence exists. This avoids inventing a private mode from a chord suffix.
    if len(field.pitch_classes) >= 5:
        out.append(LinearConnectionAffordance(
            LinearRouteKind.SCALE_FRAGMENT,
            field.pitch_classes,
            target_pitch_classes=frozenset(future_targets),
            weight=.07,
            provenance=("shared_scale_linear_intelligence", "method_book_abstraction"),
            note="Contextual scale field; player chooses direction/register/rhythm.",
        ))
    if len(structural) >= 3:
        out.append(LinearConnectionAffordance(
            LinearRouteKind.ARPEGGIO_FRAGMENT,
            structural,
            target_pitch_classes=frozenset(future_targets),
            weight=.07,
            provenance=("shared_scale_linear_intelligence", "method_book_abstraction"),
        ))

    for item in out:
        item.validate()
    return tuple(out)
