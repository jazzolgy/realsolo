"""Replaceable learned instrument/role detector boundary.

The autonomous listener can use a learned mixed-audio or source-separated model
without changing Shared Audio Intelligence contracts. This module intentionally
does not bundle model weights or claim a specific classifier is present.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Protocol, Sequence

from music_intelligence.learning.shared_audio_intelligence import DetectorEvidence
from .instrument_catalog import normalize_instrument_label
from .instrument_role_detector import AcousticDescriptorFrame, BaselineInstrumentRoleDetector


class LearnedInstrumentBackend(Protocol):
    """Backend returns calibrated-or-calibratable probabilities for one frame/window."""

    def predict(
        self,
        samples,
        *,
        sample_rate: int,
    ) -> tuple[Mapping[str,float], Mapping[str,float], Mapping[str,float]]:
        """Return instrument probabilities, role probabilities, confidence fields."""
        ...


def _clean_distribution(
    raw: Mapping[str,float],
    *,
    normalize_instruments: bool,
    max_mass: float=.97,
) -> dict[str,float]:
    merged: dict[str,float]={}
    for label,value in raw.items():
        p=max(0.0,min(1.0,float(value)))
        if p<=0:
            continue
        key=normalize_instrument_label(label) if normalize_instruments else label.strip().lower()
        if normalize_instruments and key is None:
            key=f"open:{label.strip().lower().replace(' ','_')}"
        if not key:
            continue
        merged[key]=max(merged.get(key,0.0),p)
    total=sum(merged.values())
    if total>max_mass and total>0:
        scale=max_mass/total
        merged={k:v*scale for k,v in merged.items()}
    return {k:round(v,6) for k,v in sorted(merged.items())}


@dataclass
class LearnedInstrumentRoleAdapter:
    backend: LearnedInstrumentBackend

    def detect(
        self,
        samples,
        *,
        sample_rate: int,
        frame: AcousticDescriptorFrame,
    ) -> DetectorEvidence:
        instruments,roles,conf=self.backend.predict(samples,sample_rate=sample_rate)
        clean_i=_clean_distribution(instruments,normalize_instruments=True)
        clean_r=_clean_distribution(roles,normalize_instruments=False)
        clean_c={k:max(0.0,min(1.0,float(v))) for k,v in conf.items() if k}
        clean_c.setdefault("instrument",max(clean_i.values(),default=0.0))
        clean_c.setdefault("role",max(clean_r.values(),default=0.0))
        clean_c.setdefault("pitch",max(0.0,min(1.0,frame.pitch_confidence)))
        clean_c.setdefault(
            "event",
            max(clean_c["pitch"],min(1.0,max(0.0,frame.onset_strength))),
        )
        return DetectorEvidence(
            instrument_probabilities=clean_i,
            role_probabilities=clean_r,
            confidence_fields=clean_c,
            pitch_hz=frame.pitch_hz,
            onset=frame.onset,
            onset_strength=frame.onset_strength,
            rms=frame.rms,
        )


@dataclass
class HybridInstrumentRoleDetector:
    """Use learned output when available, otherwise preserve conservative baseline.

    Learned and baseline predictions are not naively averaged. The learned backend
    owns named-instrument identity when it produces a non-empty distribution;
    baseline remains a fallback and acoustic cross-check.
    """

    learned: LearnedInstrumentRoleAdapter | None = None
    baseline: BaselineInstrumentRoleDetector = BaselineInstrumentRoleDetector()

    def detect(self,samples,*,sample_rate:int,frame:AcousticDescriptorFrame)->DetectorEvidence:
        base=self.baseline.detect(frame)
        if self.learned is None:
            return base
        learned=self.learned.detect(samples,sample_rate=sample_rate,frame=frame)
        if not learned.instrument_probabilities and not learned.role_probabilities:
            return base
        confidence=dict(learned.confidence_fields)
        confidence["baseline_crosscheck"]=max(
            base.instrument_probabilities.values(),default=0.0
        )
        return DetectorEvidence(
            instrument_probabilities=learned.instrument_probabilities or base.instrument_probabilities,
            role_probabilities=learned.role_probabilities or base.role_probabilities,
            confidence_fields=confidence,
            pitch_hz=learned.pitch_hz,
            onset=learned.onset,
            onset_strength=learned.onset_strength,
            rms=learned.rms,
        )
