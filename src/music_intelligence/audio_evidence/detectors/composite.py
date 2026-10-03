"""Compose replaceable detector outputs into raw AudioObservation objects."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from ..adapters.source import AudioSource
from ..observation.models import AudioObservation, DetectorEvidence
from .contracts import (
    InstrumentDetection,
    InstrumentDetector,
    OnsetDetection,
    OnsetDetector,
    PitchDetection,
    PitchDetector,
    TimbreDetection,
    TimbreDetector,
    UnpitchedDetection,
    UnpitchedDetector,
)


def _by_onset(items):
    result = {}
    for item in items:
        result.setdefault(item.onset_id, []).append(item)
    return result


@dataclass
class CompositeObservationDetector:
    """Build observations while preserving detector-specific evidence.

    Multiple PitchDetection objects sharing one onset become separate pitch
    hypotheses with a shared onset and polyphony estimate. No musical voice,
    chord, harmony, or notation decision is made here.
    """

    onset_detector: OnsetDetector
    pitch_detector: PitchDetector | None = None
    instrument_detector: InstrumentDetector | None = None
    timbre_detector: TimbreDetector | None = None
    unpitched_detector: UnpitchedDetector | None = None
    detector_id: str = "composite-audio-observation-detector"

    def detect(self, source: AudioSource) -> Sequence[AudioObservation]:
        source.validate()
        onsets = tuple(self.onset_detector.detect_onsets(source))
        for onset in onsets:
            onset.validate()

        pitches = (
            tuple(self.pitch_detector.detect_pitches(source, onsets))
            if self.pitch_detector is not None
            else ()
        )
        instruments = (
            tuple(self.instrument_detector.detect_instruments(source, onsets))
            if self.instrument_detector is not None
            else ()
        )
        timbres = (
            tuple(self.timbre_detector.detect_timbre(source, onsets))
            if self.timbre_detector is not None
            else ()
        )
        unpitched = (
            tuple(self.unpitched_detector.detect_unpitched(source, onsets))
            if self.unpitched_detector is not None
            else ()
        )

        for item in (*pitches, *instruments, *timbres, *unpitched):
            item.validate()

        pitch_map = _by_onset(pitches)
        instrument_map = _by_onset(instruments)
        timbre_map = _by_onset(timbres)
        unpitched_map = _by_onset(unpitched)
        observations: list[AudioObservation] = []

        for onset in onsets:
            onset_pitches: tuple[PitchDetection, ...] = tuple(
                pitch_map.get(onset.onset_id, ())
            )
            onset_instruments: tuple[InstrumentDetection, ...] = tuple(
                instrument_map.get(onset.onset_id, ())
            )
            onset_timbres: tuple[TimbreDetection, ...] = tuple(
                timbre_map.get(onset.onset_id, ())
            )
            onset_unpitched: tuple[UnpitchedDetection, ...] = tuple(
                unpitched_map.get(onset.onset_id, ())
            )

            instrument_probs = (
                dict(onset_instruments[0].probabilities)
                if onset_instruments
                else {}
            )
            instrument_confidence = (
                onset_instruments[0].confidence if onset_instruments else None
            )
            centroid = (
                onset_timbres[0].spectral_centroid_hz
                if onset_timbres
                else None
            )

            detector_evidence = [
                DetectorEvidence(
                    detector_id=self.onset_detector.detector_id,
                    evidence_kind="onset",
                    confidence=onset.confidence,
                    detail=onset.onset_id,
                )
            ]
            detector_evidence.extend(
                DetectorEvidence(
                    detector_id=item.detector_id,
                    evidence_kind="instrument",
                    confidence=item.confidence,
                    detail=item.onset_id,
                )
                for item in onset_instruments
            )
            detector_evidence.extend(
                DetectorEvidence(
                    detector_id=item.detector_id,
                    evidence_kind="timbre",
                    detail=item.onset_id,
                )
                for item in onset_timbres
            )

            if onset_pitches:
                polyphony = len(onset_pitches)
                for pitch in onset_pitches:
                    local_evidence = list(detector_evidence)
                    local_evidence.append(
                        DetectorEvidence(
                            detector_id=self.pitch_detector.detector_id,
                            evidence_kind="pitch",
                            confidence=pitch.confidence,
                            detail=pitch.pitch_id,
                        )
                    )
                    observations.append(
                        AudioObservation(
                            observation_id=source.source_id + ":" + pitch.pitch_id,
                            source_id=source.source_id,
                            onset_seconds=onset.onset_seconds,
                            offset_seconds=(
                                pitch.offset_seconds
                                if pitch.offset_seconds is not None
                                else onset.offset_seconds
                            ),
                            nominal_midi=pitch.nominal_midi,
                            frequency_hz=pitch.frequency_hz,
                            instrument_probabilities=instrument_probs,
                            onset_confidence=onset.confidence,
                            pitch_confidence=pitch.confidence,
                            instrument_confidence=instrument_confidence,
                            spectral_centroid_hz=centroid,
                            polyphony_estimate=polyphony,
                            detector_evidence=tuple(local_evidence),
                            provenance=(
                                "audio-evidence:composite-observation",
                                "onset:" + onset.onset_id,
                            ),
                        )
                    )
            for index, token in enumerate(onset_unpitched, start=1):
                local_evidence = list(detector_evidence)
                local_evidence.append(
                    DetectorEvidence(
                        detector_id=self.unpitched_detector.detector_id,
                        evidence_kind="unpitched",
                        confidence=token.confidence,
                        detail=token.token,
                    )
                )
                observations.append(
                    AudioObservation(
                        observation_id=(
                            source.source_id
                            + ":"
                            + onset.onset_id
                            + ":unpitched:"
                            + str(index)
                        ),
                        source_id=source.source_id,
                        onset_seconds=onset.onset_seconds,
                        offset_seconds=onset.offset_seconds,
                        unpitched_token=token.token,
                        instrument_probabilities=instrument_probs,
                        onset_confidence=onset.confidence,
                        instrument_confidence=instrument_confidence,
                        spectral_centroid_hz=centroid,
                        polyphony_estimate=0,
                        detector_evidence=tuple(local_evidence),
                        provenance=(
                            "audio-evidence:composite-observation",
                            "onset:" + onset.onset_id,
                        ),
                    )
                )

        return tuple(observations)
