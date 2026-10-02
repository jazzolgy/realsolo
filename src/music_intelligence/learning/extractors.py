"""Default structural extractors for shared musical learning.

These are intentionally interpretable first-pass extractors. Learned models may
replace/augment them later without changing LearningArtifact contracts.
"""
from __future__ import annotations

from hashlib import sha256
from math import isclose
from statistics import mean
from typing import Protocol

from .representation import (
    LearningArtifact,
    LearningDomain,
    StructuralPerformanceData,
    StructuralPerformanceEvent,
)


class LearningExtractor(Protocol):
    domain: LearningDomain
    def extract(self, data: StructuralPerformanceData) -> tuple[LearningArtifact, ...]:
        ...


def _id(source: str, domain: LearningDomain, payload: str) -> str:
    digest=sha256(payload.encode()).hexdigest()[:16]
    return f"learn:{domain.value}:{source}:{digest}"


def _pitched(events):
    return tuple(e for e in events if e.pitch_midi is not None)


def _intervals(events):
    p=_pitched(events)
    return tuple(int(round(b.pitch_midi-a.pitch_midi)) for a,b in zip(p,p[1:]))


def _normalized_ioi(events):
    if len(events)<2:
        return ()
    iois=tuple(b.onset_beats-a.onset_beats for a,b in zip(events,events[1:]))
    base=next((x for x in iois if x>1e-6),1.0)
    return tuple(round(max(.125,x/base),3) for x in iois)


class MotifExtractor:
    domain=LearningDomain.MOTIF
    def extract(self,data):
        out=[]
        events=tuple(sorted(data.events,key=lambda e:e.onset_beats))
        for i in range(len(events)-2):
            w=events[i:i+4]
            if len(w)<3:
                continue
            if w[-1].onset_beats+w[-1].duration_beats-w[0].onset_beats>4.0:
                continue
            ints=_intervals(w)
            rhythm=_normalized_ioi(w)
            payload=f"{ints}|{rhythm}"
            out.append(LearningArtifact(
                _id(data.source_id,self.domain,payload),data.source_id,self.domain,
                "motif.relative.v1",
                {"interval_schema":ints,"rhythm_schema":rhythm,
                 "event_count":len(w),"source_instrument":w[0].instrument},
                tuple(e.event_id for e in w),
                min(e.confidence for e in w),
                ("shared_learning:motif",),
            ))
        return tuple(out)


class SoloPhraseExtractor:
    domain=LearningDomain.SOLO_PHRASE
    def extract(self,data):
        groups={}
        for e in data.events:
            if e.role=="solo" or "solo" in e.tags or e.phrase_id:
                key=e.phrase_id or f"window:{int(e.onset_beats//4)}"
                groups.setdefault(key,[]).append(e)
        out=[]
        for key,items in groups.items():
            items=tuple(sorted(items,key=lambda e:e.onset_beats))
            if len(items)<2: continue
            ints=_intervals(items); rhythm=_normalized_ioi(items)
            span=items[-1].onset_beats+items[-1].duration_beats-items[0].onset_beats
            payload=f"{key}|{ints}|{rhythm}"
            out.append(LearningArtifact(
                _id(data.source_id,self.domain,payload),data.source_id,self.domain,
                "solo_phrase.relative.v1",
                {"interval_schema":ints,"rhythm_schema":rhythm,"span_beats":round(span,3),
                 "entry_phase":round(items[0].onset_beats%4,3),
                 "mean_accent":round(mean(e.accent for e in items),3)},
                tuple(e.event_id for e in items),
                min(e.confidence for e in items),
                ("shared_learning:solo_phrase",),
            ))
        return tuple(out)


class VocabularyExtractor:
    domain=LearningDomain.VOCABULARY
    def extract(self,data):
        motifs=MotifExtractor().extract(data)
        counts={}
        for m in motifs:
            sig=(tuple(m.features["interval_schema"]),tuple(m.features["rhythm_schema"]))
            counts[sig]=counts.get(sig,0)+1
        out=[]
        for m in motifs:
            sig=(tuple(m.features["interval_schema"]),tuple(m.features["rhythm_schema"]))
            if counts[sig]<2: continue
            features=dict(m.features)
            features["recurrence_count"]=counts[sig]
            out.append(LearningArtifact(
                _id(data.source_id,self.domain,str(sig)),data.source_id,self.domain,
                "vocabulary.recurring_cell.v1",features,m.source_event_ids,m.confidence,
                ("shared_learning:vocabulary","recurrence_detected"),
            ))
        return tuple(out)


