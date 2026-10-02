from __future__ import annotations

from dataclasses import dataclass
import re

from music_intelligence.reasoning.legend_style_core import (
    CandidateEvent,
    MusicalContextVector,
)
from music_intelligence.reasoning.online_improviser import (
    OnlineMusicalEvaluator,
    PerformanceMemory,
    SoftPlan,
    perform_one_event,
)
from players.sax import (
    SaxExpressionContext,
    SaxPhraseContext,
    SaxPhraseMemory,
    choose_sax_expression,
)

ROOTS = {
    "C": 0, "C#": 1, "Db": 1, "D": 2, "D#": 3, "Eb": 3,
    "E": 4, "F": 5, "F#": 6, "Gb": 6, "G": 7, "G#": 8,
    "Ab": 8, "A": 9, "A#": 10, "Bb": 10, "B": 11,
}
ROOT_RE = re.compile(r"^([A-G](?:#|b)?)(.*)$")


@dataclass(frozen=True, slots=True)
class ParsedChord:
    symbol: str
    root_pc: int
    intervals: tuple[int, ...]

    @property
    def pitch_classes(self) -> tuple[int, ...]:
        return tuple((self.root_pc + i) % 12 for i in self.intervals)


def parse_chord(symbol: str) -> ParsedChord:
    main = symbol.split("/", 1)[0]
    m = ROOT_RE.match(main)
    if not m:
        return ParsedChord(symbol, 0, (0, 4, 7))
    root, quality = m.groups()
    q = quality.lower()

    if "m7b5" in q or "ø" in q:
        intervals = (0, 3, 6, 10)
    elif "dim" in q or "°" in q:
        intervals = (0, 3, 6, 9)
    elif q.startswith("m") and not q.startswith("maj"):
        intervals = (0, 3, 7, 10)
    elif "maj7" in q or "Δ" in quality:
        intervals = (0, 4, 7, 11)
    elif "7" in q:
        intervals = (0, 4, 7, 10)
    else:
        intervals = (0, 4, 7)
    return ParsedChord(symbol, ROOTS.get(root, 0), intervals)


def midi_near(pc: int, center: int) -> int:
    base = center - (center % 12) + pc
    choices = (base - 12, base, base + 12)
    return min(choices, key=lambda n: abs(n - center))


def accompaniment_frame(chord_symbol: str, beat_index: int) -> dict:
    """Immediate Stage-1 playback frame, never a precomputed chorus."""

    chord = parse_chord(chord_symbol)
    pcs = chord.pitch_classes
    root = midi_near(chord.root_pc, 40)
    if root > 47:
        root -= 12

    guide_pcs = list(pcs[1:]) if len(pcs) > 1 else [chord.root_pc]
    voicing = sorted({midi_near(pc, 60) for pc in guide_pcs})
    # Keep comping open enough for a human soloist.
    comp = voicing[:4] if beat_index in (1, 3) else []

    return {
        "bass": [root],
        "comp": comp,
        "drums": {
            "ride": True,
            "hat": beat_index in (1, 3),
            "kick": beat_index in (0, 2),
        },
    }


