"""Build runtime prior hierarchy only from rights-gated promoted learning state."""
from __future__ import annotations

from music_intelligence.learning.engine import SharedLearningEngine
from music_intelligence.learning.representation import LearningDomain
from music_intelligence.reasoning.hierarchical_priors import HierarchicalPriorSet


def hierarchical_priors_from_learning_engine(
    engine: SharedLearningEngine,
) -> HierarchicalPriorSet | None:
    """Project promoted trainable priors into the runtime hierarchy.

    This intentionally calls engine.prior(), never evidence_prior(). Research
    evidence therefore cannot enter audible policy until it has passed the
    project's admission/promotion process.
    """

    domain=engine.prior(LearningDomain.SOLO_PHRASE)
    genre=engine.prior(LearningDomain.GENRE)
    style=engine.prior(LearningDomain.STYLE)

    if not any(
        x.weighted_observations > 0 or x.observations > 0
        for x in (domain,genre,style)
    ):
        return None

    priors=HierarchicalPriorSet(
        domain_prior=domain if domain.observations else None,
        genre_prior=genre if genre.observations else None,
        style_prior=style if style.observations else None,
    )
    priors.validate()
    return priors
