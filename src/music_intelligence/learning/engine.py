"""Shared domain learners, priors and runtime feedback."""
from __future__ import annotations
from dataclasses import dataclass,field
from typing import Mapping

from .pipeline import LearningConversion
from .representation import LearningArtifact,LearningDomain
from .store import LearningStore


@dataclass(frozen=True)
class LearningFeedback:
    domain:LearningDomain
    feature:str
    reward:float
    def validate(self)->None:
        if not self.feature:raise ValueError("feature is required")
        if not 0.0<=self.reward<=1.0:raise ValueError("reward must be within 0..1")


@dataclass
class DomainLearningState:
    numeric_means:dict[str,float]=field(default_factory=dict)
    numeric_counts:dict[str,int]=field(default_factory=dict)
    categorical_counts:dict[str,dict[str,int]]=field(default_factory=dict)
    feedback_bias:dict[str,float]=field(default_factory=dict)
    observations:int=0

    def observe(self,a:LearningArtifact)->None:
        a.validate();self.observations+=1
        for k,v in a.features.items():
            if isinstance(v,(int,float)):
                n=self.numeric_counts.get(k,0)+1
                old=self.numeric_means.get(k,0.0)
                self.numeric_means[k]=old+(float(v)-old)/n
                self.numeric_counts[k]=n
            elif isinstance(v,str) and v:
                bucket=self.categorical_counts.setdefault(k,{})
                bucket[v]=bucket.get(v,0)+1

    def feedback(self,f:LearningFeedback,lr:float=.15)->None:
        f.validate()
        target=2.0*(f.reward-.5)
        old=self.feedback_bias.get(f.feature,0.0)
        self.feedback_bias[f.feature]=max(-1.0,min(1.0,old+lr*(target-old)))


@dataclass(frozen=True)
class LearningPriorView:
    domain:LearningDomain
    numeric_features:Mapping[str,float]
    categorical_counts:Mapping[str,Mapping[str,int]]
    feedback_bias:Mapping[str,float]
    observations:int

    def feature_bias(self,feature:str,*,center:float=0.5,scale:float=1.0)->float:
        learned=self.numeric_features.get(feature)
        value=0.0 if learned is None else (learned-center)*scale
        return value+self.feedback_bias.get(feature,0.0)

    def category_weight(self,feature:str,value:str)->float:
        bucket=self.categorical_counts.get(feature,{})
        total=sum(bucket.values())
        return bucket.get(value,0)/total if total else 0.0


@dataclass
class SharedLearningEngine:
    store:LearningStore=field(default_factory=LearningStore)
    states:dict[LearningDomain,DomainLearningState]=field(default_factory=dict)

    def _state(self,domain:LearningDomain)->DomainLearningState:
        return self.states.setdefault(domain,DomainLearningState())

    def ingest_artifacts(self,artifacts:tuple[LearningArtifact,...],*,learn:bool=True)->int:
        added=0
        for a in artifacts:
            if self.store.add(a):
                added+=1
                if learn:self._state(a.domain).observe(a)
        return added

    def ingest_conversion(self,conversion:LearningConversion)->int:
        # Keep all derived artifacts visible in the store, but only rights-gated
        # training artifacts update learned priors.
        training_ids={a.artifact_id for a in conversion.training_artifacts}
        added=0
        for a in conversion.derived_artifacts:
            if self.store.add(a):
                added+=1
                if a.artifact_id in training_ids:self._state(a.domain).observe(a)
        return added

    def record_feedback(self,feedback:LearningFeedback)->None:
        self._state(feedback.domain).feedback(feedback)

    def prior(self,domain:LearningDomain)->LearningPriorView:
        s=self._state(domain)
        return LearningPriorView(
            domain,
            dict(s.numeric_means),
            {k:dict(v) for k,v in s.categorical_counts.items()},
            dict(s.feedback_bias),
            s.observations,
        )
