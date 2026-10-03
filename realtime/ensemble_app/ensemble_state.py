from __future__ import annotations

from dataclasses import replace

from .models import (
    AudioObservation,
    BeatState,
    EnsembleState,
    MidiObservation,
    ObservationKind,
    PhraseState,
)


class EnsembleStateStore:
    def __init__(self) -> None:
        self.state = EnsembleState()

    def update(self, obs, beat: BeatState, phrase: PhraseState) -> EnsembleState:
        notes = set(self.state.active_notes)
        input_mode = self.state.input_mode
        audio_rms = self.state.audio_rms
        audio_peak = self.state.audio_peak
        audio_onset_strength = self.state.audio_onset_strength
        audio_pitch_hz = self.state.audio_pitch_hz
        audio_pitch_confidence = self.state.audio_pitch_confidence

        if isinstance(obs, MidiObservation) and obs.kind != ObservationKind.CLOCK_TICK:
            input_mode = "midi" if input_mode in ("unknown", "midi") else "hybrid"
            if obs.kind == ObservationKind.NOTE_ON and obs.note is not None and obs.velocity > 0:
                notes.add(obs.note)
            elif obs.kind in (ObservationKind.NOTE_OFF, ObservationKind.NOTE_ON) and obs.note is not None:
                notes.discard(obs.note)
        elif isinstance(obs, AudioObservation):
            input_mode = "audio" if input_mode in ("unknown", "audio") else "hybrid"
            audio_rms = obs.rms
            audio_peak = obs.peak
            audio_onset_strength = obs.onset_strength
            audio_pitch_hz = obs.pitch_hz
            audio_pitch_confidence = obs.pitch_confidence

        target = (getattr(obs, "velocity", 0) / 127.0) if obs.is_attack else self.state.human_activity * 0.96
        activity = max(0.0, min(1.0, 0.72 * self.state.human_activity + 0.28 * target))
        self.state = replace(
            self.state,
            now=obs.timestamp,
            beat=beat,
            phrase=phrase,
            active_notes=frozenset(notes),
            human_activity=activity,
            revision=self.state.revision + 1,
            input_mode=input_mode,
            audio_rms=audio_rms,
            audio_peak=audio_peak,
            audio_onset_strength=audio_onset_strength,
            audio_pitch_hz=audio_pitch_hz,
            audio_pitch_confidence=audio_pitch_confidence,
        )
        return self.state
