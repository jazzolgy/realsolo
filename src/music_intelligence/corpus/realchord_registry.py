"""Register RealChord 1350 as a Shared Core symbolic corpus."""
from __future__ import annotations

from .registry import (
    CorpusAccess,
    CorpusItem,
    CorpusKind,
    CorpusRegistry,
    CorpusUse,
    RightsProfile,
)

REALCHORD_1350_DATASET_ID="symbolic.realchord.1350"
REALCHORD_1350_SOURCE_FILENAME="Jazz 1350.html"
REALCHORD_1350_EXPECTED_COUNT=1350


def realchord_1350_corpus_item() -> CorpusItem:
    item=CorpusItem(
        item_id=REALCHORD_1350_DATASET_ID,
        kind=CorpusKind.MUSICAL_INTELLIGENCE,
        media_type="text/html",
        title="RealChord / Jazz 1350",
        artist_or_source="project symbolic corpus",
        local_relpath="symbolic/realchord/Jazz 1350.html",
        access=CorpusAccess.PROJECT_PRIVATE,
        uses=frozenset({
            CorpusUse.RESEARCH,
            CorpusUse.REFERENCE,
            CorpusUse.EVALUATION,
        }),
        tags=frozenset({
            "jazz","standard","symbolic","chord_chart","form",
            "shared_core","realchord","canonical_coordinate",
        }),
        instruments=frozenset({
            "piano","bass","drums","sax","soloist","transcribe","ensemble",
        }),
        rights=RightsProfile(
            source=REALCHORD_1350_SOURCE_FILENAME,
            research_permission=True,
            notes="Project-provided Shared symbolic reference corpus.",
        ),
        provenance=("user_project_source","Jazz 1350.html"),
        notes=(
            "Use as Expected Harmony / form reference. Never overwrite "
            "Observed or Inferred Harmony from an actual performance."
        ),
    )
    item.validate()
    return item


def register_realchord_1350(registry: CorpusRegistry) -> None:
    registry.add(realchord_1350_corpus_item())
