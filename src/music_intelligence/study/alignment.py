"""Adapters from existing research alignment manifests to canonical coordinates.

The manifest remains evidence. Output coordinates are always Shared Core's
MusicalScoreCoordinate.
"""
from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Mapping,Sequence

from music_intelligence.learning.score_alignment import MusicalScoreCoordinate,PerformancePhase


def _phase_from_role(role:str)->PerformancePhase:
    value=(role or "").casefold()
    if "head_out" in value or "out_head" in value:
        return PerformancePhase.HEAD_OUT
    if "head" in value:
        return PerformancePhase.HEAD
    if "piano_solo" in value or "solo" in value:
        return PerformancePhase.SOLO
    if "bass" in value and "foreground" in value:
        return PerformancePhase.BASS_FOREGROUND
    if "drum" in value and "foreground" in value:
        return PerformancePhase.DRUM_FOREGROUND
    if "intro" in value:
        return PerformancePhase.INTRO
    if "interlude" in value:
        return PerformancePhase.INTERLUDE
    if "coda" in value:
        return PerformancePhase.CODA
    if "outro" in value:
        return PerformancePhase.OUTRO
    if "vamp" in value:
        return PerformancePhase.VAMP
    if "tag" in value:
        return PerformancePhase.TAG
    return PerformancePhase.UNKNOWN


@dataclass(frozen=True)
class AlignedFormSegment:
    segment_id:str
    role:str
    start_s:float
    end_s:float
    start_bar:int
    end_bar:int
    section:str=""
    confidence:float=.5

    def validate(self)->None:
        if not self.segment_id:
            raise ValueError("segment_id is required")
        if self.start_s<0 or self.end_s<=self.start_s:
            raise ValueError("segment time must satisfy 0 <= start < end")
        if self.start_bar<1 or self.end_bar<self.start_bar:
            raise ValueError("invalid segment bar range")
        if not 0.0<=self.confidence<=1.0:
            raise ValueError("confidence must be within 0..1")


@dataclass(frozen=True)
class ResearchAlignmentClock:
    song_id:str
    form_length_bars:int
    segments:tuple[AlignedFormSegment,...]
    meter_numerator:int=4
    meter_denominator:int=4
    source_offset_s:float=0.0
    realchord_id:str=""
    score_source_id:str=""
    provenance:tuple[str,...]=()

    def validate(self)->None:
        if not self.song_id:
            raise ValueError("song_id is required")
        if self.form_length_bars<1:
            raise ValueError("form_length_bars must be positive")
        if self.meter_numerator<=0 or self.meter_denominator<=0:
            raise ValueError("meter must be positive")
        if self.source_offset_s<0:
            raise ValueError("source_offset_s may not be negative")
        for segment in self.segments:
            segment.validate()

    @property
    def denominator_units_per_bar(self)->float:
        return float(self.meter_numerator)

    def coordinate_at(self,source_time_s:float)->MusicalScoreCoordinate|None:
        self.validate()
        relative=source_time_s-self.source_offset_s
        segment=next(
            (s for s in self.segments if s.start_s<=relative<s.end_s),
            None,
        )
        if segment is None:
            return None
        bars=segment.end_bar-segment.start_bar+1
        total_units=bars*self.denominator_units_per_bar
        frac=(relative-segment.start_s)/(segment.end_s-segment.start_s)
        units=min(total_units-1e-9,max(0.0,frac*total_units))
        local_bar=int(units//self.denominator_units_per_bar)
        beat_units=units-local_bar*self.denominator_units_per_bar
        form_bar=segment.start_bar+local_bar
        beat=1.0+beat_units

        score_source=self.score_source_id
        if self.realchord_id and not score_source:
            score_source=f"realchord:{self.realchord_id}"
        out=MusicalScoreCoordinate(
            song_id=self.song_id,
            score_source_id=score_source,
            realchord_id=self.realchord_id,
            section=segment.section,
            bar=form_bar,
            beat=beat,
            form_length_bars=self.form_length_bars,
            form_bar=form_bar,
            chorus_index=None,
            performance_phase=_phase_from_role(segment.role),
            arrangement_segment="core_form",
            within_core_form=True,
            confidence=segment.confidence,
            provenance=self.provenance+(
                f"alignment_segment:{segment.segment_id}",
                "research_alignment_manifest",
            ),
        )
        out.validate()
        return out


def _parse_bar_span(value:object)->tuple[int,int]:
    text=str(value or "").strip()
    if "-" in text:
        left,right=text.split("-",1)
        return int(left),int(right)
    if text:
        bar=int(text)
        return bar,bar
    raise ValueError("alignment section requires bars")


def alignment_clock_from_payload(
    payload:Mapping[str,object],
    *,
    song_id:str,
    source_offset_s:float=0.0,
    realchord_id:str="",
    score_source_id:str="",
)->ResearchAlignmentClock:
    form=payload.get("form",{})
    if not isinstance(form,Mapping):
        raise TypeError("form must be a mapping")
    form_bars=int(form.get("bars",0))
    section_names=tuple(str(x) for x in form.get("sections",()) if str(x))
    raw_segments=payload.get("sections",())
    if not isinstance(raw_segments,Sequence):
        raise TypeError("sections must be a sequence")

    segments=[]
    for raw in raw_segments:
        if not isinstance(raw,Mapping):
            continue
        start_bar,end_bar=_parse_bar_span(raw.get("bars"))
        time_s=raw.get("time_s")
        if not isinstance(time_s,Sequence) or len(time_s)!=2:
            raise ValueError("alignment section time_s must contain [start,end]")
        segment_id=str(raw.get("id",""))
        section=next(
            (name for name in section_names if segment_id==name or segment_id.endswith("_"+name)),
            "",
        )
        segments.append(AlignedFormSegment(
            segment_id=segment_id,
            role=str(raw.get("role","")),
            start_s=float(time_s[0]),
            end_s=float(time_s[1]),
            start_bar=start_bar,
            end_bar=end_bar,
            section=section,
            confidence=float(raw.get("confidence",.5)),
        ))
    clock=ResearchAlignmentClock(
        song_id=song_id,
        form_length_bars=form_bars,
        segments=tuple(segments),
        source_offset_s=source_offset_s,
        realchord_id=realchord_id,
        score_source_id=score_source_id,
        provenance=(
            str(payload.get("recording_id","")),
            str(payload.get("schema_version","")),
        ),
    )
    clock.validate()
    return clock


def load_alignment_clock(
    path:str|Path,
    *,
    song_id:str,
    source_offset_s:float=0.0,
    realchord_id:str="",
    score_source_id:str="",
)->ResearchAlignmentClock:
    payload=json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload,Mapping):
        raise TypeError("alignment JSON root must be an object")
    return alignment_clock_from_payload(
        payload,
        song_id=song_id,
        source_offset_s=source_offset_s,
        realchord_id=realchord_id,
        score_source_id=score_source_id,
    )
