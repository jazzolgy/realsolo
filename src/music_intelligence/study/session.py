"""First runnable RealSolo study session.

The MVP studies compact audio windows and persists JSONL evidence. Learning is
admitted only when a canonical MusicalScoreCoordinate is available. A manual
form clock is an explicit bootstrap alignment tool, not an autonomous form
detector and not a second canonical coordinate.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
import json
from pathlib import Path
from typing import Protocol

from music_intelligence.learning.engine import SharedLearningEngine
from music_intelligence.learning.representation import LearningArtifact,LearningDomain
from music_intelligence.learning.score_alignment import MusicalScoreCoordinate,PerformancePhase

from .audio import AudioWindowFeatures,stream_audio_windows


class CoordinateClock(Protocol):
    def coordinate_at(self,source_time_s:float)->MusicalScoreCoordinate|None: ...


@dataclass(frozen=True)
class SectionRange:
    section:str
    start_bar:int
    end_bar:int

    def validate(self)->None:
        if not self.section:
            raise ValueError("section is required")
        if self.start_bar<1 or self.end_bar<self.start_bar:
            raise ValueError("invalid section bar range")


@dataclass(frozen=True)
class ManualFormClock:
    """Explicit seconds -> score-position bootstrap for immediate research.

    This exists so study can start before automatic beat/downbeat/form alignment
    is production-ready. Persisted output is always MusicalScoreCoordinate.
    """
    song_id:str
    bpm:float
    meter_numerator:int=4
    meter_denominator:int=4
    form_length_bars:int|None=None
    form_start_s:float=0.0
    realchord_id:str=""
    score_source_id:str=""
    sections:tuple[SectionRange,...]=()
    performance_phase:PerformancePhase=PerformancePhase.UNKNOWN

    def validate(self)->None:
        if not self.song_id:
            raise ValueError("song_id is required")
        if self.bpm<=0:
            raise ValueError("bpm must be positive")
        if self.meter_numerator<=0 or self.meter_denominator<=0:
            raise ValueError("meter must be positive")
        if self.form_length_bars is not None and self.form_length_bars<1:
            raise ValueError("form_length_bars must be positive")
        if self.form_start_s<0:
            raise ValueError("form_start_s may not be negative")
        for section in self.sections:
            section.validate()

    @property
    def quarter_notes_per_bar(self)->float:
        return self.meter_numerator*(4.0/self.meter_denominator)

    def coordinate_at(self,source_time_s:float)->MusicalScoreCoordinate|None:
        self.validate()
        if source_time_s<self.form_start_s:
            return None
        elapsed=source_time_s-self.form_start_s
        qn=elapsed*(self.bpm/60.0)
        qpb=self.quarter_notes_per_bar
        global_bar=int(qn//qpb)
        within_qn=qn-global_bar*qpb
        beat=1.0+within_qn*(self.meter_denominator/4.0)
        if self.form_length_bars is not None:
            chorus=global_bar//self.form_length_bars
            form_bar=global_bar%self.form_length_bars+1
            bar=form_bar
        else:
            chorus=None
            form_bar=None
            bar=global_bar+1
        section=""
        for item in self.sections:
            probe=form_bar if form_bar is not None else bar
            if item.start_bar<=probe<=item.end_bar:
                section=item.section
                break
        score_source=self.score_source_id
        if self.realchord_id and not score_source:
            score_source=f"realchord:{self.realchord_id}"
        out=MusicalScoreCoordinate(
            song_id=self.song_id,
            score_source_id=score_source,
            realchord_id=self.realchord_id,
            section=section,
            bar=bar,
            beat=beat,
            form_length_bars=self.form_length_bars,
            form_bar=form_bar,
            chorus_index=chorus,
            performance_phase=self.performance_phase,
            arrangement_segment="core_form",
            within_core_form=(self.form_length_bars is not None),
            confidence=.65,
            provenance=("manual_form_clock","study_mvp"),
        )
        out.validate()
        return out


@dataclass(frozen=True)
class StudySessionSummary:
    source_id:str
    windows:int
    aligned_windows:int
    stored_artifacts:int
    evidence_observations:int
    output_path:str


def _artifact_id(source_id:str,domain:LearningDomain,start_s:float)->str:
    raw=f"{source_id}|{domain.value}|{start_s:.3f}|study.audio_window.v1"
    return "study:"+sha256(raw.encode()).hexdigest()[:20]


def artifacts_for_window(
    source_id:str,
    window:AudioWindowFeatures,
    coordinate:MusicalScoreCoordinate|None,
)->tuple[LearningArtifact,...]:
    common={
        "source_time_start_s":round(window.start_s,6),
        "source_time_end_s":round(window.end_s,6),
        "activity_proxy":round(window.activity,6),
    }
    rhythm=LearningArtifact(
        artifact_id=_artifact_id(source_id,LearningDomain.RHYTHM_GROOVE,window.start_s),
        source_id=source_id,
        domain=LearningDomain.RHYTHM_GROOVE,
        feature_schema="study.audio_window.rhythm.v1",
        features={
            **common,
            "onset_rate_hz":round(window.onset_rate_hz,6),
            "zero_crossing_rate":round(window.zero_crossing_rate,6),
            "spectral_centroid_hz":(
                None if window.spectral_centroid_hz is None
                else round(window.spectral_centroid_hz,3)
            ),
        },
        confidence=.45,
        provenance=("local_audio_study","observation_only","non_reconstructive"),
        musical_position=coordinate,
    )
    expression=LearningArtifact(
        artifact_id=_artifact_id(source_id,LearningDomain.EXPRESSION,window.start_s),
        source_id=source_id,
        domain=LearningDomain.EXPRESSION,
        feature_schema="study.audio_window.expression.v1",
        features={
            **common,
            "rms":round(window.rms,8),
            "peak":round(window.peak,8),
        },
        confidence=.55,
        provenance=("local_audio_study","observation_only","non_reconstructive"),
        musical_position=coordinate,
    )
    rhythm.validate();expression.validate()
    return rhythm,expression


def _coordinate_json(c:MusicalScoreCoordinate|None):
    if c is None:
        return None
    return {
        "song_id":c.song_id,
        "score_source_id":c.score_source_id,
        "realchord_id":c.realchord_id,
        "section":c.section,
        "bar":c.bar,
        "beat":c.beat,
        "form_length_bars":c.form_length_bars,
        "form_bar":c.form_bar,
        "chorus_index":c.chorus_index,
        "performance_phase":c.performance_phase.value,
        "arrangement_segment":c.arrangement_segment,
        "within_core_form":c.within_core_form,
        "confidence":c.confidence,
        "provenance":c.provenance,
    }


@dataclass
class StudySession:
    source_id:str
    output_path:Path
    form_clock:CoordinateClock|None=None
    engine:SharedLearningEngine|None=None

    def run(
        self,
        audio_path:str|Path,
        *,
        window_s:float=2.0,
        hop_s:float=1.0,
        start_s:float=0.0,
        max_seconds:float|None=None,
    )->StudySessionSummary:
        if not self.source_id:
            raise ValueError("source_id is required")
        self.output_path=Path(self.output_path).expanduser().resolve()
        self.output_path.parent.mkdir(parents=True,exist_ok=True)
        engine=self.engine or SharedLearningEngine()
        windows=aligned=stored=0
        with self.output_path.open("w",encoding="utf-8") as fh:
            for window in stream_audio_windows(
                audio_path,window_s=window_s,hop_s=hop_s,start_s=start_s,max_seconds=max_seconds
            ):
                coordinate=(
                    self.form_clock.coordinate_at(window.start_s)
                    if self.form_clock is not None else None
                )
                artifacts=artifacts_for_window(self.source_id,window,coordinate)
                stored+=engine.ingest_artifacts(
                    artifacts,learn=False,study_as_evidence=True
                )
                row={
                    "schema":"realsolo.study.window.v1",
                    "source_id":self.source_id,
                    "audio":asdict(window),
                    "musical_position":_coordinate_json(coordinate),
                    "learning_status":(
                        "aligned_evidence" if coordinate is not None
                        else "navigation_only"
                    ),
                    "artifact_ids":[a.artifact_id for a in artifacts],
                }
                fh.write(json.dumps(row,ensure_ascii=False,separators=(",",":"))+"\n")
                windows+=1
                aligned+=int(coordinate is not None)
        evidence_observations=sum(
            state.observations for state in engine.evidence_states.values()
        )
        return StudySessionSummary(
            source_id=self.source_id,
            windows=windows,
            aligned_windows=aligned,
            stored_artifacts=stored,
            evidence_observations=evidence_observations,
            output_path=str(self.output_path),
        )


def parse_section_map(value:str)->tuple[SectionRange,...]:
    if not value.strip():
        return ()
    out=[]
    for token in value.split(","):
        name,sep,span=token.strip().partition(":")
        if not sep or "-" not in span:
            raise ValueError("section map must look like A1:1-8,B:17-24")
        lo,hi=span.split("-",1)
        item=SectionRange(name.strip(),int(lo),int(hi))
        item.validate()
        out.append(item)
    return tuple(out)
