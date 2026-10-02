"""Drum rhythmic-language engine.

This layer turns solo-development verbs into actual rhythmic transformations.
It stores *motif identity* (relative onset/IOI/accent/orchestration structure),
never a committed future performance. Runtime realization still emits only the
event available at the current clock phase, then the caller listens and replans.
"""
from __future__ import annotations

from dataclasses import dataclass, replace
from enum import Enum

from music_intelligence.reasoning.motif import MotifIdentity

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


@dataclass(frozen=True)
class CommittedRhythmicEvent:
    """One already-played event used only for retrospective motif discovery."""

    unit: int
    accent: float
    orchestration_slot: int

    def validate(self, cycle_units: int) -> None:
        if not 0 <= self.unit < cycle_units:
            raise ValueError("committed event unit must lie inside cycle")
        if not 0.0 <= self.accent <= 1.0:
            raise ValueError("committed event accent must be within 0..1")
        if self.orchestration_slot < 0:
            raise ValueError("orchestration_slot may not be negative")


def motif_from_committed_events(
    events: tuple[CommittedRhythmicEvent, ...],
    *,
    cycle_units: int = 12,
    subdivision: str = "eighth_triplet_grid",
    min_events: int = 2,
) -> RhythmicMotifIdentity | None:
    """Infer motif identity only from events that have already happened."""
    if cycle_units <= 0:
        raise ValueError("cycle_units must be positive")
    if min_events < 2:
        raise ValueError("min_events must be at least 2")
    if len(events) < min_events:
        return None
    for event in events:
        event.validate(cycle_units)

    # Keep the most recent realization at duplicate phase positions.
    by_unit: dict[int, CommittedRhythmicEvent] = {}
    for event in events:
        by_unit[event.unit] = event
    if len(by_unit) < min_events:
        return None

    ordered = tuple(by_unit[u] for u in sorted(by_unit))
    motif = RhythmicMotifIdentity(
        motif_id="retrospective_committed_motif",
        cycle_units=cycle_units,
        onset_units=tuple(e.unit for e in ordered),
        subdivision=subdivision,
        accent_vector=tuple(e.accent for e in ordered),
        orchestration_contour=tuple(e.orchestration_slot for e in ordered),
        source="retrospective_local_execution",
        provenance=("drum_rhythmic_language", "committed_execution"),
    )
    motif.validate()
    return motif


def grouping_boundary_motif(
    *,
    motif_id: str,
    grouping: tuple[int, ...],
    subdivision: str,
    source: str,
) -> RhythmicMotifIdentity:
    """Convert source-supported grouping lengths into boundary-only identity.

    This deliberately stores group boundaries, not the copyrighted note content
    that may have appeared inside each group.
    """
    if not grouping or any(x <= 0 for x in grouping):
        raise ValueError("grouping must contain positive units")
    cycle_units = sum(grouping)
    onsets: list[int] = []
    cursor = 0
    for size in grouping:
        onsets.append(cursor)
        cursor += size

    accents = tuple(0.82 if i == 0 else 0.62 for i in range(len(onsets)))
    contour = tuple(i for i in range(len(onsets)))
    motif = RhythmicMotifIdentity(
        motif_id=motif_id,
        cycle_units=cycle_units,
        onset_units=tuple(onsets),
        subdivision=subdivision,
        accent_vector=accents,
        orchestration_contour=contour,
        source=source,
        provenance=("drum_rhythmic_language", "source_grouping_boundary"),
    )
    motif.validate()
    return motif


def rhythmic_motif_from_shared(
    identity: MotifIdentity,
) -> RhythmicMotifIdentity:
    """Project instrument-neutral Shared MotifIdentity into drum rhythm space."""
    identity.validate()
    if not identity.rhythm_schema:
        return engineering_seed_motif()

    iois = tuple(max(1, int(round(x))) for x in identity.rhythm_schema)
    onsets = [0]
    cursor = 0
    for ioi in iois:
        cursor += ioi
        onsets.append(cursor)

    cycle_units = cursor + 1
    accents = identity.accent_shape
    if len(accents) != len(onsets):
        accents = tuple(0.72 if i == 0 else 0.62 for i in range(len(onsets)))

    motif = RhythmicMotifIdentity(
        motif_id=f"shared:{identity.motif_id}",
        cycle_units=cycle_units,
        onset_units=tuple(onsets),
        subdivision="shared_relative_grid",
        accent_vector=tuple(accents),
        orchestration_contour=tuple(0 for _ in onsets),
        source="shared_motif_identity",
        provenance=identity.provenance + ("players_drums:rhythmic_projection",),
    )
    motif.validate()
    return motif


def motif_from_normalized_vocabulary(
    *,
    vocabulary_id: str,
    source_id: str,
    normalized_representation: str,
    provenance: tuple[str, ...] = (),
) -> RhythmicMotifIdentity | None:
    """Convert a shared normalized IOI/accent representation into motif identity.

    Expected format:
    `ioi:2,3,1|accent:0.638,0.720,0.613,0.659`

    This is an abstract memory representation, not a scheduled phrase.
    """
    if not normalized_representation:
        return None
    parts = {}
    for part in normalized_representation.split("|"):
        if ":" not in part:
            continue
        key, value = part.split(":", 1)
        parts[key.strip()] = value.strip()
    if "ioi" not in parts:
        return None

    try:
        iois = tuple(int(x) for x in parts["ioi"].split(",") if x.strip())
    except ValueError:
        return None
    if not iois or any(x <= 0 for x in iois):
        return None

    onsets = [0]
    cursor = 0
    for ioi in iois:
        cursor += ioi
        onsets.append(cursor)
    cycle_units = cursor
    # Last onset at cycle boundary belongs to next cycle; convert to in-cycle
    # representation by using the preceding events plus boundary-aware final event
    # just before wrap when necessary.
    if onsets[-1] == cycle_units:
        # Preserve N+1 event accent shape by increasing cycle one unit; this avoids
        # collapsing the terminal event onto onset 0 while keeping relative IOIs.
        cycle_units += 1

    accent_text = parts.get("accent", "")
    accents: tuple[float, ...]
    try:
        accents = tuple(float(x) for x in accent_text.split(",") if x.strip())
    except ValueError:
        accents = ()
    if len(accents) != len(onsets):
        accents = tuple(0.72 if i == 0 else 0.62 for i in range(len(onsets)))
    accents = tuple(max(0.0, min(1.0, x)) for x in accents)

    motif = RhythmicMotifIdentity(
        motif_id=f"legend:{vocabulary_id}",
        cycle_units=cycle_units,
        onset_units=tuple(onsets),
        subdivision="triplet_grid",
        accent_vector=accents,
        orchestration_contour=tuple(0 for _ in onsets),
        source=f"shared_legend_vocabulary:{source_id}",
        provenance=provenance + ("shared_legend_vocabulary",),
    )
    motif.validate()
    return motif


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
