"""Pattern-corpus adapter for online drummer decisions."""
from __future__ import annotations

from .model import DrumGesture, DrumHit, DrummerRuntimeContext, DrumVoice, Limb
from .pattern_corpus import StoredDrumPattern, hits_at_current_position, patterns_with_tags
from .timing import tempo_conditioned_swing_prior


_VOICE_TO_LIMB = {
    DrumVoice.RIDE: Limb.RIGHT_HAND,
    DrumVoice.CLOSED_HIHAT: Limb.LEFT_FOOT,
    DrumVoice.OPEN_HIHAT: Limb.LEFT_FOOT,
    DrumVoice.SNARE: Limb.LEFT_HAND,
    DrumVoice.BASS_DRUM: Limb.RIGHT_FOOT,
    DrumVoice.CRASH: Limb.RIGHT_HAND,
    DrumVoice.HIGH_TOM: Limb.RIGHT_HAND,
    DrumVoice.MID_TOM: Limb.RIGHT_HAND,
    DrumVoice.FLOOR_TOM: Limb.LEFT_HAND,
}


def _velocity(value: str) -> int:
    return {
        "very_soft": 34,
        "soft": 50,
        "medium": 72,
        "strong": 96,
        "accent": 112,
    }.get(value, 72)


def _tempo_warp_onset(pattern: StoredDrumPattern, onset: float, bpm: float) -> float:
    """Warp canonical swung offbeats while preserving source-pattern identity."""
    if "swing" not in pattern.tags or "ride" not in pattern.tags:
        return onset
    frac = onset % 1.0
    if abs(frac - 2.0 / 3.0) > 0.02:
        return onset
    prior = tempo_conditioned_swing_prior(bpm)
    return int(onset) + prior.offbeat_fraction


def pattern_gesture_now(
    pattern: StoredDrumPattern,
    context: DrummerRuntimeContext,
    *,
    tolerance_beats: float = 0.04,
) -> DrumGesture | None:
    """Realize only the current slice of one stored source pattern."""
    if "swing" in pattern.tags and "ride" in pattern.tags:
        phase = context.position_in_bar_beats % pattern.length_beats
        selected = tuple(
            hit
            for hit in pattern.hits
            if abs(_tempo_warp_onset(pattern, hit.onset_beats, context.tempo_bpm) - phase)
            <= tolerance_beats
        )
    else:
        selected = hits_at_current_position(
            pattern,
            context.position_in_bar_beats,
            tolerance_beats=tolerance_beats,
        )

    if not selected:
        return None

    hits = tuple(
        DrumHit(
            voice=h.voice,
            limb=_VOICE_TO_LIMB[h.voice],
            velocity=_velocity(h.velocity_class),
            articulation=h.articulation,
        )
        for h in selected
    )
    gesture = DrumGesture(
        hits=hits,
        role=pattern.role,
        tags=pattern.tags | frozenset({"source_pattern", pattern.pattern_id}),
        provenance=("drum_player", "pattern_corpus", pattern.pattern_id),
    )
    gesture.validate()
    return gesture


def source_pattern_candidates(
    context: DrummerRuntimeContext,
) -> tuple[DrumGesture, ...]:
    """Return source-derived gestures relevant to the current instant."""
    candidates: list[DrumGesture] = []

    for pattern in patterns_with_tags("jazz", "ride"):
        gesture = pattern_gesture_now(pattern, context)
        if gesture is not None:
            candidates.append(gesture)

    if context.phrase_position >= 0.82 or context.section_transition:
        for pattern in patterns_with_tags("setup"):
            gesture = pattern_gesture_now(pattern, context)
            if gesture is not None:
                candidates.append(gesture)

    return tuple(candidates)