class Stage1Soloist:
    """Temporary Stage-1 candidate adapter around the shared Core evaluator.

    Candidate generation should ultimately move into shared Core / player
    grammar. This adapter exists so the chart product can exercise the true
    one-event commitment contract now.
    """

    def __init__(self) -> None:
        self.evaluator = OnlineMusicalEvaluator()
        self.memory = PerformanceMemory()
        self.previous_pitch: int | None = None
        self.phrase_memory = SaxPhraseMemory()

    def reset(self) -> None:
        self.memory = PerformanceMemory()
        self.previous_pitch = None
        self.phrase_memory.reset()

    def choose(
        self,
        chord_symbol: str,
        next_chord: str = "",
        *,
        beat_in_bar: float = 0.0,
        phrase_step: int = 0,
    ) -> dict:
        chord = parse_chord(chord_symbol)
        center = self.previous_pitch if self.previous_pitch is not None else 67

        candidates: list[CandidateEvent] = []
        for pc in chord.pitch_classes:
            pitch = midi_near(pc, center)
            for candidate_pitch in (pitch - 12, pitch, pitch + 12):
                if 52 <= candidate_pitch <= 88:
                    if self.previous_pitch is not None and candidate_pitch == self.previous_pitch:
                        continue
                    tags = {"chord_tone"}
                    if len(chord.pitch_classes) >= 4 and pc in (chord.pitch_classes[1], chord.pitch_classes[-1]):
                        tags.add("guide_tone")
                    if self.previous_pitch is not None and abs(candidate_pitch - self.previous_pitch) >= 7:
                        tags.add("large_leap")
                    candidates.append(
                        CandidateEvent(
                            candidate_pitch,
                            duration_beats=0.5 if phrase_step % 3 else 1.0,
                            tags=frozenset(tags),
                            source_family="stage1_chart_tone",
                        )
                    )

        if self.previous_pitch is not None:
            for delta in (-2, -1, 1, 2):
                p = self.previous_pitch + delta
                if 52 <= p <= 88:
                    candidates.append(
                        CandidateEvent(
                            p,
                            duration_beats=0.5,
                            tags=frozenset({"passing" if abs(delta) == 2 else "close_approach"}),
                            source_family="stage1_connector",
                        )
                    )

        plan = SoftPlan(
            horizon_beats=2.0,
            intention="continue chart-aware solo one event at a time",
            soft_targets=("voice-leading", "phrase continuity"),
            candidate_families=("chord_tone", "connector"),
        )
        next_harmony = next_chord or ""
        context = MusicalContextVector(
            chord_symbol=chord_symbol,
            metric_position=(beat_in_bar % 4.0) / 4.0,
            phrase_maturity=min(1.0, (phrase_step % 8) / 7.0),
            tension=0.55 if "7" in chord_symbol and "maj7" not in chord_symbol.lower() else 0.28,
            recent_large_leaps=(
                1
                if len(self.memory.committed) >= 2
                and self.memory.committed[-1].pitch_midi is not None
                and self.memory.committed[-2].pitch_midi is not None
                and abs(
                    self.memory.committed[-1].pitch_midi
                    - self.memory.committed[-2].pitch_midi
                ) >= 7
                else 0
            ),
            next_harmony=next_harmony,
        )
        chosen = perform_one_event(plan, self.evaluator, candidates, context, self.memory)
        event = chosen.candidate
        previous_pitch = self.previous_pitch
        phrase_maturity = context.phrase_maturity
        tension = context.tension
        phrase_context = (
            SaxPhraseContext(
                pitch_midi=event.pitch_midi,
                previous_pitch_midi=previous_pitch,
                duration_beats=event.duration_beats,
                beat_in_bar=beat_in_bar,
                phrase_maturity=phrase_maturity,
                source_family=event.source_family,
            )
            if event.pitch_midi is not None
            else None
        )
        phrase = self.phrase_memory.decide(phrase_context) if phrase_context is not None else None
        expression = (
            choose_sax_expression(
                SaxExpressionContext(
                    pitch_midi=event.pitch_midi,
                    previous_pitch_midi=previous_pitch,
                    duration_beats=event.duration_beats,
                    beat_in_bar=beat_in_bar,
                    phrase_maturity=phrase_maturity,
                    tension=tension,
                )
            )
            if event.pitch_midi is not None
            else None
        )
        if phrase_context is not None and phrase is not None:
            self.phrase_memory.commit(phrase_context, phrase)
        self.previous_pitch = event.pitch_midi
        articulation = list(expression.tags) if expression is not None else []
        if phrase is not None and phrase.connect_legato and "legato" not in articulation:
            articulation.append("legato")
        return {
            "pitch": event.pitch_midi,
            "duration_beats": event.duration_beats,
            "velocity": expression.velocity if expression is not None else 82,
            "articulation": articulation,
            "breath_before": phrase.breath_before if phrase is not None else False,
            "soften_attack": phrase.soften_attack if phrase is not None else False,
            "release_shape": phrase.release_shape if phrase is not None else "normal",
            "phrase_reasons": list(phrase.reason) if phrase is not None else [],
            "expression_reasons": list(expression.reason) if expression is not None else [],
            "reasons": list(chosen.reasons),
            "source_family": event.source_family,
            "committed_count": len(self.memory.committed),
        }
