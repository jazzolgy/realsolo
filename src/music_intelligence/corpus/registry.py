"""v1.45 shared corpus registry.

The registry gives all workstreams one source of truth for research/reference
materials without duplicating the same corpus separately into each player
branch.

Important: this module stores metadata and stable identifiers. Copyrighted raw
audio should normally live outside the public repository under a private/local
corpus root. Registry items point to relative locations or external references
and carry explicit rights/use metadata.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Iterable, Mapping
import os


class CorpusKind(str, Enum):
    AUDIO_FOUNDATION = "audio_foundation"
    MUSICAL_INTELLIGENCE = "musical_intelligence"
    AESTHETIC = "aesthetic"
    SYNTHETIC = "synthetic"
    EXPERT_ANNOTATION = "expert_annotation"


class CorpusUse(str, Enum):
    TRAINING = "training"
    RESEARCH = "research"
    REFERENCE = "reference"
    EVALUATION = "evaluation"
    REDISTRIBUTION = "redistribution"


class CorpusAccess(str, Enum):
    LOCAL_PRIVATE = "local_private"
    PROJECT_PRIVATE = "project_private"
    PUBLIC_REPO = "public_repo"
    EXTERNAL_REFERENCE = "external_reference"


@dataclass(frozen=True)
class RightsProfile:
    source: str | None = None
    rights_holder: str | None = None
    license: str | None = None
    training_permission: bool | None = None
    research_permission: bool | None = None
    commercial_permission: bool | None = None
    redistribution_permission: bool | None = None
    notes: str = ""

    def permits(self, use: CorpusUse) -> bool | None:
        if use is CorpusUse.TRAINING:
            return self.training_permission
        if use is CorpusUse.RESEARCH:
            return self.research_permission
        if use is CorpusUse.REDISTRIBUTION:
            return self.redistribution_permission
        # REFERENCE / EVALUATION can be context-specific; unknown unless
        # explicitly represented in notes/policy by a higher layer.
        return None


@dataclass(frozen=True)
class CorpusItem:
    item_id: str
    kind: CorpusKind
    media_type: str
    title: str
    artist_or_source: str | None = None
    local_relpath: str | None = None
    external_ref: str | None = None
    access: CorpusAccess = CorpusAccess.LOCAL_PRIVATE
    uses: frozenset[CorpusUse] = frozenset()
    tags: frozenset[str] = frozenset()
    instruments: frozenset[str] = frozenset()
    legend_ids: frozenset[str] = frozenset()
    derived_from: tuple[str, ...] = ()
    rights: RightsProfile = RightsProfile()
    provenance: tuple[str, ...] = ()
    notes: str = ""

    def validate(self) -> None:
        if not self.item_id:
            raise ValueError("item_id is required")
        if not self.media_type:
            raise ValueError("media_type is required")
        if not self.title:
            raise ValueError("title is required")
        if self.access in {
            CorpusAccess.LOCAL_PRIVATE,
            CorpusAccess.PROJECT_PRIVATE,
            CorpusAccess.PUBLIC_REPO,
        } and not self.local_relpath:
            raise ValueError("local_relpath required for local/project/repo items")
        if self.access is CorpusAccess.EXTERNAL_REFERENCE and not self.external_ref:
            raise ValueError("external_ref required for external-reference items")


class CorpusRegistry:
    """In-memory registry with stable IDs and branch-neutral querying."""

    def __init__(self, items: Iterable[CorpusItem] = ()):
        self._items: dict[str, CorpusItem] = {}
        for item in items:
            self.add(item)

    def add(self, item: CorpusItem) -> None:
        item.validate()
        if item.item_id in self._items:
            raise ValueError(f"duplicate corpus item_id: {item.item_id}")
        self._items[item.item_id] = item

    def get(self, item_id: str) -> CorpusItem:
        return self._items[item_id]

    def all(self) -> tuple[CorpusItem, ...]:
        return tuple(self._items.values())

    def query(
        self,
        *,
        kind: CorpusKind | None = None,
        use: CorpusUse | None = None,
        tag: str | None = None,
        instrument: str | None = None,
        legend_id: str | None = None,
        media_type: str | None = None,
        require_explicit_permission: bool = False,
    ) -> tuple[CorpusItem, ...]:
        out: list[CorpusItem] = []
        for item in self._items.values():
            if kind is not None and item.kind is not kind:
                continue
            if use is not None and use not in item.uses:
                continue
            if tag is not None and tag not in item.tags:
                continue
            if instrument is not None and instrument not in item.instruments:
                continue
            if legend_id is not None and legend_id not in item.legend_ids:
                continue
            if media_type is not None and item.media_type != media_type:
                continue
            if require_explicit_permission and use is not None:
                if item.rights.permits(use) is not True:
                    continue
            out.append(item)
        return tuple(out)

    def dependency_closure(self, item_id: str) -> tuple[CorpusItem, ...]:
        """Return item plus its derived-from ancestors, once each."""
        seen: set[str] = set()
        ordered: list[CorpusItem] = []

        def visit(current_id: str) -> None:
            if current_id in seen:
                return
            seen.add(current_id)
            item = self.get(current_id)
            for parent in item.derived_from:
                visit(parent)
            ordered.append(item)

        visit(item_id)
        return tuple(ordered)

    def resolve_path(self, item_id: str, *, root: str | Path | None = None) -> Path:
        item = self.get(item_id)
        if not item.local_relpath:
            raise ValueError("item has no local path")
        base = Path(root) if root is not None else corpus_root_from_env()
        return (base / item.local_relpath).expanduser().resolve()

    def manifest(self) -> Mapping[str, CorpusItem]:
        return dict(self._items)


def corpus_root_from_env() -> Path:
    value = os.environ.get("REALSOLO_CORPUS_ROOT")
    if not value:
        raise RuntimeError(
            "REALSOLO_CORPUS_ROOT is not set; point it to the private shared corpus directory"
        )
    return Path(value).expanduser().resolve()
