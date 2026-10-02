"""Pattern-corpus adapter for online drummer decisions."""
from __future__ import annotations

from .model import DrumGesture, DrumHit, DrummerRuntimeContext, DrummerSoftPlan, DrumVoice, Limb
from .pattern_corpus import StoredDrumPattern, hits_at_current_position, patterns_with_tags
from .timing import swing_prior_from_groove
from music_intelligence.reasoning.groove_context import GrooveFeel


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
    DrumVoice.COWBELL: Limb.RIGHT_HAND,
    DrumVoice.CLAVE: Limb.RIGHT_HAND,
}


def _velocity(value: str) -> int:
    return {
        "very_soft": 34,
        "soft": 50,
        "medium": 72,
        "strong": 96,
        "accent": 112,
    }.get(value, 72)


def _tempo_warp_onset(pattern: StoredDrumPattern, onset: float, context: DrummerRuntimeContext) -> float:
    """Warp canonical swung offbeats while preserving source-pattern identity."""
    if "swing" not in pattern.tags or "ride" not in pattern.tags:
        return onset
    frac = onset % 1.0
    if abs(frac - 2.0 / 3.0) > 0.02:
        return onset
    prior = swing_prior_from_groove(context.groove, fallback_bpm=context.tempo_bpm)
    return int(onset) + prior.offbeat_fraction


def pattern_gesture_now(
    pattern: StoredDrumPattern,
    context: DrummerRuntimeContext,
    *,
    tolerance_beats: float = 0.04,
) -> DrumGesture | None:
    """Realize only the current slice of one stored source pattern."""
    position = (
        context.pattern_phase_beats
        if context.pattern_phase_beats is not None
        else context.position_in_bar_beats
    )
    if "swing" in pattern.tags and "ride" in pattern.tags:
        phase = position % pattern.length_beats
        selected = tuple(
            hit
            for hit in pattern.hits
            if abs(_tempo_warp_onset(pattern, hit.onset_beats, context) - phase)
            <= tolerance_beats
        )
    else:
        selected = hits_at_current_position(
            pattern,
            position,
            tolerance_beats=tolerance_beats,
        )

    if not selected:
        return None

    hits = tuple(
        DrumHit(
            voice=h.voice,
            limb=h.limb or _VOICE_TO_LIMB[h.voice],
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


def _style_matches(pattern: StoredDrumPattern, plan: DrummerSoftPlan) -> bool:
    """Require at least one musically identifying style tag to match.

    Functional tags such as fill/setup/ride do not count as style identity.
    """
    non_style = {
        "ride", "time_playing", "swing", "pedal_hihat", "2_and_4",
        "fill", "setup", "upbeat_figure", "triplet", "sixteenth",
    }
    pattern_styles = set(pattern.tags) - non_style
    if not pattern_styles:
        return True
    return bool(pattern_styles & set(plan.style_tags))


def source_pattern_candidates(
    plan: DrummerSoftPlan,
    context: DrummerRuntimeContext,
) -> tuple[DrumGesture, ...]:
    """Return source-derived gestures relevant to style and current instant."""
    plan.validate()
    candidates: list[DrumGesture] = []

    shared_feel = context.groove.feel if context.groove is not None else None
    for pattern in patterns_with_tags("ride"):
        if not _style_matches(pattern, plan):
            continue
        if shared_feel is not None:
            if "swing" in pattern.tags and shared_feel not in {GrooveFeel.SWING, GrooveFeel.SHUFFLE}:
                continue
            if "bop" in pattern.tags and shared_feel in {GrooveFeel.STRAIGHT, GrooveFeel.FUNK, GrooveFeel.BOSSA, GrooveFeel.SALSA}:
                continue
        gesture = pattern_gesture_now(pattern, context)
        if gesture is not None:
            candidates.append(gesture)

    if "afro_cuban" in plan.style_tags:
        for pattern in patterns_with_tags("clave"):
            if not _style_matches(pattern, plan):
                continue
            gesture = pattern_gesture_now(pattern, context)
            if gesture is not None:
                candidates.append(gesture)

    if context.phrase_position >= 0.82 or context.section_transition:
        for pattern in patterns_with_tags("setup"):
            if not _style_matches(pattern, plan):
                continue
            gesture = pattern_gesture_now(pattern, context)
            if gesture is not None:
                candidates.append(gesture)

    return tuple(candidates)
