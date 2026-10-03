"""Fuse a source separator with a learned instrument classifier."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from .source_separation import SourceSeparationBackend
from .learned_instrument_adapter import LearnedInstrumentBackend


def _fuse(rows, max_mass=.97):
    totals={}
    weight_total=0.0
    for probs,weight in rows:
        w=max(0.0,float(weight))
        if w<=0:
            continue
        weight_total+=w
        for key,value in probs.items():
            totals[key]=totals.get(key,0.0)+w*max(0.0,float(value))
    if weight_total<=0:
        return {}
    avg={k:v/weight_total for k,v in totals.items()}
    total=sum(avg.values())
    if total>max_mass:
        scale=max_mass/total
        avg={k:v*scale for k,v in avg.items()}
    return {k:round(v,6) for k,v in sorted(avg.items())}


@dataclass
class StemAwareInstrumentBackend:
    separator: SourceSeparationBackend
    classifier: LearnedInstrumentBackend

    def predict(self,samples,*,sample_rate:int):
        stems=self.separator.separate(samples,sample_rate=sample_rate)
        if not stems:
            return self.classifier.predict(samples,sample_rate=sample_rate)

        instrument_rows=[]
        role_rows=[]
        confidence_rows=[]
        for stem in stems:
            stem.validate()
            instruments,roles,confidence=self.classifier.predict(
                stem.samples,
                sample_rate=stem.sample_rate,
            )
            weight=max(.05,stem.confidence)
            instrument_rows.append((instruments,weight))
            role_rows.append((roles,weight))
            confidence_rows.append((confidence,weight))

        instruments=_fuse(instrument_rows)
        roles=_fuse(role_rows)
        confidence=_fuse(confidence_rows,max_mass=1.0)
        confidence["source_separation"]=min(
            1.0,
            sum(x.confidence for x in stems)/len(stems),
        )
        confidence["stem_count_norm"]=min(1.0,len(stems)/8.0)
        return instruments,roles,confidence
