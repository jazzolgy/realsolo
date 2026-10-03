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
    numeric_weights:dict[str,float]=field(default_factory=dict)
    categorical_counts:dict[str,dict[str,int]]=field(default_factory=dict)
    categorical_weights:dict[str,dict[str,float]]=field(default_factory=dict)
    feedback_bias:dict[str,float]=field(default_factory=dict)
    observations:int=0
    weighted_observations:float=0.0

    def observe(self,a:LearningArtifact)->None:
        """Backward-compatible full-weight observation."""
        self.observe_weighted(a,1.0)

    def observe_weighted(self,a:LearningArtifact,weight:float)->None:
        """Update priors without letting weak evidence count as a full observation."""
        a.validate()
        if not 0.0<weight<=1.0:
            raise ValueError("learning weight must be within (0,1]")
        self.observations+=1
        self.weighted_observations+=weight
        for k,v in a.features.items():
            if isinstance(v,(int,float)):
                old_weight=self.numeric_weights.get(k,0.0)
                new_weight=old_weight+weight
                old=self.numeric_means.get(k,0.0)
                self.numeric_means[k]=old+(float(v)-old)*(weight/new_weight)
                self.numeric_weights[k]=new_weight
                self.numeric_counts[k]=self.numeric_counts.get(k,0)+1
            elif isinstance(v,str) and v:
                bucket=self.categorical_counts.setdefault(k,{})
                bucket[v]=bucket.get(v,0)+1
                weighted_bucket=self.categorical_weights.setdefault(k,{})
                weighted_bucket[v]=weighted_bucket.get(v,0.0)+weight

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
    numeric_weights:Mapping[str,float]=field(default_factory=dict)
    categorical_weights:Mapping[str,Mapping[str,float]]=field(default_factory=dict)
    weighted_observations:float=0.0

    def feature_bias(self,feature:str,*,center:float=0.5,scale:float=1.0)->float:
        learned=self.numeric_features.get(feature)
        value=0.0 if learned is None else (learned-center)*scale
        return value+self.feedback_bias.get(feature,0.0)

    def category_weight(self,feature:str,value:str)->float:
        weighted=self.categorical_weights.get(feature,{})
        weighted_total=sum(weighted.values())
        if weighted_total:
            return weighted.get(value,0.0)/weighted_total
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
                    base_weight=1.0 if decision.evidence_weight is None else decision.evidence_weight
                    evidence_weight=base_weight*a.confidence
                    if evidence_weight>0:
                        self._evidence_state(a.domain).observe_weighted(a,evidence_weight)
                if decision.admit_to_training_prior:
                    base_weight=1.0 if decision.training_weight is None else decision.training_weight
                    training_weight=base_weight*a.confidence
                    if training_weight>0:
                        self._state(a.domain).observe_weighted(a,training_weight)
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
            domain=domain,
            numeric_features=dict(s.numeric_means),
            categorical_counts={k:dict(v) for k,v in s.categorical_counts.items()},
            feedback_bias=dict(s.feedback_bias),
            observations=s.observations,
            numeric_weights=dict(s.numeric_weights),
            categorical_weights={k:dict(v) for k,v in s.categorical_weights.items()},
            weighted_observations=s.weighted_observations,
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
