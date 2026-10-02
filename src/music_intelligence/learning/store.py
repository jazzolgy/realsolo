"""Shared deduplicating learning store."""
from __future__ import annotations
from dataclasses import dataclass,field
from .representation import LearningArtifact,LearningDomain

@dataclass
class LearningStore:
    _artifacts:dict[str,LearningArtifact]=field(default_factory=dict)
    def add(self,artifact:LearningArtifact)->bool:
        artifact.validate()
        if artifact.artifact_id in self._artifacts:return False
        self._artifacts[artifact.artifact_id]=artifact;return True
    def add_many(self,artifacts:tuple[LearningArtifact,...])->int:
        return sum(1 for x in artifacts if self.add(x))
    def all(self)->tuple[LearningArtifact,...]:
        return tuple(self._artifacts.values())
    def by_domain(self,domain:LearningDomain)->tuple[LearningArtifact,...]:
        return tuple(x for x in self._artifacts.values() if x.domain is domain)
    def __len__(self)->int:return len(self._artifacts)
