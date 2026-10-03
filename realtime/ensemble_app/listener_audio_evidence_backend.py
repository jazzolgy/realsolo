"""Model/detector adapter for the canonical StreamingAudioEvidenceEngine.

This module may use realtime-specific feature/model implementations, but it does
not construct PerformanceEvidence and does not own the raw/posterior contract.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field

from music_intelligence.audio_evidence import ContextCorrection, DetectorEvidence

from .audio_features import AudioFeatureExtractor
from .beat_tracker import AdaptiveBeatTracker
from .phrase_tracker import PhraseTracker
from .instrument_role_detector import AcousticDescriptorFrame, TemporalContextCorrector
from .learned_instrument_adapter import (
    HybridInstrumentRoleDetector,
    LearnedInstrumentBackend,
    LearnedInstrumentRoleAdapter,
)
from .musical_context_corrector import MusicalContextCorrector, MusicalContextFrame


@dataclass
class ListenerAudioEvidenceBackend:
    learned_instrument_backend: LearnedInstrumentBackend | None = None
    _extractors: dict[tuple[str,int],AudioFeatureExtractor] = field(default_factory=dict)
    _detectors: dict[str,HybridInstrumentRoleDetector] = field(default_factory=dict)
    _temporal: dict[str,TemporalContextCorrector] = field(default_factory=dict)
    _musical: dict[str,MusicalContextCorrector] = field(default_factory=dict)
    _beats: dict[str,AdaptiveBeatTracker] = field(default_factory=dict)
    _phrases: dict[str,PhraseTracker] = field(default_factory=dict)
    _last: dict[str,dict] = field(default_factory=dict)

    def _detector(self, source_id: str) -> HybridInstrumentRoleDetector:
        if source_id not in self._detectors:
            learned=(
                LearnedInstrumentRoleAdapter(self.learned_instrument_backend)
                if self.learned_instrument_backend is not None else None
            )
            self._detectors[source_id]=HybridInstrumentRoleDetector(learned=learned)
        return self._detectors[source_id]

    def detect_float32(
        self,
        source_id: str,
        payload: bytes,
        *,
        sample_rate: int,
        timestamp_s: float,
    ) -> DetectorEvidence:
        try:
            import numpy as np
        except ImportError as exc:
            raise RuntimeError('Install audio support with: pip install -e ".[audio]"') from exc

        samples=np.frombuffer(payload,dtype="<f4")
        extractor=self._extractors.setdefault(
            (source_id,sample_rate),AudioFeatureExtractor(sample_rate=sample_rate)
        )
        obs=extractor.process(samples,timestamp_s)
        frame=AcousticDescriptorFrame(
            pitch_hz=obs.pitch_hz,
            pitch_confidence=float(obs.pitch_confidence),
            onset=bool(obs.onset),
            onset_strength=float(obs.onset_strength),
            rms=float(obs.rms),
            spectral_centroid_hz=obs.spectral_centroid_hz,
            spectral_flatness=obs.spectral_flatness,
            zero_crossing_rate=obs.zero_crossing_rate,
            low_energy_ratio=obs.low_energy_ratio,
            mid_energy_ratio=obs.mid_energy_ratio,
            high_energy_ratio=obs.high_energy_ratio,
        )
        raw=self._detector(source_id).detect(
            samples,sample_rate=sample_rate,frame=frame
        )
        beat=self._beats.setdefault(source_id,AdaptiveBeatTracker()).update(obs)
        phrase=self._phrases.setdefault(source_id,PhraseTracker()).update(obs,beat)
        self._last[source_id]={
            "observation":obs,
            "beat":beat,
            "phrase":phrase,
        }
        return raw

    def correct(
        self,
        source_id: str,
        raw: DetectorEvidence,
        *,
        timestamp_s: float,
    ) -> ContextCorrection:
        state=self._last.get(source_id)
        if state is None:
            raise RuntimeError("detector context missing for source")
        prior=self._temporal.setdefault(
            source_id,TemporalContextCorrector()
        ).correct(raw)
        obs=state["observation"]
        return self._musical.setdefault(
            source_id,MusicalContextCorrector()
        ).correct(
            raw,
            prior,
            MusicalContextFrame(
                beat=state["beat"],
                phrase=state["phrase"],
                pitch_hz=obs.pitch_hz,
                onset=bool(obs.onset),
            ),
        )

    def observation_payload(self, source_id: str) -> dict:
        state=self._last.get(source_id)
        if state is None:
            return {}
        payload=asdict(state["observation"])
        kind=payload.get("kind")
        if hasattr(kind,"value"):
            payload["kind"]=kind.value
        return payload

    def musical_moment_kwargs(self, source_id: str) -> dict:
        state=self._last.get(source_id)
        if state is None:
            return {}
        obs=state["observation"]
        beat=state["beat"]
        return {
            "tempo_bpm":beat.tempo_bpm if beat.confidence >= .35 else None,
            "beat_position":beat.phase if beat.confidence >= .35 else None,
            "register_center":obs.note if obs.pitch_confidence >= .45 else None,
        }
