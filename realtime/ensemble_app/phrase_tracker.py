from __future__ import annotations

from dataclasses import replace

from .models import BeatState, PhraseState


class PhraseTracker:
    """Input-agnostic online activity/space tracker."""

    def __init__(self, *, phrase_end_beats: float = 1.15, fallback_phrase_end_s: float = 0.8) -> None:
        self.phrase_end_beats = phrase_end_beats
        self.fallback_phrase_end_s = fallback_phrase_end_s
        self.state = PhraseState()
        self._end_emitted = False

    def update(self, obs, beat: BeatState) -> PhraseState:
        s = self.state
        if obs.is_attack:
            n = s.attack_count + 1
            velocity = getattr(obs, "velocity", 0)
            mean_velocity = ((s.mean_velocity * s.attack_count) + velocity) / n
            self._end_emitted = False
            self.state = PhraseState(
                active=True,
                attack_count=n,
                last_attack_time=obs.timestamp,
                last_pitch=getattr(obs, "note", None) or s.last_pitch,
                mean_velocity=mean_velocity,
                phrase_end=False,
                silence_beats=0.0,
            )
            return self.state

        if s.last_attack_time is None:
            return replace(s, phrase_end=False)

        silence_s = max(0.0, obs.timestamp - s.last_attack_time)
        if beat.beat_period_s:
            silence_beats = silence_s / beat.beat_period_s
            ended = silence_beats >= self.phrase_end_beats
        else:
            silence_beats = 0.0
            ended = silence_s >= self.fallback_phrase_end_s

        emit_end = ended and not self._end_emitted and s.attack_count > 0
        if emit_end:
            self._end_emitted = True

        self.state = replace(
            s,
            active=not ended,
            phrase_end=emit_end,
            silence_beats=silence_beats,
        )
        return self.state
