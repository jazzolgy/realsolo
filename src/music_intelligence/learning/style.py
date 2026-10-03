"""Cross-domain performer/style learning.

Style describes source-specific tendencies across musical domains. It does not
own exact notes or literal phrases.
"""
from __future__ import annotations
from hashlib import sha256
from statistics import mean

from .representation import LearningArtifact, LearningDomain, StructuralPerformanceData
from .canonical_position import canonicalize_structural_positions, position_feature_map


def _numeric(artifacts, domain, key):
    values=[]
    for a in artifacts:
        if a.domain is domain:
            v=a.features.get(key)
            if isinstance(v,(int,float)):
                values.append(float(v))
    return values


def _mean(values, default=0.0):
    return mean(values) if values else default


def build_style_artifact(
    data: StructuralPerformanceData,
    artifacts: tuple[LearningArtifact,...],
) -> LearningArtifact | None:
    data=canonicalize_structural_positions(data)
    if not artifacts:
        return None
    features={
        "solo_phrase_span_mean":round(_mean(_numeric(artifacts,LearningDomain.SOLO_PHRASE,"span_beats")),4),
        "solo_accent_mean":round(_mean(_numeric(artifacts,LearningDomain.SOLO_PHRASE,"mean_accent"),.5),4),
        "comping_density_mean":round(_mean(_numeric(artifacts,LearningDomain.COMPING,"density")),4),
        "comping_dynamic_mean":round(_mean(_numeric(artifacts,LearningDomain.COMPING,"mean_dynamic"),.5),4),
        "interaction_response_gap_mean":round(_mean(_numeric(artifacts,LearningDomain.ENSEMBLE_INTERACTION,"response_gap_beats")),4),
        "form_tension_mean":round(_mean(_numeric(artifacts,LearningDomain.FORM_TENSION,"tension_proxy")),4),
        "artist_or_legend":data.metadata.get("artist_or_legend",""),
        "style_label":data.metadata.get("style_label",""),
        "form_label":data.form_label,
        "metric_form_context":{
            "resolved_metric":all(e.metric_form_position is not None and e.metric_form_position.resolved_metric for e in data.events),
            "resolved_form":all(e.metric_form_position is not None and e.metric_form_position.resolved_form for e in data.events),
            "form_id":data.form_map.form_id if data.form_map is not None else (data.form_label or None),
            "sections":tuple(dict.fromkeys(
                e.metric_form_position.section_id
                for e in data.events
                if e.metric_form_position is not None and e.metric_form_position.section_id
            )),
            "start":position_feature_map(data.events[0]) if data.events else None,
            "end":position_feature_map(data.events[-1]) if data.events else None,
        },
    }
    payload="|".join(f"{k}={features[k]}" for k in sorted(features))
    digest=sha256(payload.encode()).hexdigest()[:16]
    return LearningArtifact(
        artifact_id=f"learn:style:{data.source_id}:{digest}",
        source_id=data.source_id,
        domain=LearningDomain.STYLE,
        feature_schema="style.cross_domain_profile.v1",
        features=features,
        source_event_ids=tuple(e.event_id for e in data.events),
        confidence=mean(a.confidence for a in artifacts),
        provenance=("shared_learning:style","cross_domain_aggregation","metric_form_learning_address"),
    )