class CompingExtractor:
    domain=LearningDomain.COMPING
    def extract(self,data):
        comp=tuple(e for e in data.events if e.role=="comping" or "comping" in e.tags)
        if not comp: return ()
        windows={}
        for e in comp: windows.setdefault(int(e.onset_beats//4),[]).append(e)
        out=[]
        for bar,items in windows.items():
            items=tuple(sorted(items,key=lambda e:e.onset_beats))
            placements=tuple(round(e.onset_beats%4,3) for e in items)
            durations=tuple(round(e.duration_beats,3) for e in items)
            payload=f"{bar}|{placements}|{durations}"
            out.append(LearningArtifact(
                _id(data.source_id,self.domain,payload),data.source_id,self.domain,
                "comping.gesture_distribution.v1",
                {"metric_placements":placements,"durations":durations,
                 "density":round(len(items)/4,3),
                 "mean_dynamic":round(mean(e.dynamic if e.dynamic is not None else .5 for e in items),3)},
                tuple(e.event_id for e in items),min(e.confidence for e in items),
                ("shared_learning:comping",),
            ))
        return tuple(out)


class HarmonyVoiceLeadingExtractor:
    domain=LearningDomain.HARMONY_VOICE_LEADING
    def extract(self,data):
        pitched=_pitched(tuple(sorted(data.events,key=lambda e:e.onset_beats)))
        out=[]
        for a,b in zip(pitched,pitched[1:]):
            if not (a.harmony_label or b.harmony_label): continue
            motion=int(round(b.pitch_midi-a.pitch_midi))
            payload=f"{a.harmony_label}>{b.harmony_label}|{motion}"
            out.append(LearningArtifact(
                _id(data.source_id,self.domain,payload),data.source_id,self.domain,
                "harmony.voice_leading_transition.v1",
                {"from_harmony":a.harmony_label,"to_harmony":b.harmony_label,
                 "voice_motion":motion,"common_context":a.harmony_label==b.harmony_label},
                (a.event_id,b.event_id),min(a.confidence,b.confidence),
                ("shared_learning:harmony_voice_leading",),
            ))
        return tuple(out)


class RhythmMicrotimingExtractor:
    domain=LearningDomain.RHYTHM_MICROTIMING
    def extract(self,data):
        if not data.events: return ()
        events=tuple(sorted(data.events,key=lambda e:e.onset_beats))
        offsets=tuple(round(e.timing_offset_beats,4) for e in events)
        phases=tuple(round(e.onset_beats%1,3) for e in events)
        payload=f"{phases}|{offsets}"
        return (LearningArtifact(
            _id(data.source_id,self.domain,payload),data.source_id,self.domain,
            "rhythm.microtiming_profile.v1",
            {"metric_phases":phases,"timing_offsets":offsets,
             "rhythm_schema":_normalized_ioi(events)},
            tuple(e.event_id for e in events),min(e.confidence for e in events),
            ("shared_learning:rhythm_microtiming",),
        ),)


class EnsembleInteractionExtractor:
    domain=LearningDomain.ENSEMBLE_INTERACTION
    def extract(self,data):
        events=tuple(sorted(data.events,key=lambda e:e.onset_beats))
        out=[]
        for a,b in zip(events,events[1:]):
            if not a.instrument or not b.instrument or a.instrument==b.instrument: continue
            gap=b.onset_beats-(a.onset_beats+a.duration_beats)
            if gap>2.0: continue
            payload=f"{a.instrument}>{b.instrument}|{round(gap,3)}|{a.ensemble_role}>{b.ensemble_role}"
            out.append(LearningArtifact(
                _id(data.source_id,self.domain,payload),data.source_id,self.domain,
                "ensemble.interaction_transition.v1",
                {"source_instrument":a.instrument,"response_instrument":b.instrument,
                 "response_gap_beats":round(gap,3),
                 "source_role":a.ensemble_role,"response_role":b.ensemble_role},
                (a.event_id,b.event_id),min(a.confidence,b.confidence),
                ("shared_learning:ensemble_interaction",),
            ))
        return tuple(out)


class ExpressionExtractor:
    domain=LearningDomain.EXPRESSION
    def extract(self,data):
        if not data.events: return ()
        events=tuple(sorted(data.events,key=lambda e:e.onset_beats))
        payload="|".join(e.event_id for e in events)
        dyn=tuple(round(e.dynamic if e.dynamic is not None else .5,3) for e in events)
        accent=tuple(round(e.accent,3) for e in events)
        return (LearningArtifact(
            _id(data.source_id,self.domain,payload),data.source_id,self.domain,
            "expression.trajectory.v1",
            {"dynamic_trajectory":dyn,"accent_trajectory":accent,
             "articulations":tuple(e.articulation for e in events)},
            tuple(e.event_id for e in events),min(e.confidence for e in events),
            ("shared_learning:expression",),
        ),)


class FormTensionExtractor:
    domain=LearningDomain.FORM_TENSION
    def extract(self,data):
        events=tuple(sorted(data.events,key=lambda e:e.onset_beats))
        if not events: return ()
        windows={}
        for e in events: windows.setdefault(int(e.onset_beats//4),[]).append(e)
        out=[]
        prev_density=None
        for bar,items in sorted(windows.items()):
            density=len(items)/4.0
            mean_accent=mean(e.accent for e in items)
            pitch_span=0.0
            p=[e.pitch_midi for e in items if e.pitch_midi is not None]
            if p: pitch_span=max(p)-min(p)
            tension=min(1.0,.35*density+.30*mean_accent+.35*min(1.0,pitch_span/12.0))
            direction="stable" if prev_density is None or isclose(density,prev_density,abs_tol=.12) else ("build" if density>prev_density else "release")
            prev_density=density
            payload=f"{bar}|{round(tension,3)}|{direction}"
            out.append(LearningArtifact(
                _id(data.source_id,self.domain,payload),data.source_id,self.domain,
                "form.tension_window.v1",
                {"window":bar,"density":round(density,3),"tension_proxy":round(tension,3),
                 "trajectory":direction,"form_label":data.form_label},
                tuple(e.event_id for e in items),min(e.confidence for e in items),
                ("shared_learning:form_tension",),
            ))
        return tuple(out)


DEFAULT_EXTRACTORS: tuple[LearningExtractor,...]=(
    MotifExtractor(),
    SoloPhraseExtractor(),
    VocabularyExtractor(),
    CompingExtractor(),
    HarmonyVoiceLeadingExtractor(),
    RhythmMicrotimingExtractor(),
    EnsembleInteractionExtractor(),
    ExpressionExtractor(),
    FormTensionExtractor(),
)


def extract_learning_artifacts(
    data: StructuralPerformanceData,
    extractors: tuple[LearningExtractor,...]=DEFAULT_EXTRACTORS,
) -> tuple[LearningArtifact,...]:
    data.validate()
    out=[]
    for extractor in extractors:
        out.extend(extractor.extract(data))
    for artifact in out: artifact.validate()
    return tuple(out)
