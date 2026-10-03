"""Rhythm/groove learning for idioms such as salsa, funk, swing and bossa.

The representation learns cyclic placement, accent, syncopation and interlock
rather than merely storing a genre label.
"""
from __future__ import annotations
from hashlib import sha256
from statistics import mean

from .representation import LearningArtifact, LearningDomain, StructuralPerformanceData
from .canonical_position import canonicalize_structural_positions, position_feature_map
from .groove_grammar import best_matching_grammars


def _slot(position: float, cycle_beats: float, subdivisions_per_beat: int) -> int:
    total=max(1,int(round(cycle_beats*subdivisions_per_beat)))
    phase=position%cycle_beats
    return int(round(phase*subdivisions_per_beat))%total


def build_groove_artifact(
    data: StructuralPerformanceData,
    *,
    subdivisions_per_beat: int = 4,
) -> LearningArtifact | None:
    data=canonicalize_structural_positions(data)
    if not data.events:
        return None
    if subdivisions_per_beat <= 0:
        raise ValueError("subdivisions_per_beat must be positive")

    cycle_raw=data.metadata.get("groove_cycle_beats","")
    try:
        cycle_beats=float(cycle_raw) if cycle_raw else 4.0
    except ValueError:
        cycle_beats=4.0
    if cycle_beats <= 0:
        cycle_beats=4.0

    total_slots=max(1,int(round(cycle_beats*subdivisions_per_beat)))
    onset_counts=[0]*total_slots
    accent_sums=[0.0]*total_slots
    instrument_counts={}

    offbeat=0
    backbeat_accents=[]
    downbeat_accents=[]
    ordered=tuple(sorted(data.events,key=lambda e:e.onset_beats))

    for e in ordered:
        s=_slot(e.onset_beats,cycle_beats,subdivisions_per_beat)
        onset_counts[s]+=1
        accent_sums[s]+=e.accent
        if e.instrument:
            instrument_counts[e.instrument]=instrument_counts.get(e.instrument,0)+1
        beat_phase=e.onset_beats%1.0
        if abs(beat_phase)>.08:
            offbeat+=1
        p=e.metric_form_position
        bar_phase=p.beat_in_measure if p is not None and p.resolved_metric else None
        if bar_phase is not None and p.meter_numerator==4 and p.meter_denominator==4:
            if abs(bar_phase-1.0)<=.13 or abs(bar_phase-3.0)<=.13:
                backbeat_accents.append(e.accent)
            if abs(bar_phase)<=.13:
                downbeat_accents.append(e.accent)

    accent_profile=tuple(
        round(accent_sums[i]/onset_counts[i],3) if onset_counts[i] else 0.0
        for i in range(total_slots)
    )
    density_profile=tuple(round(c/len(ordered),4) for c in onset_counts)

    # Cross-instrument lock: nearest onset separation for successive events from
    # different instruments, clipped to one beat.
    lock_gaps=[]
    for a,b in zip(ordered,ordered[1:]):
        if a.instrument and b.instrument and a.instrument!=b.instrument:
            lock_gaps.append(min(1.0,abs(b.onset_beats-a.onset_beats)))

    matches=best_matching_grammars(
        density_profile,
        cycle_beats=cycle_beats,
        subdivisions_per_beat=subdivisions_per_beat,
        limit=3,
    )
    features={
        "genre_label":data.metadata.get("genre_label",""),
        "rhythm_label":data.metadata.get("rhythm_label",""),
        "cycle_beats":cycle_beats,
        "subdivisions_per_beat":subdivisions_per_beat,
        "onset_density_profile":density_profile,
        "accent_profile":accent_profile,
        "syncopation_rate":round(offbeat/len(ordered),4),
        "backbeat_strength":round(mean(backbeat_accents),4) if backbeat_accents else 0.0,
        "downbeat_strength":round(mean(downbeat_accents),4) if downbeat_accents else 0.0,
        "cross_instrument_lock_gap_mean":round(mean(lock_gaps),4) if lock_gaps else 0.0,
        "instrument_event_counts":tuple(sorted(instrument_counts.items())),
        "meter":data.meter,
        "tempo_bpm":round(data.tempo_bpm,3) if data.tempo_bpm is not None else 0.0,
        "groove_matches":tuple((g.grammar_id,round(score,4)) for g,score in matches),
        "best_groove_grammar":matches[0][0].grammar_id if matches else "",
        "best_groove_score":round(matches[0][1],4) if matches else 0.0,
        "metric_form_context":{
            "resolved_metric":all(e.metric_form_position is not None and e.metric_form_position.resolved_metric for e in ordered),
            "resolved_form":all(e.metric_form_position is not None and e.metric_form_position.resolved_form for e in ordered),
            "form_id":data.form_map.form_id if data.form_map is not None else (data.form_label or None),
            "sections":tuple(dict.fromkeys(
                e.metric_form_position.section_id
                for e in ordered
                if e.metric_form_position is not None and e.metric_form_position.section_id
            )),
            "start":position_feature_map(ordered[0]),
            "end":position_feature_map(ordered[-1]),
        },
    }
    payload=str(features)
    digest=sha256(payload.encode()).hexdigest()[:16]
    return LearningArtifact(
        artifact_id=f"learn:groove:{data.source_id}:{digest}",
        source_id=data.source_id,
        domain=LearningDomain.RHYTHM_GROOVE,
        feature_schema="rhythm.groove_cycle.v1",
        features=features,
        source_event_ids=tuple(e.event_id for e in ordered),
        confidence=mean(e.confidence for e in ordered),
        provenance=("shared_learning:rhythm_groove","cyclic_structure","metric_form_learning_address"),
    )
