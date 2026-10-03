"""Conservative realtime instrument/role evidence for mixed research audio.

This is a baseline front-end, not a production source separator. It converts
measured acoustic descriptors into broad, uncertainty-preserving probabilities.
Hard-to-distinguish pitched instruments remain partially unresolved instead of
being forced into a named class.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping

from music_intelligence.audio_evidence import (
    ContextCorrection,
    DetectorEvidence,
)


def _normalize(weights: Mapping[str,float], *, max_mass: float=.95) -> dict[str,float]:
    positive={k:max(0.0,float(v)) for k,v in weights.items() if float(v)>0.0}
    total=sum(positive.values())
    if total<=0:
        return {}
    scale=min(1.0,max_mass/total)
    return {k:round(v*scale,6) for k,v in positive.items()}


@dataclass(frozen=True)
class AcousticDescriptorFrame:
    pitch_hz: float | None
    pitch_confidence: float
    onset: bool
    onset_strength: float
    rms: float
    spectral_centroid_hz: float | None = None
    spectral_flatness: float | None = None
    zero_crossing_rate: float | None = None
    low_energy_ratio: float | None = None
    mid_energy_ratio: float | None = None
    high_energy_ratio: float | None = None


@dataclass
class BaselineInstrumentRoleDetector:
    """Unknown-first detector from measured signal descriptors.

    It can form useful evidence for drums and bass-family activity and a broad
    foreground-pitched hypothesis. It deliberately does not pretend that simple
    spectral statistics can reliably separate trumpet/sax/flute/vocal/guitar/piano
    in a mixed jazz recording.
    """

    def detect(self, frame: AcousticDescriptorFrame) -> DetectorEvidence:
        pitch_conf=max(0.0,min(1.0,float(frame.pitch_confidence)))
        onset=max(0.0,min(1.0,float(frame.onset_strength)))
        flat=frame.spectral_flatness
        high=frame.high_energy_ratio
        low=frame.low_energy_ratio
        zcr=frame.zero_crossing_rate
        pitch=frame.pitch_hz

        drum=0.0
        if frame.onset:
            drum += .28 + .28*onset
        if flat is not None:
            drum += .24*max(0.0,min(1.0,flat))
        if zcr is not None:
            drum += .12*max(0.0,min(1.0,zcr*8.0))
        drum *= (1.0-.55*pitch_conf)

        bass_family=0.0
        if pitch is not None and pitch < 260:
            bass_family += .30 + .35*pitch_conf
        if low is not None:
            bass_family += .30*max(0.0,min(1.0,low))
        if flat is not None:
            bass_family *= 1.0-.35*max(0.0,min(1.0,flat))

        pitched_foreground=.0
        if pitch is not None:
            pitched_foreground=.25+.55*pitch_conf
            if frame.onset:
                pitched_foreground += .08

        # Acoustic vs electric bass is intentionally unresolved at this stage.
        bass_split=.5*bass_family
        instruments=_normalize({
            "drums":drum,
            "acoustic_bass":bass_split,
            "electric_bass":bass_split,
            "unknown_pitched":pitched_foreground,
        },max_mass=.92)

        roles=_normalize({
            "timekeeping":drum*.75,
            "bass_line":bass_family*.78,
            "melody_or_solo":pitched_foreground*.62,
            "comping_or_support":pitched_foreground*.24,
            "unknown":.18,
        },max_mass=.92)

        instrument_conf=max(instruments.values(),default=0.0)
        role_conf=max(roles.values(),default=0.0)
        event_conf=max(pitch_conf,min(1.0,onset))
        return DetectorEvidence(
            instrument_probabilities=instruments,
            role_probabilities=roles,
            confidence_fields={
                "pitch":pitch_conf,
                "instrument":instrument_conf,
                "role":role_conf,
                "event":event_conf,
            },
            pitch_hz=pitch,
            onset=frame.onset,
            onset_strength=frame.onset_strength,
            rms=frame.rms,
        )


@dataclass
class TemporalContextCorrector:
    """Small causal posterior correction using continuity only.

    No provider/search metadata is used as musical evidence. The correction is
    bounded so a weak raw detector cannot become highly certain merely because
    the previous frame had a label.
    """

    memory: float = .68
    max_context_boost: float = .18
    _instrument_history: dict[str,float] = field(default_factory=dict)
    _role_history: dict[str,float] = field(default_factory=dict)

    def correct(self, raw: DetectorEvidence) -> ContextCorrection:
        raw.validate()
        instruments=self._blend(raw.instrument_probabilities,self._instrument_history)
        roles=self._blend(raw.role_probabilities,self._role_history)
        self._instrument_history=dict(instruments)
        self._role_history=dict(roles)

        raw_i=max(raw.instrument_probabilities.values(),default=0.0)
        post_i=max(instruments.values(),default=0.0)
        raw_r=max(raw.role_probabilities.values(),default=0.0)
        post_r=max(roles.values(),default=0.0)
        confidence=dict(raw.confidence_fields)
        confidence["instrument"]=min(1.0,max(raw_i,post_i))
        confidence["role"]=min(1.0,max(raw_r,post_r))
        confidence["contextual_correction_magnitude"]=min(
            1.0,
            max(abs(post_i-raw_i),abs(post_r-raw_r)),
        )
        reasons=("temporal_instrument_continuity","temporal_role_continuity")
        return ContextCorrection(
            instrument_probabilities=instruments,
            role_probabilities=roles,
            confidence_fields=confidence,
            reasons=reasons,
        )

    def _blend(self,current: Mapping[str,float],history: Mapping[str,float]) -> dict[str,float]:
        if not current:
            return {}
        keys=set(current)|set(history)
        mixed={}
        for key in keys:
            raw=float(current.get(key,0.0))
            prior=float(history.get(key,0.0))
            boost=min(self.max_context_boost,self.memory*prior)
            mixed[key]=raw+boost*raw
        return _normalize(mixed,max_mass=.95)
