"""Shared-corpus discovery for score/form knowledge.

This module intentionally separates *source discovery* from form inference.
RealChord, lead-sheet/chart corpora, manual form annotations and beat/downbeat
maps can all be registered as corpus items. Shared Form Intelligence consumes
structured form knowledge produced by an adapter; corpus metadata alone is never
treated as performed-audio truth.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from .registry import CorpusItem, CorpusRegistry, CorpusUse


FORM_SOURCE_TAGS=frozenset({
    "realchord",
    "chord_chart",
    "form_annotation",
    "form_map",
    "measure_map",
    "meter_map",
    "downbeat_map",
    "score",
    "lead_sheet",
})


@dataclass(frozen=True)
class FormSourceCandidate:
    item_id: str
    title: str
    media_type: str
    tags: frozenset[str]
    derived_from: tuple[str,...]
    local_relpath: str | None
    external_ref: str | None
    provenance: tuple[str,...]

    @property
    def is_realchord(self) -> bool:
        return "realchord" in self.tags


def discover_form_sources(
    registry: CorpusRegistry,
    *,
    title: str | None = None,
    item_ids: Iterable[str] = (),
    require_research_use: bool = True,
) -> tuple[FormSourceCandidate,...]:
    """Return corpus items that may provide expected form/score knowledge.

    This does not parse or endorse a file format. A concrete adapter must turn a
    candidate into FormMap / score-alignment evidence.
    """
    wanted_ids=set(item_ids)
    title_norm=(title or "").strip().casefold()
    out=[]
    for item in registry.all():
        if require_research_use and CorpusUse.RESEARCH not in item.uses:
            continue
        if wanted_ids and item.item_id not in wanted_ids and not set(item.derived_from)&wanted_ids:
            continue
        if title_norm and title_norm not in item.title.casefold():
            continue
        if not (set(item.tags)&set(FORM_SOURCE_TAGS)):
            continue
        out.append(FormSourceCandidate(
            item_id=item.item_id,
            title=item.title,
            media_type=item.media_type,
            tags=item.tags,
            derived_from=item.derived_from,
            local_relpath=item.local_relpath,
            external_ref=item.external_ref,
            provenance=item.provenance,
        ))
    # Prefer explicit form/downbeat/RealChord evidence over generic chart sources.
    def rank(x:FormSourceCandidate):
        tags=x.tags
        score=0
        score+=8 if "realchord" in tags else 0
        score+=7 if "form_map" in tags or "form_annotation" in tags else 0
        score+=5 if "measure_map" in tags or "downbeat_map" in tags else 0
        score+=3 if "chord_chart" in tags else 0
        score+=1 if "score" in tags or "lead_sheet" in tags else 0
        return (-score,x.item_id)
    return tuple(sorted(out,key=rank))
