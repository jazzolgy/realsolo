"""Beat/phrase/register-aware posterior correction for research audio."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from music_intelligence.audio_evidence import ContextCorrection, DetectorEvidence
from .models import BeatState, PhraseState


def _renorm(values: Mapping[str,float],max_mass:float=.97)->dict[str,float]:
    positive={k:max(0.0,float(v)) for k,v in values.items() if float(v)>0}
    total=sum(positive.values())
    if total<=0:
        return {}
    scale=min(1.0,max_mass/total)
    return {k:round(v*scale,6) for k,v in sorted(positive.items())}


@dataclass(frozen=True)
class MusicalContextFrame:
    beat: BeatState
    phrase: PhraseState
    pitch_hz: float | None
    onset: bool


@dataclass
class MusicalContextCorrector:
    """Bounded contextual update layered after temporal continuity.

    This corrector only reweights labels that already exist. It cannot conjure a
    trumpet, saxophone, vocal, etc. from an unresolved raw detector.
    """

    max_relative_boost: float=.18

    def correct(
        self,
        raw: DetectorEvidence,
        prior: ContextCorrection,
        context: MusicalContextFrame,
    ) -> ContextCorrection:
        raw.validate(); prior.validate()
        instruments=dict(prior.instrument_probabilities)
        roles=dict(prior.role_probabilities)
        reasons=list(prior.reasons)

        pitch=context.pitch_hz
        if pitch is not None and pitch < 260:
            for key in ("acoustic_bass","electric_bass"):
                if key in instruments:
                    instruments[key]*=1.0+self.max_relative_boost*.7
            if "bass_line" in roles:
                roles["bass_line"]*=1.0+self.max_relative_boost
            reasons.append("low_register_supports_bass_role")

        beat=context.beat
        if beat.confidence >= .45 and context.onset and beat.phase is not None:
            near_pulse=min(beat.phase,1.0-beat.phase) <= .14
            if near_pulse:
                if "timekeeping" in roles:
                    roles["timekeeping"]*=1.0+self.max_relative_boost*.7
                if "bass_line" in roles:
                    roles["bass_line"]*=1.0+self.max_relative_boost*.45
                reasons.append("beat_grid_pulse_alignment")

        phrase=context.phrase
        if phrase.active and phrase.attack_count >= 3:
            if "melody_or_solo" in roles:
                roles["melody_or_solo"]*=1.0+self.max_relative_boost*.55
            reasons.append("active_phrase_continuity")
        if phrase.phrase_end:
            if "comping_or_support" in roles:
                roles["comping_or_support"]*=1.0+self.max_relative_boost*.35
            reasons.append("phrase_boundary_context")

        instruments=_renorm(instruments)
        roles=_renorm(roles)
        confidence=dict(prior.confidence_fields)
        raw_top=max(raw.role_probabilities.values(),default=0.0)
        post_top=max(roles.values(),default=0.0)
        confidence["musical_context_correction_magnitude"]=min(
            1.0,abs(post_top-raw_top)
        )
        confidence["beat_context"]=max(0.0,min(1.0,beat.confidence))
        confidence["phrase_context"]=min(1.0,phrase.attack_count/8.0) if phrase.active else 0.0

        return ContextCorrection(
            instrument_probabilities=instruments,
            role_probabilities=roles,
            confidence_fields=confidence,
            reasons=tuple(dict.fromkeys(reasons)),
        )
