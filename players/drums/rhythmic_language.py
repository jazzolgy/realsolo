"""Drum rhythmic-language engine.

This layer turns solo-development verbs into actual rhythmic transformations.
It stores *motif identity* (relative onset/IOI/accent/orchestration structure),
never a committed future performance. Runtime realization still emits only the
event available at the current clock phase, then the caller listens and replans.
"""
from __future__ import annotations

from dataclasses import dataclass, replace
from enum import Enum

from .model import DrumGesture, DrumHit, DrummerRuntimeContext, DrumVoice, GestureRole, Limb


class RhythmicTransform(str, Enum):
    IDENTITY = "identity"
    REPEAT = "repeat"
    DISPLACE = "displace"
    REORCHESTRATE = "reorchestrate"
    INTERNAL_REST = "internal_rest"
    EXPAND = "expand"
    CONTRACT = "contract"
    FRAGMENT = "fragment"
    HYBRIDIZE = "hybridize"


@dataclass(frozen=True)
class RhythmicMotifIdentity:
    """Structural memory of a rhythmic idea, not a scheduled future phrase.

    onset_units live on a relative cycle grid. accent_vector and
    orchestration_contour describe identity independently of absolute clock time.
    """

    motif_id: str
    cycle_units: int
    onset_units: tuple[int, ...]
    subdivision: str
    accent_vector: tuple[float, ...]
    orchestration_contour: tuple[int, ...]
    source: str = "local_execution"
    provenance: tuple[str, ...] = ("drum_rhythmic_language",)

    def validate(self) -> None:
        if self.cycle_units <= 0:
            raise ValueError("cycle_units must be positive")
        if not self.onset_units:
            raise ValueError("motif must contain at least one onset")
        if tuple(sorted(set(self.onset_units))) != self.onset_units:
            raise ValueError("onset_units must be sorted and unique")
        if any(x < 0 or x >= self.cycle_units for x in self.onset_units):
            raise ValueError("onset_units must lie inside motif cycle")
        if len(self.accent_vector) != len(self.onset_units):
            raise ValueError("accent_vector must align with onset_units")
        if len(self.orchestration_contour) != len(self.onset_units):
            raise ValueError("orchestration_contour must align with onset_units")
        if any(not 0.0 <= x <= 1.0 for x in self.accent_vector):
            raise ValueError("accent values must be within 0..1")

    @property
    def iois(self) -> tuple[int, ...]:
        """Circular inter-onset intervals in grid units."""
        pts = self.onset_units
        return tuple(
            (pts[(i + 1) % len(pts)] - pts[i]) % self.cycle_units
            for i in range(len(pts))
        )


def engineering_seed_motif() -> RhythmicMotifIdentity:
    """Small non-legend engineering seed used until executed material exists."""
    motif = RhythmicMotifIdentity(
        motif_id="engineering_seed_3event",
        cycle_units=12,
        onset_units=(0, 4, 7),
        subdivision="eighth_triplet_grid",
        accent_vector=(0.82, 0.48, 0.68),
        orchestration_contour=(0, 0, 1),
        source="engineering_seed_not_source_transcription",
    )
    motif.validate()
    return motif


