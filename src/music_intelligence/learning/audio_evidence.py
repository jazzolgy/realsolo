"""Adapters for compact, public-safe audio evidence aggregates.

These artifacts intentionally contain non-reconstructive summary features. Exact
note hypotheses may stay in the private corpus and are not required at runtime.
"""
from __future__ import annotations

from hashlib import sha256
from typing import Mapping, Sequence

from .representation import LearningArtifact, LearningDomain


def _id(source_id: str, domain: LearningDomain, schema: str) -> str:
    digest=sha256(f"{source_id}|{domain.value}|{schema}".encode()).hexdigest()[:16]
    return f"learn:{domain.value}:{source_id}:{digest}"


def artifacts_from_audio_aggregate(payload: Mapping[str, object]) -> tuple[LearningArtifact, ...]:
    """Convert a Bill-Evans-style aggregate payload into research artifacts.

    The result is suitable for SharedLearningEngine.ingest_artifacts with
    learn=False, study_as_evidence=True. It must not be treated as explicit
    model-training permission.
    """
    sources=payload.get("sources",())
    out=[]
    for raw in sources if isinstance(sources,Sequence) else ():
        if not isinstance(raw,Mapping):
            continue
        source_id=str(raw.get("source_id",""))
        if not source_id:
            continue
        rhythm={
            "onset_rate_p10":float(raw.get("onset_rate_p10",0.0)),
            "onset_rate_p50":float(raw.get("onset_rate_p50",0.0)),
            "onset_rate_p90":float(raw.get("onset_rate_p90",0.0)),
        }
        expression={
            "rms_p10":float(raw.get("rms_p10",0.0)),
            "rms_p50":float(raw.get("rms_p50",0.0)),
            "rms_p90":float(raw.get("rms_p90",0.0)),
        }
        vocabulary={
            "pitch_class_entropy_norm":float(raw.get("pitch_class_entropy_norm",0.0)),
            "same_pitch_transition_fraction":float(raw.get("same_pitch_transition_fraction",0.0)),
            "step_motion_fraction":float(raw.get("step_motion_fraction",0.0)),
            "within_fifth_motion_fraction":float(raw.get("within_fifth_motion_fraction",0.0)),
            "octave_or_more_motion_fraction":float(raw.get("octave_or_more_motion_fraction",0.0)),
            "analysis_scope":"mixed_audio_note_hypothesis_aggregate",
        }
        for domain,schema,features in (
            (LearningDomain.RHYTHM_GROOVE,"audio_aggregate.rhythm.v1",rhythm),
            (LearningDomain.EXPRESSION,"audio_aggregate.expression.v1",expression),
            (LearningDomain.VOCABULARY,"audio_aggregate.vocabulary.v1",vocabulary),
        ):
            out.append(LearningArtifact(
                artifact_id=_id(source_id,domain,schema),
                source_id=source_id,
                domain=domain,
                feature_schema=schema,
                features=features,
                confidence=float(raw.get("confidence_mean",0.5)),
                provenance=(
                    "private_audio_analysis",
                    "mixed_audio",
                    "observation_only",
                    "non_reconstructive_aggregate",
                ),
            ))
    return tuple(out)
