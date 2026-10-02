"""Lightweight drummer calibration telemetry for A/B evaluation."""
from __future__ import annotations

from dataclasses import dataclass

from .model import DrumGesture, DrumVoice, GestureRole


@dataclass
class BebopCalibrationTelemetry:
    decisions: int = 0
    active_gestures: int = 0
    space_gestures: int = 0
    snare_statements: int = 0
    snare_returns: int = 0
    snare_displaced_returns: int = 0
    intentional_non_responses: int = 0
    bass_floor_events: int = 0
    bass_bombs: int = 0
    ride_skip_hits: int = 0
    ride_skip_omissions: int = 0
    setup_events: int = 0

    def observe(self, gesture: DrumGesture) -> None:
        gesture.validate()
        self.decisions += 1
        if gesture.role is GestureRole.SPACE:
            self.space_gestures += 1
        else:
            self.active_gestures += 1

        voices = {hit.voice for hit in gesture.hits}
        if DrumVoice.SNARE in voices and "snare_phrase" in gesture.tags:
            self.snare_statements += 1
        if "return" in gesture.tags:
            self.snare_returns += 1
        if "displaced_return" in gesture.tags:
            self.snare_displaced_returns += 1
        if "intentional_non_response" in gesture.tags:
            self.intentional_non_responses += 1
        if "bass_floor_support" in gesture.tags:
            self.bass_floor_events += 1
        if "bass_bomb" in gesture.tags:
            self.bass_bombs += 1
        if "skip" in gesture.tags and DrumVoice.RIDE in voices:
            self.ride_skip_hits += 1
        if "omit_skip" in gesture.tags:
            self.ride_skip_omissions += 1
        if gesture.role is GestureRole.SETUP:
            self.setup_events += 1

    @property
    def active_ratio(self) -> float:
        return self.active_gestures / self.decisions if self.decisions else 0.0

    @property
    def snare_return_share(self) -> float:
        if not self.snare_statements:
            return 0.0
        return (
            self.snare_returns + self.snare_displaced_returns
        ) / self.snare_statements

    @property
    def ride_skip_omission_share(self) -> float:
        total = self.ride_skip_hits + self.ride_skip_omissions
        return self.ride_skip_omissions / total if total else 0.0

    def snapshot(self) -> dict[str, float | int]:
        return {
            "decisions": self.decisions,
            "active_gestures": self.active_gestures,
            "space_gestures": self.space_gestures,
            "active_ratio": round(self.active_ratio, 6),
            "snare_statements": self.snare_statements,
            "snare_returns": self.snare_returns,
            "snare_displaced_returns": self.snare_displaced_returns,
            "snare_return_share": round(self.snare_return_share, 6),
            "intentional_non_responses": self.intentional_non_responses,
            "bass_floor_events": self.bass_floor_events,
            "bass_bombs": self.bass_bombs,
            "ride_skip_hits": self.ride_skip_hits,
            "ride_skip_omissions": self.ride_skip_omissions,
            "ride_skip_omission_share": round(self.ride_skip_omission_share, 6),
            "setup_events": self.setup_events,
        }