def transform_motif(
    motif: RhythmicMotifIdentity,
    transform: RhythmicTransform,
    *,
    amount_units: int = 1,
) -> RhythmicMotifIdentity:
    """Apply a real structural transformation while preserving identity metadata."""
    motif.validate()

    if transform in {RhythmicTransform.IDENTITY, RhythmicTransform.REPEAT}:
        return replace(motif, motif_id=f"{motif.motif_id}:{transform.value}")

    if transform is RhythmicTransform.DISPLACE:
        shift = amount_units % motif.cycle_units
        indexed = [
            ((u + shift) % motif.cycle_units, a, o)
            for u, a, o in zip(
                motif.onset_units, motif.accent_vector, motif.orchestration_contour
            )
        ]
        indexed.sort(key=lambda x: x[0])
        out = replace(
            motif,
            motif_id=f"{motif.motif_id}:displace{shift}",
            onset_units=tuple(x[0] for x in indexed),
            accent_vector=tuple(x[1] for x in indexed),
            orchestration_contour=tuple(x[2] for x in indexed),
        )
    elif transform is RhythmicTransform.REORCHESTRATE:
        out = replace(
            motif,
            motif_id=f"{motif.motif_id}:reorchestrate",
            orchestration_contour=tuple(x + 1 for x in motif.orchestration_contour),
        )
    elif transform is RhythmicTransform.INTERNAL_REST:
        if len(motif.onset_units) <= 1:
            return motif
        # Remove a lower-salience interior event where possible.
        candidates = list(range(1, len(motif.onset_units) - 1)) or list(range(len(motif.onset_units)))
        remove_i = min(candidates, key=lambda i: motif.accent_vector[i])
        out = replace(
            motif,
            motif_id=f"{motif.motif_id}:internal_rest",
            onset_units=tuple(x for i, x in enumerate(motif.onset_units) if i != remove_i),
            accent_vector=tuple(x for i, x in enumerate(motif.accent_vector) if i != remove_i),
            orchestration_contour=tuple(
                x for i, x in enumerate(motif.orchestration_contour) if i != remove_i
            ),
        )
    elif transform is RhythmicTransform.EXPAND:
        factor = 2
        indexed = [
            (min(motif.cycle_units - 1, u * factor), a, o)
            for u, a, o in zip(
                motif.onset_units, motif.accent_vector, motif.orchestration_contour
            )
        ]
        dedup: dict[int, tuple[float, int]] = {}
        for u, a, o in indexed:
            if u not in dedup or a > dedup[u][0]:
                dedup[u] = (a, o)
        units = tuple(sorted(dedup))
        out = replace(
            motif,
            motif_id=f"{motif.motif_id}:expand",
            onset_units=units,
            accent_vector=tuple(dedup[u][0] for u in units),
            orchestration_contour=tuple(dedup[u][1] for u in units),
        )
    elif transform is RhythmicTransform.CONTRACT:
        indexed = [
            (round(u / 2), a, o)
            for u, a, o in zip(
                motif.onset_units, motif.accent_vector, motif.orchestration_contour
            )
        ]
        dedup: dict[int, tuple[float, int]] = {}
        for u, a, o in indexed:
            if u not in dedup or a > dedup[u][0]:
                dedup[u] = (a, o)
        units = tuple(sorted(dedup))
        out = replace(
            motif,
            motif_id=f"{motif.motif_id}:contract",
            onset_units=units,
            accent_vector=tuple(dedup[u][0] for u in units),
            orchestration_contour=tuple(dedup[u][1] for u in units),
        )
    elif transform is RhythmicTransform.FRAGMENT:
        keep = max(1, (len(motif.onset_units) + 1) // 2)
        out = replace(
            motif,
            motif_id=f"{motif.motif_id}:fragment",
            onset_units=motif.onset_units[:keep],
            accent_vector=motif.accent_vector[:keep],
            orchestration_contour=motif.orchestration_contour[:keep],
        )
    elif transform is RhythmicTransform.HYBRIDIZE:
        # Preserve the opening identity; create a new ending event from the
        # largest existing gap. This is structural hybridization, not a quote.
        pts = list(motif.onset_units)
        gaps = []
        for i, u in enumerate(pts):
            nxt = pts[(i + 1) % len(pts)]
            gap = (nxt - u) % motif.cycle_units
            gaps.append((gap, u))
        gap, start = max(gaps)
        candidate = (start + max(1, gap // 2)) % motif.cycle_units
        if candidate in pts:
            candidate = (candidate + 1) % motif.cycle_units
        indexed = [
            (u, a, o)
            for u, a, o in zip(
                motif.onset_units, motif.accent_vector, motif.orchestration_contour
            )
        ]
        indexed.append((candidate, 0.58, max(motif.orchestration_contour) + 1))
        indexed.sort(key=lambda x: x[0])
        out = replace(
            motif,
            motif_id=f"{motif.motif_id}:hybrid",
            onset_units=tuple(x[0] for x in indexed),
            accent_vector=tuple(x[1] for x in indexed),
            orchestration_contour=tuple(x[2] for x in indexed),
            source=f"{motif.source}+new_material",
        )
    else:
        raise ValueError(transform)

    out.validate()
    return out


def motif_phase_unit(
    context: DrummerRuntimeContext,
    motif: RhythmicMotifIdentity,
) -> int:
    motif.validate()
    # pattern_phase_beats is preferred when caller provides continuous phrase
    # phase. Otherwise fall back to current bar position.
    phase_beats = (
        context.pattern_phase_beats
        if context.pattern_phase_beats is not None
        else context.position_in_bar_beats
    )
    beat_fraction = (phase_beats / max(1, context.beats_per_bar)) % 1.0
    return int(round(beat_fraction * motif.cycle_units)) % motif.cycle_units


def _voice_from_contour(slot: int, intensity: float) -> DrumVoice:
    palette = [
        DrumVoice.SNARE,
        DrumVoice.HIGH_TOM,
        DrumVoice.MID_TOM,
        DrumVoice.FLOOR_TOM,
        DrumVoice.RIDE,
    ]
    if intensity >= 0.8:
        palette.append(DrumVoice.CRASH)
    return palette[slot % len(palette)]


def _limb_for_voice(voice: DrumVoice, index: int) -> Limb:
    if voice is DrumVoice.BASS_DRUM:
        return Limb.RIGHT_FOOT
    if voice in {DrumVoice.RIDE, DrumVoice.CRASH}:
        return Limb.RIGHT_HAND
    return Limb.RIGHT_HAND if index % 2 == 0 else Limb.LEFT_HAND


def realize_motif_now(
    motif: RhythmicMotifIdentity,
    context: DrummerRuntimeContext,
    *,
    intensity: float,
    development_tag: str,
    tolerance_units: int = 0,
) -> DrumGesture:
    """Realize only the motif event available *now*.

    The motif identity may describe several relative onsets, but this function
    exposes at most one current onset. It never returns a future sequence.
    """
    motif.validate()
    context.validate()
    if not 0.0 <= intensity <= 1.0:
        raise ValueError("intensity must be within 0..1")

    unit = motif_phase_unit(context, motif)
    nearest = [
        (min((unit - u) % motif.cycle_units, (u - unit) % motif.cycle_units), i)
        for i, u in enumerate(motif.onset_units)
    ]
    distance, i = min(nearest)
    if distance > tolerance_units:
        return DrumGesture(
            role=GestureRole.SPACE,
            tags=frozenset({"drum_solo", "motif_space", development_tag}),
            provenance=motif.provenance + ("realize_motif_now",),
        )

    voice = _voice_from_contour(motif.orchestration_contour[i], intensity)
    accent = motif.accent_vector[i]
    velocity = max(1, min(127, int(42 + 58 * intensity + 22 * accent)))
    gesture = DrumGesture(
        hits=(
            DrumHit(
                voice=voice,
                limb=_limb_for_voice(voice, i),
                velocity=velocity,
                articulation=f"motif_{development_tag}",
            ),
        ),
        role=GestureRole.FILL,
        tags=frozenset(
            {"drum_solo", "rhythmic_motif", development_tag, motif.motif_id}
        ),
        confidence=0.9,
        provenance=motif.provenance + ("realize_motif_now",),
    )
    gesture.validate()
    return gesture
