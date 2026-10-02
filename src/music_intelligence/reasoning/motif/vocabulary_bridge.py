"""Bridge Shared Legend vocabulary memory into Shared Motif Identity.

This module is instrument-neutral. It converts normalized vocabulary memory into
relative motif identity only; it never schedules future notes or drum hits.
"""
from __future__ import annotations

from music_intelligence.legends.interfaces import VocabularyMemoryItem

from .representation import MotifIdentity


def motif_identity_from_vocabulary(
    item: VocabularyMemoryItem,
) -> MotifIdentity | None:
    """Build a Shared MotifIdentity from normalized vocabulary representation.

    Supported normalized fields are intentionally compact and relative:
    `ioi:2,3,1|accent:0.638,0.720,0.613,0.659`

    IOIs become the motif rhythm schema. Accent values become accent_shape.
    Instrument-specific orchestration remains the Player's responsibility.
    """
    item.validate()
    rep = item.transposition_normalized_representation.strip()
    if not rep:
        return None

    parts: dict[str, str] = {}
    for raw in rep.split("|"):
        if ":" not in raw:
            continue
        key, value = raw.split(":", 1)
        parts[key.strip().lower()] = value.strip()

    ioi_text = parts.get("ioi", "")
    if not ioi_text:
        return None
    try:
        rhythm = tuple(float(x) for x in ioi_text.split(",") if x.strip())
    except ValueError:
        return None
    if not rhythm or any(x <= 0 for x in rhythm):
        return None

    accent: tuple[float, ...] = ()
    accent_text = parts.get("accent", "")
    if accent_text:
        try:
            accent = tuple(float(x) for x in accent_text.split(",") if x.strip())
        except ValueError:
            accent = ()
        if accent and any(not 0.0 <= x <= 1.0 for x in accent):
            return None

    event_count = max(1, min(8, len(rhythm) + 1))
    if accent and len(accent) != event_count:
        # Keep structural rhythm if accent evidence is incomplete.
        accent = ()

    identity = MotifIdentity(
        motif_id=f"vocabulary:{item.vocabulary_id}",
        rhythm_schema=rhythm,
        contour=item.contour,
        accent_shape=accent,
        phrase_shape=item.phrase_position or "vocabulary_abstraction",
        density=min(1.0, event_count / max(4.0, sum(rhythm))),
        harmonic_target_behavior="contextual_retarget",
        interaction_function=(
            "drum_solo"
            if "drum_solo" in item.context_tags
            else "vocabulary_recall"
        ),
        event_count_hint=event_count,
        provenance=item.provenance
        + (
            "shared_motif:vocabulary_bridge",
            item.source_id,
            item.vocabulary_id,
        ),
    )
    identity.validate()
    return identity
