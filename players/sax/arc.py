from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SaxArcContext:
    pitch_midi: int
    previous_pitch_midi: int | None
    duration_beats: float
    phrase_maturity: float
    notes_since_breath: int
    breath_before: bool
    phrase_start: bool
    phrase_end: bool
    tension: float = 0.0


@dataclass(frozen=True, slots=True)
class SaxArcDecision:
    phase: str
    add_articulations: tuple[str, ...] = ()
    remove_articulations: tuple[str, ...] = ()
    velocity_delta: int = 0
    attack_scale: float = 1.0
    release_shape: str | None = None
    reason: tuple[str, ...] = ()


def choose_sax_articulation_arc(context: SaxArcContext) -> SaxArcDecision:
    """Shape the current committed note inside a phrase-level articulation arc.

    This is deliberately causal: it never specifies a future pitch or rhythm.
    It only interprets the current event as phrase attack, connected body,
    local peak, or release.
    """

    maturity = max(0.0, min(1.0, context.phrase_maturity))
    tension = max(0.0, min(1.0, context.tension))
    interval = (
        context.pitch_midi - context.previous_pitch_midi
        if context.previous_pitch_midi is not None
        else 0
    )
    reasons: list[str] = []

    # Phrase attack: clear tongue after a breath, but keep long entrances round.
    if context.breath_before or context.phrase_start or maturity <= 0.12:
        if context.duration_beats >= 0.9:
            reasons.append("rounded phrase attack")
            return SaxArcDecision(
                "attack",
                add_articulations=("tongued",),
                velocity_delta=-2,
                attack_scale=0.72,
                reason=tuple(reasons),
            )
        reasons.append("clear phrase attack")
        return SaxArcDecision(
            "attack",
            add_articulations=("tongued",),
            velocity_delta=2,
            attack_scale=0.92,
            reason=tuple(reasons),
        )

    # Phrase release has priority over local accenting.
    if context.phrase_end or maturity >= 0.88:
        reasons.append("phrase release")
        return SaxArcDecision(
            "release",
            remove_articulations=("accent", "tongued"),
            velocity_delta=-5,
            attack_scale=0.85,
            release_shape="open",
            reason=tuple(reasons),
        )

    # Local peak: a rising arrival in the later-middle part of the phrase.
    if 0.52 <= maturity <= 0.80 and interval >= 3 and context.duration_beats >= 0.5:
        reasons.append("rising phrase peak")
        return SaxArcDecision(
            "peak",
            add_articulations=("accent",),
            remove_articulations=("subtone",),
            velocity_delta=7 if tension < 0.8 else 4,
            attack_scale=1.08,
            reason=tuple(reasons),
        )

    # Body: use connected slur groups, but periodically rearticulate so a fast
    # line does not turn into one endlessly legato stream.
    close_motion = abs(interval) <= 4
    rearticulate = context.notes_since_breath > 0 and context.notes_since_breath % 4 == 0
    if close_motion and not rearticulate and context.duration_beats <= 0.8:
        reasons.append("connected phrase body")
        return SaxArcDecision(
            "body",
            add_articulations=("legato",),
            remove_articulations=("tongued", "accent"),
            velocity_delta=0,
            attack_scale=0.52,
            release_shape="connected",
            reason=tuple(reasons),
        )

    reasons.append("periodic phrase rearticulation")
    return SaxArcDecision(
        "body",
        add_articulations=("tongued",),
        remove_articulations=("legato",),
        velocity_delta=1,
        attack_scale=0.88,
        reason=tuple(reasons),
    )


def apply_sax_arc(
    articulations: tuple[str, ...] | list[str],
    velocity: int,
    attack_scale: float,
    release_shape: str,
    decision: SaxArcDecision,
) -> tuple[tuple[str, ...], int, float, str]:
    tags = [str(x) for x in articulations if str(x) not in set(decision.remove_articulations)]
    for tag in decision.add_articulations:
        if tag not in tags:
            tags.append(tag)

    # Keep expressive payload intentionally sparse.
    if len(tags) > 4:
        tags = tags[:4]

    velocity = max(1, min(127, velocity + decision.velocity_delta))
    attack_scale = max(0.2, min(1.5, attack_scale * decision.attack_scale))
    if decision.release_shape is not None:
        release_shape = decision.release_shape
    return tuple(tags), velocity, attack_scale, release_shape
