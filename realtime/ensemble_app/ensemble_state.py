from __future__ import annotations

from dataclasses import replace

from .models import BeatState, EnsembleState, MidiObservation, ObservationKind, PhraseState


class EnsembleStateStore:
    def __init__(self) -> None:
        self.state = EnsembleState()

    def update(self, obs: MidiObservation, beat: BeatState, phrase: PhraseState) -> EnsembleState:
        notes = set(self.state.active_notes)
        if obs.kind == ObservationKind.NOTE_ON and obs.note is not None and obs.velocity > 0:
            notes.add(obs.note)
        elif obs.kind in (ObservationKind.NOTE_OFF, ObservationKind.NOTE_ON) and obs.note is not None:
            notes.discard(obs.note)

        target = (obs.velocity / 127.0) if obs.is_attack else self.state.human_activity * 0.96
        activity = max(0.0, min(1.0, 0.72 * self.state.human_activity + 0.28 * target))
        self.state = replace(
            self.state,
            now=obs.timestamp,
            beat=beat,
            phrase=phrase,
            active_notes=frozenset(notes),
            human_activity=activity,
            revision=self.state.revision + 1,
        )
        return self.state
