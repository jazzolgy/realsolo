from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SaxPhraseContext:
    pitch_midi: int
    previous_pitch_midi: int | None
    duration_beats: float
    beat_in_bar: float
    phrase_maturity: float
    source_family: str = ""
    score_phrase_boundary_before: bool = False
    score_phrase_boundary_after: bool = False


@dataclass(frozen=True, slots=True)
class SaxPhraseDecision:
    connect_legato: bool = False
    breath_before: bool = False
    soften_attack: bool = False
    release_shape: str = "normal"
    phrase_start: bool = False
    phrase_end: bool = False
    reason: tuple[str, ...] = ()


@dataclass(slots=True)
class SaxPhraseMemory:
    notes_since_breath: int = 0
    beats_since_breath: float = 0.0
    last_pitch_midi: int | None = None
    last_duration_beats: float = 0.0
    last_phrase_maturity: float = 0.0

    def reset(self) -> None:
        self.notes_since_breath = 0
        self.beats_since_breath = 0.0
        self.last_pitch_midi = None
        self.last_duration_beats = 0.0
        self.last_phrase_maturity = 0.0

    def decide(self, context: SaxPhraseContext) -> SaxPhraseDecision:
        maturity = max(0.0, min(1.0, context.phrase_maturity))
        interval = (
            abs(context.pitch_midi - context.previous_pitch_midi)
            if context.previous_pitch_midi is not None
            else 0
        )
        reasons: list[str] = []

        heuristic_start = context.previous_pitch_midi is None or maturity <= 0.08
        heuristic_end = maturity >= 0.9 and context.duration_beats >= 0.75

        phrase_start = context.score_phrase_boundary_before or heuristic_start
        phrase_end = context.score_phrase_boundary_after or heuristic_end

        if context.score_phrase_boundary_before:
            reasons.append("explicit score phrase-start boundary")
        if context.score_phrase_boundary_after:
            reasons.append("explicit score phrase-end boundary")

        breath_due = (
            self.notes_since_breath >= 7
            or self.beats_since_breath >= 5.5
            or (phrase_start and self.notes_since_breath > 0)
        )
        breath_before = bool(breath_due and not phrase_end)
        if breath_before:
            reasons.append("breath reset before new phrase cell")

        connect_legato = (
            not breath_before
            and context.previous_pitch_midi is not None
            and interval <= 4
            and context.duration_beats <= 0.8
            and not phrase_end
        )
        if connect_legato:
            reasons.append("stepwise phrase connection")

        soften_attack = bool(connect_legato or (phrase_start and context.duration_beats >= 0.75))
        if soften_attack and not connect_legato:
            reasons.append("soft phrase entrance")

        release_shape = "normal"
        if phrase_end:
            release_shape = "open"
            reasons.append("phrase-ending open release")
        elif connect_legato:
            release_shape = "connected"

        return SaxPhraseDecision(
            connect_legato=connect_legato,
            breath_before=breath_before,
            soften_attack=soften_attack,
            release_shape=release_shape,
            phrase_start=phrase_start,
            phrase_end=phrase_end,
            reason=tuple(reasons),
        )

    def commit(self, context: SaxPhraseContext, decision: SaxPhraseDecision) -> None:
        if decision.breath_before:
            self.notes_since_breath = 0
            self.beats_since_breath = 0.0
        self.notes_since_breath += 1
        self.beats_since_breath += context.duration_beats
        self.last_pitch_midi = context.pitch_midi
        self.last_duration_beats = context.duration_beats
        self.last_phrase_maturity = context.phrase_maturity
