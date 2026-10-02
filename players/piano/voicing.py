"""Minimal piano voicing-family generation from resolved harmonic material.

This module deliberately does NOT parse chord symbols or infer jazz harmony.
Shared Core (or a Core adapter) must resolve harmonic roles to pitch classes first.

The current slice only demonstrates small shell/rootless families so that RealSolo
can test the full harmony -> piano candidates -> immediate gesture path.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Sequence

from music_intelligence.reasoning.polyphonic_event import (
    PolyphonicEventCandidate,
    VoiceEvent,
)

from .policy import PianoRealizationCandidate


@dataclass(frozen=True)
class ResolvedHarmonicMaterial:
    """Instrument-neutral harmonic roles already resolved to pitch classes."""

    affordance_id: str
    role_pitch_classes: Mapping[str, tuple[int, ...]]
    root_pitch_class: int | None = None

    def validate(self) -> None:
        if not self.affordance_id:
            raise ValueError("affordance_id is required")
        if self.root_pitch_class is not None and not 0 <= self.root_pitch_class <= 11:
            raise ValueError("root_pitch_class must be within 0..11")
        for role, pcs in self.role_pitch_classes.items():
            if not role:
                raise ValueError("harmonic role name cannot be empty")
            if not pcs:
                raise ValueError("harmonic role must expose at least one pitch class")
            if any(not 0 <= pc <= 11 for pc in pcs):
                raise ValueError("pitch classes must be within 0..11")


@dataclass(frozen=True)
class PianoVoicingRequest:
    material: ResolvedHarmonicMaterial
    bassist_present: bool = True
    low_midi: int = 43
    high_midi: int = 79
    top_note_pitch_class: int | None = None
    duration_beats: float = 0.5

    def validate(self) -> None:
        self.material.validate()
        if not 21 <= self.low_midi <= 108:
            raise ValueError("low_midi outside piano range")
        if not 21 <= self.high_midi <= 108:
            raise ValueError("high_midi outside piano range")
        if self.low_midi >= self.high_midi:
            raise ValueError("low_midi must be below high_midi")
        if self.top_note_pitch_class is not None and not 0 <= self.top_note_pitch_class <= 11:
            raise ValueError("top_note_pitch_class must be within 0..11")
        if self.duration_beats <= 0:
            raise ValueError("duration_beats must be positive")


def _role_pcs(material: ResolvedHarmonicMaterial, *names: str) -> tuple[int, ...]:
    for name in names:
        pcs = material.role_pitch_classes.get(name)
        if pcs:
            return tuple(pcs)
    return ()


def _midi_options(pc: int, low: int, high: int) -> tuple[int, ...]:
    return tuple(n for n in range(low, high + 1) if n % 12 == pc)


def _nearest_in_range(pc: int, target: float, low: int, high: int) -> int:
    options = _midi_options(pc, low, high)
    if not options:
        raise ValueError(f"pitch class {pc} has no realization in requested range")
    return min(options, key=lambda n: abs(n - target))


def _dedupe_ordered(items: Sequence[tuple[str, int]]) -> tuple[tuple[str, int], ...]:
    used: set[int] = set()
    out: list[tuple[str, int]] = []
    for role, pitch in items:
        if pitch in used:
            continue
        used.add(pitch)
        out.append((role, pitch))
    return tuple(out)


def _event_from_roles(
    request: PianoVoicingRequest,
    roles: Sequence[tuple[str, int]],
    *,
    family: str,
) -> PianoRealizationCandidate:
    ordered = sorted(_dedupe_ordered(roles), key=lambda x: x[1])
    voices = tuple(
        VoiceEvent(
            voice_id=f"{family}.{i}",
            pitch_midi=pitch,
            harmonic_role=role,
            provenance=("piano_voicing_generator",),
        )
        for i, (role, pitch) in enumerate(ordered)
    )
    tension_roles = {"9th","9","b9","#9","11th","11","#11","13th","13","b13"}
    tension_count = sum(1 for role, _ in ordered if role in tension_roles)
    event_tags = {family, "sparse" if len(voices) <= 3 else "dense"}
    event_tags.add(f"tension_count:{tension_count}")
    event = PolyphonicEventCandidate(
        voices=voices,
        duration_beats=request.duration_beats,
        tags=frozenset(event_tags),
        role="comping",
        source_family=f"piano_{family}",
        provenance=("piano_voicing_generator", request.material.affordance_id),
        annotations={
            "harmonic_affordance_id": request.material.affordance_id,
            "tension_count": tension_count,
        },
    )
    hands = tuple(
        (voice.voice_id, "LH" if voice.pitch_midi < 60 else "RH")
        for voice in voices
    )
    return PianoRealizationCandidate(event=event, hand_assignment=hands)


def generate_shell_voicings(request: PianoVoicingRequest) -> tuple[PianoRealizationCandidate, ...]:
    """Generate small guide-tone shells from roles already resolved by Core.

    This function knows that shell voicings commonly privilege structural guide
    tones, but it does not calculate which pitch classes are the 3rd/7th of a chord.
    """
    request.validate()
    third = _role_pcs(request.material, "3rd", "b3", "minor_3rd")
    seventh = _role_pcs(request.material, "7th", "b7", "major_7th", "minor_7th")
    root = _role_pcs(request.material, "root")

    if not third or not seventh:
        return ()

    target_low = max(request.low_midi, 48)
    target_high = min(request.high_midi, 72)

    variants: list[PianoRealizationCandidate] = []
    for tpc in third[:2]:
        for spc in seventh[:2]:
            a = _nearest_in_range(tpc, 55, target_low, target_high)
            b = _nearest_in_range(spc, 62, target_low, target_high)
            roles = [("3rd", a), ("7th", b)]
            if not request.bassist_present and root:
                rp = _nearest_in_range(root[0], 43, request.low_midi, min(request.high_midi, 55))
                roles.insert(0, ("root", rp))
            variants.append(_event_from_roles(request, roles, family="shell"))
    return tuple(variants)


def generate_rootless_voicings(request: PianoVoicingRequest) -> tuple[PianoRealizationCandidate, ...]:
    """Generate compact rootless candidates from supplied harmonic-role pitch classes."""
    request.validate()
    third = _role_pcs(request.material, "3rd", "b3", "minor_3rd")
    seventh = _role_pcs(request.material, "7th", "b7", "major_7th", "minor_7th")
    if not third or not seventh:
        return ()

    colors: list[tuple[str, int]] = []
    # Prefer common color tensions before stronger altered colors. Altered roles
    # remain available when Shared Core explicitly supplies them.
    preferred_roles = (
        "9th", "9", "13th", "13", "#11", "11th", "11",
        "b9", "#9", "b13",
    )
    for role in preferred_roles:
        for pc in request.material.role_pitch_classes.get(role, ()):
            colors.append((role, pc))

    base_roles = [
        ("3rd", _nearest_in_range(third[0], 55, request.low_midi, request.high_midi)),
        ("7th", _nearest_in_range(seventh[0], 62, request.low_midi, request.high_midi)),
    ]

    variants: list[PianoRealizationCandidate] = []
    if not colors:
        variants.append(_event_from_roles(request, base_roles, family="rootless"))
        return tuple(variants)

    for role, pc in colors[:5]:
        color_pitch = _nearest_in_range(pc, 66, request.low_midi, request.high_midi)
        roles = [*base_roles, (role, color_pitch)]
        if (
            request.top_note_pitch_class is not None
            and roles[-1][1] % 12 != request.top_note_pitch_class
        ):
            target = _nearest_in_range(
                request.top_note_pitch_class,
                max(p for _, p in roles) + 3,
                request.low_midi,
                request.high_midi,
            )
            roles.append(("top_constraint", target))
        variants.append(_event_from_roles(request, roles, family="rootless"))

    for i, (role_a, pc_a) in enumerate(colors[:5]):
        for role_b, pc_b in colors[i + 1 : 5]:
            if pc_a == pc_b:
                continue
            a = _nearest_in_range(pc_a, 63, request.low_midi, request.high_midi)
            b = _nearest_in_range(pc_b, 69, request.low_midi, request.high_midi)
            roles = [*base_roles, (role_a, a), (role_b, b)]
            variants.append(_event_from_roles(request, roles, family="rootless"))

    return tuple(variants[:10])


def generate_minimal_voicing_families(
    request: PianoVoicingRequest,
) -> tuple[PianoRealizationCandidate, ...]:
    return generate_shell_voicings(request) + generate_rootless_voicings(request)


def _available_role_pcs(material: ResolvedHarmonicMaterial) -> tuple[tuple[str, int], ...]:
    """Flatten only pitch classes already exposed by Core-resolved material."""
    out: list[tuple[str, int]] = []
    seen: set[tuple[str, int]] = set()
    for role, pcs in material.role_pitch_classes.items():
        for pc in pcs:
            item = (role, pc)
            if item not in seen:
                seen.add(item)
                out.append(item)
    return tuple(out)


def _structure_score(intervals: Sequence[int], preferred: set[int]) -> int:
    return sum(1 for interval in intervals if interval % 12 in preferred)


def _candidate_from_pitch_classes(
    request: PianoVoicingRequest,
    role_pcs: Sequence[tuple[str, int]],
    *,
    targets: Sequence[float],
    family: str,
) -> PianoRealizationCandidate:
    roles: list[tuple[str, int]] = []
    for (role, pc), target in zip(role_pcs, targets):
        pitch = _nearest_in_range(pc, target, request.low_midi, request.high_midi)
        while any(existing == pitch for _, existing in roles) and pitch + 12 <= request.high_midi:
            pitch += 12
        roles.append((role, pitch))
    return _event_from_roles(request, roles, family=family)


def generate_tertian_voicings(
    request: PianoVoicingRequest,
) -> tuple[PianoRealizationCandidate, ...]:
    """Create experimental tertian-shaped candidates from Core-supplied pitch classes.

    No chord spelling is inferred here. The generator searches only among roles/pitch
    classes already exposed by ResolvedHarmonicMaterial.
    """
    request.validate()
    pool = _available_role_pcs(request.material)
    if len(pool) < 3:
        return ()

    variants: list[PianoRealizationCandidate] = []
    for start in range(min(len(pool), 5)):
        chosen = [pool[start]]
        current_pc = pool[start][1]
        remaining = [item for item in pool if item != pool[start]]
        while remaining and len(chosen) < 4:
            ranked = sorted(
                remaining,
                key=lambda item: (
                    0 if (item[1] - current_pc) % 12 in {3, 4} else 1,
                    min((item[1] - current_pc) % 12, (current_pc - item[1]) % 12),
                ),
            )
            nxt = ranked[0]
            chosen.append(nxt)
            current_pc = nxt[1]
            remaining.remove(nxt)
        if len(chosen) >= 3:
            variants.append(
                _candidate_from_pitch_classes(
                    request,
                    chosen,
                    targets=(50, 55, 60, 65),
                    family="tertian",
                )
            )
    return tuple(variants[:4])


def generate_quartal_voicings(
    request: PianoVoicingRequest,
) -> tuple[PianoRealizationCandidate, ...]:
    """Create fourth-oriented candidates from already permitted harmonic material."""
    request.validate()
    pool = _available_role_pcs(request.material)
    if len(pool) < 3:
        return ()

    variants: list[PianoRealizationCandidate] = []
    for start in range(min(len(pool), 6)):
        chosen = [pool[start]]
        current_pc = pool[start][1]
        remaining = [item for item in pool if item != pool[start]]
        while remaining and len(chosen) < 4:
            ranked = sorted(
                remaining,
                key=lambda item: (
                    0 if (item[1] - current_pc) % 12 in {5, 6, 7} else 1,
                    min(
                        abs(((item[1] - current_pc) % 12) - 5),
                        abs(((item[1] - current_pc) % 12) - 7),
                    ),
                ),
            )
            nxt = ranked[0]
            chosen.append(nxt)
            current_pc = nxt[1]
            remaining.remove(nxt)
        if len(chosen) >= 3:
            variants.append(
                _candidate_from_pitch_classes(
                    request,
                    chosen,
                    targets=(48, 55, 62, 69),
                    family="quartal",
                )
            )
    return tuple(variants[:4])


def generate_inverted_quartal_voicings(
    request: PianoVoicingRequest,
) -> tuple[PianoRealizationCandidate, ...]:
    """Redistribute quartal material into a non-stacked/inverted register layout."""
    base = generate_quartal_voicings(request)
    out: list[PianoRealizationCandidate] = []
    for realization in base:
        voices = realization.event.voices
        if len(voices) < 3:
            continue
        role_pcs = [(v.harmonic_role or "color", v.pitch_midi % 12) for v in voices]
        rotated = role_pcs[1:] + role_pcs[:1]
        out.append(
            _candidate_from_pitch_classes(
                request,
                rotated,
                targets=(50, 57, 64, 71),
                family="inverted_quartal",
            )
        )
    return tuple(out)


def generate_octave_voicings(
    request: PianoVoicingRequest,
) -> tuple[PianoRealizationCandidate, ...]:
    """Create projected octave structures from one supplied structural/color role."""
    request.validate()
    pool = _available_role_pcs(request.material)
    if not pool:
        return ()

    preferred_order = ("3rd", "7th", "b7", "9th", "9", "11th", "11", "13th", "13", "root")
    ranked = sorted(
        pool,
        key=lambda item: preferred_order.index(item[0]) if item[0] in preferred_order else len(preferred_order),
    )
    out: list[PianoRealizationCandidate] = []
    for role, pc in ranked[:3]:
        low = _nearest_in_range(pc, 52, request.low_midi, request.high_midi)
        high_options = [n for n in (low + 12, low + 24) if n <= request.high_midi]
        if not high_options:
            continue
        roles = [(role, low), (f"{role}_octave", high_options[-1])]
        out.append(_event_from_roles(request, roles, family="octave"))
    return tuple(out)


def generate_mixed_voicings(
    request: PianoVoicingRequest,
) -> tuple[PianoRealizationCandidate, ...]:
    """Experimental combination family mixing structural and color roles."""
    request.validate()
    structural = []
    for role in ("3rd", "b3", "7th", "b7"):
        for pc in request.material.role_pitch_classes.get(role, ()):
            structural.append((role, pc))
    colors = [
        (role, pc)
        for role, pcs in request.material.role_pitch_classes.items()
        if role not in {"root", "3rd", "b3", "7th", "b7"}
        for pc in pcs
    ]
    if len(structural) < 2 or not colors:
        return ()

    out: list[PianoRealizationCandidate] = []
    for color in colors[:4]:
        chosen = structural[:2] + [color]
        out.append(
            _candidate_from_pitch_classes(
                request,
                chosen,
                targets=(50, 58, 67),
                family="mixed",
            )
        )
    return tuple(out)


def generate_extended_voicing_families(
    request: PianoVoicingRequest,
) -> tuple[PianoRealizationCandidate, ...]:
    """Experimental McNeely-derived family competition for sustained/static contexts."""
    return (
        generate_tertian_voicings(request)
        + generate_quartal_voicings(request)
        + generate_inverted_quartal_voicings(request)
        + generate_octave_voicings(request)
        + generate_mixed_voicings(request)
    )
