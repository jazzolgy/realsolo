"""Piano realization adapter for Shared Scale/Linear Intelligence.

Shared Core owns semantic linear-route affordances. Piano owns only immediate
register realization and piano-local event tags.
"""
from __future__ import annotations

from music_intelligence.harmony.scale_linear_core import (
    LinearConnectionAffordance,
    LinearRouteKind,
)
from music_intelligence.reasoning.legend_style_core import CandidateEvent


def _nearest_pitch_for_pc(
    pc: int,
    *,
    anchor_midi: int,
    low_midi: int,
    high_midi: int,
) -> int | None:
    choices = [n for n in range(low_midi, high_midi + 1) if n % 12 == pc]
    if not choices:
        return None
    return min(choices, key=lambda n: abs(n - anchor_midi))


def realize_shared_linear_affordances(
    affordances: tuple[LinearConnectionAffordance, ...],
    *,
    anchor_midi: int,
    low_midi: int = 48,
    high_midi: int = 96,
    duration_beats: float = 0.5,
    pickup: bool = False,
) -> tuple[CandidateEvent, ...]:
    """Realize immediate shared pitch-class routes inside a piano register.

    No future phrase or multi-event sequence is created here.
    """
    if not 21 <= low_midi < high_midi <= 108:
        raise ValueError("invalid piano range")
    if duration_beats <= 0:
        raise ValueError("duration_beats must be positive")

    anchor_midi = max(low_midi, min(high_midi, anchor_midi))
    events: list[CandidateEvent] = []

    for route in affordances:
        route.validate()
        for pc in sorted(route.immediate_pitch_classes):
            pitch = _nearest_pitch_for_pc(
                pc,
                anchor_midi=anchor_midi,
                low_midi=low_midi,
                high_midi=high_midi,
            )
            if pitch is None:
                continue

            tags = {
                "shared_linear",
                f"linear_route:{route.route.value}",
            }
            tags.update(route.context_tags)

            if route.route is LinearRouteKind.CHORDAL:
                tags |= {"chord_tone", "harmonic_identity"}
            elif route.route is LinearRouteKind.DIATONIC_PASSING:
                tags |= {"passing", "connector", "diatonic_passing"}
            elif route.route is LinearRouteKind.CHROMATIC_PASSING:
                tags |= {"passing", "connector", "chromatic_passing"}
            elif route.route is LinearRouteKind.NEIGHBOR:
                tags |= {"neighbor", "connector"}
            elif route.route is LinearRouteKind.ENCLOSURE:
                tags |= {"enclosure", "connector", "directed_target"}
            elif route.route is LinearRouteKind.APPROACH:
                tags |= {"close_approach", "connector", "directed_target"}
            elif route.route is LinearRouteKind.ANTICIPATION:
                tags |= {"anticipation", "next_harmony_target"}
            elif route.route is LinearRouteKind.SCALE_FRAGMENT:
                tags |= {"scale_fragment", "connector"}
            elif route.route is LinearRouteKind.ARPEGGIO_FRAGMENT:
                tags |= {"arpeggio_fragment", "harmonic_outline"}
            elif route.route is LinearRouteKind.COMMON_TONE:
                tags |= {"common_tone", "motif_continuation"}

            if route.requires_resolution:
                tags.add("resolution_required")
            if route.tension_delta > 0:
                tags.add("tension_increase")
            elif route.tension_delta < 0:
                tags.add("tension_release")

            for target_pc in sorted(route.target_pitch_classes):
                tags.add(f"target_pc:{target_pc}")

            onset = -0.125 if pickup and route.route in {
                LinearRouteKind.APPROACH,
                LinearRouteKind.ANTICIPATION,
                LinearRouteKind.ENCLOSURE,
            } else 0.0
            if onset < 0:
                tags |= {"pickup", "syncopated_entry"}

            events.append(
                CandidateEvent(
                    pitch,
                    duration_beats,
                    onset_offset_beats=onset,
                    tags=frozenset(tags),
                )
            )

    # Deterministic dedupe.
    unique: list[CandidateEvent] = []
    seen = set()
    for event in events:
        key = (
            event.pitch_midi,
            event.duration_beats,
            event.onset_offset_beats,
            tuple(sorted(event.tags)),
        )
        if key in seen:
            continue
        seen.add(key)
        unique.append(event)
    return tuple(unique)
