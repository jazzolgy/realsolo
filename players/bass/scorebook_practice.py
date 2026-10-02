"""Scorebook-driven practice harness for the canonical Bass player.

This module does not parse PDF pages and does not own shared harmony theory.
It consumes already-structured HarmonicFrame pulses from Shared Core /
Transcribe adapters, runs the real causal bass player, and measures whether the
resulting practice chorus is becoming more idiomatic without collapsing into a
single template.

No copied scorebook melody or bass line is stored here.
"""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass

from music_intelligence.harmony.jazz_harmony_core import HarmonicFrame

from .immediate_realizer import BassHarmonicRole, BassMode
from .scorebook_evidence import BassScoreEvidenceDirective
from .sequential_runner import BassSequentialRunner, BassStepInput, BassStepResult


@dataclass(frozen=True)
class BassPracticePulse:
    frame: HarmonicFrame
    beat_in_measure: float
    absolute_beat: float
    mode: BassMode
    local_key_pitch_classes: frozenset[int] = frozenset()
    phrase_boundary: bool = False
    form_boundary: bool = False
    ensemble_activity: float = 0.5
    score_evidence: BassScoreEvidenceDirective = BassScoreEvidenceDirective()


@dataclass(frozen=True)
class BassPracticeSong:
    song_id: str
    title: str
    pulses: tuple[BassPracticePulse, ...]
    provenance: tuple[str, ...] = ()

    def validate(self) -> None:
        if not self.song_id or not self.title:
            raise ValueError("song_id/title required")
        if not self.pulses:
            raise ValueError("practice song requires pulses")
        last = None
        for p in self.pulses:
            p.frame.validate()
            if last is not None and p.absolute_beat <= last:
                raise ValueError("practice pulses must be strictly ordered")
            last = p.absolute_beat


@dataclass(frozen=True)
class BassPracticeMetrics:
    event_count: int
    role_counts: tuple[tuple[str, int], ...]
    route_variety: int
    approach_rate: float
    scale_linear_rate: float
    repeated_pitch_rate: float
    same_direction_run_rate: float
    long_step_chain_rate: float
    two_feel_color_rate: float
    register_low: int | None
    register_high: int | None

    @property
    def register_span(self) -> int:
        if self.register_low is None or self.register_high is None:
            return 0
        return self.register_high - self.register_low


@dataclass(frozen=True)
class BassPracticePassResult:
    pass_index: int
    results: tuple[BassStepResult, ...]
    metrics: BassPracticeMetrics


@dataclass(frozen=True)
class BassPracticeSession:
    song_id: str
    title: str
    passes: tuple[BassPracticePassResult, ...]
    provenance: tuple[str, ...] = ()


def _sign(value: int) -> int:
    return 1 if value > 0 else -1 if value < 0 else 0


def evaluate_practice_results(
    results: tuple[BassStepResult, ...],
) -> BassPracticeMetrics:
    if not results:
        return BassPracticeMetrics(
            0, (), 0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, None, None
        )

    roles = [x.candidate.harmonic_role.value for x in results]
    pitches = [x.candidate.event.pitch_midi for x in results]
    pitched = [p for p in pitches if p is not None]

    directed = {
        BassHarmonicRole.CHROMATIC_APPROACH.value,
        BassHarmonicRole.ANTICIPATION.value,
    }
    shared_linear = {
        BassHarmonicRole.DIATONIC_PASSING.value,
        BassHarmonicRole.NEIGHBOR.value,
        BassHarmonicRole.SCALE_COLOR.value,
    }

    repeats = sum(a == b for a, b in zip(pitched, pitched[1:]))
    intervals = [b - a for a, b in zip(pitched, pitched[1:])]

    same_direction_run_events = 0
    run_sign = 0
    run_len = 0
    long_step_chain_events = 0
    step_len = 0
    for delta in intervals:
        s = _sign(delta)
        if s and s == run_sign:
            run_len += 1
        elif s:
            run_sign = s
            run_len = 1
        else:
            run_sign = 0
            run_len = 0
        if run_len >= 3:
            same_direction_run_events += 1

        if 0 < abs(delta) <= 2:
            step_len += 1
        else:
            step_len = 0
        if step_len >= 4:
            long_step_chain_events += 1

    two_second = [
        x for x in results
        if x.candidate.grammar.metric_role.value == "two_feel_direction"
    ]
    two_color = sum(
        x.candidate.harmonic_role in {
            BassHarmonicRole.CHORD_TONE,
            BassHarmonicRole.SCALE_COLOR,
            BassHarmonicRole.NEIGHBOR,
            BassHarmonicRole.DIATONIC_PASSING,
        }
        for x in two_second
    )

    count = len(results)
    role_counts = tuple(sorted(Counter(roles).items()))
    return BassPracticeMetrics(
        event_count=count,
        role_counts=role_counts,
        route_variety=len(set(roles)),
        approach_rate=sum(r in directed for r in roles) / count,
        scale_linear_rate=sum(r in shared_linear for r in roles) / count,
        repeated_pitch_rate=repeats / max(1, len(pitched) - 1),
        same_direction_run_rate=same_direction_run_events / max(1, len(intervals)),
        long_step_chain_rate=long_step_chain_events / max(1, len(intervals)),
        two_feel_color_rate=two_color / max(1, len(two_second)),
        register_low=min(pitched) if pitched else None,
        register_high=max(pitched) if pitched else None,
    )


def run_scorebook_practice(
    song: BassPracticeSong,
    *,
    passes: int = 8,
    tempo_bpm: float = 120.0,
    register_low_midi: int = 28,
    register_high_midi: int = 52,
) -> BassPracticeSession:
    """Run repeated causal practice passes over one structured scorebook song.

    Each pass starts with fresh short-term performance memory. This measures the
    canonical policy itself instead of letting a prior chorus leak exact local
    state into the next chorus. Cross-pass learning belongs in grammar/model
    updates after aggregate evaluation, not hidden state.
    """
    song.validate()
    if passes <= 0:
        raise ValueError("passes must be positive")

    completed: list[BassPracticePassResult] = []
    for index in range(1, passes + 1):
        runner = BassSequentialRunner(
            tempo_bpm=tempo_bpm,
            register_low_midi=register_low_midi,
            register_high_midi=register_high_midi,
        )
        step_inputs = tuple(
            BassStepInput(
                frame=p.frame,
                mode=p.mode,
                beat_in_measure=p.beat_in_measure,
                absolute_beat=p.absolute_beat,
                phrase_boundary=p.phrase_boundary,
                form_boundary=p.form_boundary,
                ensemble_activity=p.ensemble_activity,
                local_key_pitch_classes=p.local_key_pitch_classes,
                score_evidence=p.score_evidence,
            )
            for p in song.pulses
        )
        results = runner.run(step_inputs)
        completed.append(BassPracticePassResult(
            pass_index=index,
            results=results,
            metrics=evaluate_practice_results(results),
        ))

    return BassPracticeSession(
        song_id=song.song_id,
        title=song.title,
        passes=tuple(completed),
        provenance=song.provenance + ("players/bass:scorebook-practice",),
    )
