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
    form_context_observations:dict[str,int]=field(default_factory=dict)
    form_context_numeric_means:dict[str,dict[str,float]]=field(default_factory=dict)
    form_context_numeric_counts:dict[str,dict[str,int]]=field(default_factory=dict)

    @staticmethod
    def _form_context_key(a:LearningArtifact)->str|None:
        ctx=a.features.get("metric_form_context")
        if not isinstance(ctx,Mapping) or not ctx.get("resolved_metric"):
            return None
        start=ctx.get("start")
        if not isinstance(start,Mapping):
            return None
        form_id=str(ctx.get("form_id") or "*")
        section=str(start.get("section_id") or "*")
        measure=start.get("measure_index")
        beat=start.get("beat_in_measure")
        iteration=start.get("form_iteration")
        beat_text="*" if beat is None else f"{float(beat):.3f}"
        return f"form={form_id}|section={section}|iteration={iteration}|measure={measure}|beat={beat_text}"

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

        context_key=self._form_context_key(a)
        if context_key is not None:
            self.form_context_observations[context_key]=self.form_context_observations.get(context_key,0)+1
            means=self.form_context_numeric_means.setdefault(context_key,{})
            counts=self.form_context_numeric_counts.setdefault(context_key,{})
            for k,v in a.features.items():
                if isinstance(v,(int,float)) and not isinstance(v,bool):
                    n=counts.get(k,0)+1
                    old=means.get(k,0.0)
                    means[k]=old+(float(v)-old)/n
                    counts[k]=n

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
    form_context_observations:Mapping[str,int]=field(default_factory=dict)
    form_context_numeric_features:Mapping[str,Mapping[str,float]]=field(default_factory=dict)

    def feature_bias(self,feature:str,*,center:float=0.5,scale:float=1.0)->float:
        learned=self.numeric_features.get(feature)
        value=0.0 if learned is None else (learned-center)*scale
        return value+self.feedback_bias.get(feature,0.0)

    def category_weight(self,feature:str,value:str)->float:
        bucket=self.categorical_counts.get(feature,{})
        total=sum(bucket.values())
        return bucket.get(value,0)/total if total else 0.0

    def contextual_numeric(self,context_key:str,feature:str)->float|None:
        return self.form_context_numeric_features.get(context_key,{}).get(feature)

    def context_observations(self,context_key:str)->int:
        return int(self.form_context_observations.get(context_key,0))


@dataclass
class SharedLearningEngine:
    """Keep rights-gated training priors separate from research evidence priors.

    states remains the model-training/adaptation view. evidence_states may
    learn from derived research artifacts even when training permission is
    absent. This lets RealSolo study private/reference recordings without
    silently treating them as training-authorized material.
    """
    store:LearningStore=field(default_factory=LearningStore)
    states:dict[LearningDomain,DomainLearningState]=field(default_factory=dict)
    evidence_states:dict[LearningDomain,DomainLearningState]=field(default_factory=dict)

    def _state(self,domain:LearningDomain)->DomainLearningState:
        return self.states.setdefault(domain,DomainLearningState())

    def _evidence_state(self,domain:LearningDomain)->DomainLearningState:
        return self.evidence_states.setdefault(domain,DomainLearningState())

    def ingest_artifacts(
        self,
        artifacts:tuple[LearningArtifact,...],
        *,
        learn:bool=True,
        study_as_evidence:bool=True,
    )->int:
        added=0
        for a in artifacts:
            if self.store.add(a):
                added+=1
                if study_as_evidence:self._evidence_state(a.domain).observe(a)
                if learn:self._state(a.domain).observe(a)
        return added

    def ingest_conversion(self,conversion:LearningConversion)->int:
        # Every derived artifact may inform the research/evidence view.
        # Only rights-gated training artifacts update trainable priors.
        training_ids={a.artifact_id for a in conversion.training_artifacts}
        added=0
        for a in conversion.derived_artifacts:
            if self.store.add(a):
                added+=1
                self._evidence_state(a.domain).observe(a)
                if a.artifact_id in training_ids:self._state(a.domain).observe(a)
        return added

    def record_feedback(self,feedback:LearningFeedback)->None:
        self._state(feedback.domain).feedback(feedback)

    @staticmethod
    def _view(domain:LearningDomain,s:DomainLearningState)->LearningPriorView:
        return LearningPriorView(
            domain,
            dict(s.numeric_means),
            {k:dict(v) for k,v in s.categorical_counts.items()},
            dict(s.feedback_bias),
            s.observations,
            dict(s.form_context_observations),
            {k:dict(v) for k,v in s.form_context_numeric_means.items()},
        )

    def prior(self,domain:LearningDomain)->LearningPriorView:
        """Rights-gated trainable/adaptive prior."""
        return self._view(domain,self._state(domain))

    def evidence_prior(self,domain:LearningDomain)->LearningPriorView:
        """Research prior from all admitted derived evidence.

        Runtime code must still apply legend/provenance promotion rules before
        converting this view into a musical policy.
        """
        return self._view(domain,self._evidence_state(domain))
