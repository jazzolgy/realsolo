"""Persistent jazz-instrument adaptation head over YAMNet embeddings.

This head is deliberately a *domain adaptation* layer, not a replacement for
ground-truth supervision. It can learn stable timbral prototypes from very
high-confidence YAMNet observations and later smooth ambiguous windows for the
same jazz-instrument space. Explicitly labelled exemplars can be admitted later
through the same observe() API.

Only embeddings/prototypes are persisted, never source audio.
"""
from __future__ import annotations

from dataclasses import dataclass, field
import json
from math import exp
from pathlib import Path
from typing import Mapping


@dataclass
class InstrumentPrototype:
    label: str
    count: int
    centroid: object


@dataclass
class JazzInstrumentEmbeddingHead:
    path: Path | None = None
    min_examples: int = 4
    bootstrap_confidence: float = .92
    bootstrap_margin: float = .18
    temperature: float = .12
    _prototypes: dict[str,InstrumentPrototype] = field(default_factory=dict,init=False,repr=False)

    def __post_init__(self) -> None:
        if self.path is not None:
            self._load()

    def _np(self):
        try:
            import numpy as np
        except ImportError as exc:
            raise RuntimeError('Jazz embedding head requires numpy') from exc
        return np

    def _unit(self,embedding):
        np=self._np()
        x=np.asarray(embedding,dtype=np.float32).reshape(-1)
        norm=float(np.linalg.norm(x))
        if x.size==0 or norm<=1e-9:
            return None
        return x/norm

    def observe(
        self,
        label: str,
        embedding,
        *,
        confidence: float,
        margin: float,
        explicit_label: bool=False,
    ) -> bool:
        """Admit one prototype example.

        Automatic admission is intentionally strict. Human/curated labels may
        set explicit_label=True and bypass the YAMNet confidence/margin gate.
        """
        if not label:
            return False
        if not explicit_label and (
            confidence < self.bootstrap_confidence or margin < self.bootstrap_margin
        ):
            return False
        x=self._unit(embedding)
        if x is None:
            return False
        old=self._prototypes.get(label)
        if old is None:
            proto=InstrumentPrototype(label,1,x)
        else:
            np=self._np()
            centroid=(old.centroid*old.count+x)/(old.count+1)
            norm=float(np.linalg.norm(centroid))
            if norm>1e-9:
                centroid=centroid/norm
            proto=InstrumentPrototype(label,old.count+1,centroid.astype(np.float32))
        self._prototypes[label]=proto
        self._save()
        return True

    def predict(self,embedding) -> Mapping[str,float]:
        x=self._unit(embedding)
        if x is None:
            return {}
        eligible=[p for p in self._prototypes.values() if p.count>=self.min_examples]
        if len(eligible)<2:
            return {}
        sims={p.label:float(x @ p.centroid) for p in eligible}
        m=max(sims.values())
        exps={k:exp((v-m)/max(1e-6,self.temperature)) for k,v in sims.items()}
        total=sum(exps.values())
        if total<=0:
            return {}
        return {k:v/total for k,v in sorted(exps.items())}

    def counts(self) -> Mapping[str,int]:
        return {k:v.count for k,v in sorted(self._prototypes.items())}

    def _save(self) -> None:
        if self.path is None:
            return
        self.path.parent.mkdir(parents=True,exist_ok=True)
        payload={
            "version":1,
            "prototypes":{
                k:{"count":v.count,"centroid":[float(x) for x in v.centroid]}
                for k,v in sorted(self._prototypes.items())
            },
        }
        tmp=self.path.with_suffix(self.path.suffix+".tmp")
        tmp.write_text(json.dumps(payload,separators=(",",":")),encoding="utf-8")
        tmp.replace(self.path)

    def _load(self) -> None:
        if self.path is None or not self.path.exists():
            return
        np=self._np()
        raw=json.loads(self.path.read_text(encoding="utf-8"))
        for label,item in raw.get("prototypes",{}).items():
            centroid=self._unit(np.asarray(item.get("centroid",[]),dtype=np.float32))
            count=int(item.get("count",0))
            if centroid is not None and count>0:
                self._prototypes[str(label)]=InstrumentPrototype(str(label),count,centroid)
