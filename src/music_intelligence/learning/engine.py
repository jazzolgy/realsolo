"""Shared domain learners, priors and runtime feedback."""
from __future__ import annotations
from dataclasses import dataclass,field
from typing import Mapping

from .admission import LearningAdmissionDecision
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
    """Keep rights-gated training priors separate from research evidence priors.

    states remains the model-training/adaptation view. evidence_states may
    learn from derived research artifacts even when training permission is
    absent. This lets RealSolo study private/reference recordings without
    silently treating them as training-authorized material.
    """
    store:LearningStore=field(default_factory=LearningStore)
    states:dict[LearningDomain,DomainLearningState]=field(default_factory=dict)
    evidence_states:dict[LearningDomain,DomainLearningState]=field(default_factory=dict)
    admission_log:dict[str,LearningAdmissionDecision]=field(default_factory=dict)

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

    def ingest_artifacts_with_admission(
        self,
        artifacts:tuple[LearningArtifact,...],
        decisions:Mapping[str,LearningAdmissionDecision],
    )->int:
        """Store all artifacts while gating automatic prior updates by evidence quality.

        Missing decisions are rejected so callers cannot silently bypass the
        evidence-quality gate once this admission path is chosen.
        """
        added=0
        for a in artifacts:
            decision=decisions.get(a.artifact_id)
            if decision is None:
                raise ValueError(f"missing admission decision for {a.artifact_id}")
            decision.validate()
            if decision.artifact_id != a.artifact_id:
                raise ValueError("admission decision belongs to another artifact")
            if self.store.add(a):
                added+=1
                self.admission_log[a.artifact_id]=decision
                if decision.admit_to_evidence_prior:
                    self._evidence_state(a.domain).observe(a)
                if decision.admit_to_training_prior:
                    self._state(a.domain).observe(a)
        return added

    def review_required_artifacts(self)->tuple[LearningArtifact,...]:
        """Return stored artifacts held out of priors pending review."""
        ids={
            artifact_id for artifact_id,decision in self.admission_log.items()
            if decision.requires_review
        }
        return tuple(a for a in self.store.all() if a.artifact_id in ids)

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
