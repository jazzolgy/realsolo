"""Genre/idiom learning above individual-player style.

Genre priors describe broader musical grammars (bebop, funk, salsa, bossa,
modal, etc.). Labels may come from trusted metadata; the learned features remain
structural and can later support clustering/classification without labels.
"""
from __future__ import annotations
from hashlib import sha256
from statistics import mean

from .representation import LearningArtifact, LearningDomain, StructuralPerformanceData
from .canonical_position import canonicalize_structural_positions, position_feature_map


def build_genre_artifact(
    data: StructuralPerformanceData,
    artifacts: tuple[LearningArtifact,...],
) -> LearningArtifact | None:
    data=canonicalize_structural_positions(data)
    if not artifacts:
        return None

    genre_label=data.metadata.get("genre_label","")
    rhythm_label=data.metadata.get("rhythm_label","")

    comp=[a for a in artifacts if a.domain is LearningDomain.COMPING]
    tension=[a for a in artifacts if a.domain is LearningDomain.FORM_TENSION]
    interaction=[a for a in artifacts if a.domain is LearningDomain.ENSEMBLE_INTERACTION]
    solo=[a for a in artifacts if a.domain is LearningDomain.SOLO_PHRASE]

    def avg(items,key,default=0.0):
        vals=[float(a.features[key]) for a in items if isinstance(a.features.get(key),(int,float))]
        return mean(vals) if vals else default

    features={
        "genre_label":genre_label,
        "rhythm_label":rhythm_label,
        "meter":data.meter,
        "tempo_bpm":round(data.tempo_bpm,3) if data.tempo_bpm is not None else 0.0,
        "comping_density_mean":round(avg(comp,"density"),4),
        "solo_phrase_span_mean":round(avg(solo,"span_beats"),4),
        "interaction_gap_mean":round(avg(interaction,"response_gap_beats"),4),
        "tension_mean":round(avg(tension,"tension_proxy"),4),
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
        artifact_id=f"learn:genre:{data.source_id}:{digest}",
        source_id=data.source_id,
        domain=LearningDomain.GENRE,
        feature_schema="genre.structural_profile.v1",
        features=features,
        source_event_ids=tuple(e.event_id for e in data.events),
        confidence=mean(a.confidence for a in artifacts),
        provenance=("shared_learning:genre","cross_domain_idiom_profile","metric_form_learning_address"),
    )
