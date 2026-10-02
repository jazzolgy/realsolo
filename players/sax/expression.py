from __future__ import annotations

from dataclasses import dataclass

from .articulation import SoloArticulation


@dataclass(frozen=True, slots=True)
class SaxExpressionContext:
    pitch_midi: int
    previous_pitch_midi: int | None
    duration_beats: float
    beat_in_bar: float
    phrase_maturity: float
    tension: float = 0.0
    velocity: int = 82


@dataclass(frozen=True, slots=True)
class SaxExpressionDecision:
    articulations: tuple[SoloArticulation, ...]
    velocity: int
    reason: tuple[str, ...] = ()

    @property
    def tags(self) -> tuple[str, ...]:
        return tuple(x.value for x in self.articulations)


def choose_sax_expression(context: SaxExpressionContext) -> SaxExpressionDecision:
    """Choose renderer-facing sax expression after the note has been selected.

    This policy never changes pitch or rhythm. It only decides how the already
    committed note should be voiced. The rules are intentionally sparse so the
    player does not decorate every event.
    """

    pitch = context.pitch_midi
    duration = context.duration_beats
    maturity = max(0.0, min(1.0, context.phrase_maturity))
    tension = max(0.0, min(1.0, context.tension))
    interval = (
        abs(pitch - context.previous_pitch_midi)
        if context.previous_pitch_midi is not None
        else 0
    )

    arts: list[SoloArticulation] = []
    reasons: list[str] = []
    velocity = max(1, min(127, context.velocity))

    # Short notes should sound articulated rather than artificially sustained.
    if duration <= 0.55:
        arts.append(SoloArticulation.SHORT)
        reasons.append("short note articulation")

    # Low-register, spacious notes benefit from air/subtone rather than attack.
    if duration >= 0.9 and pitch <= 60 and maturity < 0.72 and tension < 0.65:
        arts.append(SoloArticulation.SUBTONE)
        arts.append(SoloArticulation.BREATHY)
        velocity = max(56, velocity - 12)
        reasons.append("low-register spacious subtone")

    # A significant upward arrival may receive a restrained scoop/accent.
    if (
        context.previous_pitch_midi is not None
        and pitch > context.previous_pitch_midi
        and interval >= 7
        and duration >= 0.7
        and maturity < 0.8
    ):
        if SoloArticulation.SHORT not in arts:
            arts.append(SoloArticulation.SCOOP)
        arts.append(SoloArticulation.ACCENT)
        velocity = min(112, velocity + 6)
        reasons.append("large upward arrival")

    # Longer notes later in a phrase may develop vibrato.
    if duration >= 0.9 and maturity >= 0.45:
        arts.append(SoloArticulation.VIBRATO)
        reasons.append("late sustained note vibrato")

    # Phrase-ending long notes may release with a fall, but not every cadence.
    if duration >= 0.9 and maturity >= 0.86 and tension <= 0.72:
        arts.append(SoloArticulation.FALL)
        reasons.append("phrase-ending release")

    # High-tension notes should retain clarity rather than adding multiple colors.
    if tension >= 0.78:
        arts = [
            a for a in arts
            if a not in {
                SoloArticulation.SUBTONE,
                SoloArticulation.BREATHY,
                SoloArticulation.FALL,
            }
        ]
        if duration >= 0.75 and SoloArticulation.ACCENT not in arts:
            arts.append(SoloArticulation.ACCENT)
        reasons.append("high-tension clarity")

    # Default sound remains plain sustain. Keep at most three expressive tags.
    if not arts:
        arts.append(SoloArticulation.SUSTAIN)

    unique: list[SoloArticulation] = []
    for art in arts:
        if art not in unique:
            unique.append(art)
    unique = unique[:3]

    return SaxExpressionDecision(tuple(unique), velocity, tuple(reasons))
