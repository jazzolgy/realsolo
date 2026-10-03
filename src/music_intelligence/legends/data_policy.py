"""Shared storage and runtime boundary for all Legend Intelligence.

Exact source material may be musically useful without belonging in the public
repository.  This module defines one project-wide rule for every legend:

PRIVATE_RAW
    source audio, exact note-by-note transcription, exact score-derived phrase

PRIVATE_DERIVED
    normalized/transposed phrase, literal vocabulary, similarity fingerprints

PUBLIC_RUNTIME_SAFE
    abstract vocabulary, motif identity, tendencies, priors, non-reconstructive
    statistics and provenance

The public code may define provider interfaces for private stores.  The data
itself remains outside the public repository.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Protocol

from .interfaces import VocabularyMemoryItem, VocabularyQuery


class LegendDataLayer(str, Enum):
    PRIVATE_RAW = "private_raw"
    PRIVATE_DERIVED = "private_derived"
    PUBLIC_RUNTIME_SAFE = "public_runtime_safe"


class LegendMaterialKind(str, Enum):
    SOURCE_AUDIO = "source_audio"
    EXACT_TRANSCRIPTION = "exact_transcription"
    EXACT_SCORE_PHRASE = "exact_score_phrase"
    NORMALIZED_PHRASE = "normalized_phrase"
    LITERAL_VOCABULARY = "literal_vocabulary"
    SIMILARITY_FINGERPRINT = "similarity_fingerprint"
    ABSTRACT_VOCABULARY = "abstract_vocabulary"
    MOTIF_IDENTITY = "motif_identity"
    STYLE_TENDENCY = "style_tendency"
    POLICY_PRIOR = "policy_prior"
    NON_RECONSTRUCTIVE_STATISTICS = "non_reconstructive_statistics"
    PROVENANCE_MANIFEST = "provenance_manifest"


_DEFAULT_LAYER: dict[LegendMaterialKind, LegendDataLayer] = {
    LegendMaterialKind.SOURCE_AUDIO: LegendDataLayer.PRIVATE_RAW,
    LegendMaterialKind.EXACT_TRANSCRIPTION: LegendDataLayer.PRIVATE_RAW,
    LegendMaterialKind.EXACT_SCORE_PHRASE: LegendDataLayer.PRIVATE_RAW,
    LegendMaterialKind.NORMALIZED_PHRASE: LegendDataLayer.PRIVATE_DERIVED,
    LegendMaterialKind.LITERAL_VOCABULARY: LegendDataLayer.PRIVATE_DERIVED,
    LegendMaterialKind.SIMILARITY_FINGERPRINT: LegendDataLayer.PRIVATE_DERIVED,
    LegendMaterialKind.ABSTRACT_VOCABULARY: LegendDataLayer.PUBLIC_RUNTIME_SAFE,
    LegendMaterialKind.MOTIF_IDENTITY: LegendDataLayer.PUBLIC_RUNTIME_SAFE,
    LegendMaterialKind.STYLE_TENDENCY: LegendDataLayer.PUBLIC_RUNTIME_SAFE,
    LegendMaterialKind.POLICY_PRIOR: LegendDataLayer.PUBLIC_RUNTIME_SAFE,
    LegendMaterialKind.NON_RECONSTRUCTIVE_STATISTICS: LegendDataLayer.PUBLIC_RUNTIME_SAFE,
    LegendMaterialKind.PROVENANCE_MANIFEST: LegendDataLayer.PUBLIC_RUNTIME_SAFE,
}


def default_legend_data_layer(kind: LegendMaterialKind) -> LegendDataLayer:
    return _DEFAULT_LAYER[kind]


@dataclass(frozen=True)
class PrivateLegendStoreDescriptor:
    """Public-safe descriptor for a private exact-material store.

    It describes connectivity/capability only.  It must not contain an exact
    phrase, local filesystem secret, credential, or source payload.
    """

    store_id: str
    legend_id: str
    supports_literal_vocabulary: bool = False
    supports_exact_transcription: bool = False
    supports_similarity_fingerprints: bool = False
    provenance: tuple[str, ...] = ()

    def validate(self) -> None:
        if not self.store_id or not self.legend_id:
            raise ValueError("store_id and legend_id are required")


class PrivateLegendVocabularyProvider(Protocol):
    """Runtime interface for an externally configured private vocabulary store.

    Implementations may live in a private service, encrypted object store,
    private database or local research environment.  Public code depends only
    on this contract.
    """

    @property
    def descriptor(self) -> PrivateLegendStoreDescriptor:
        ...

    def query(self, request: VocabularyQuery) -> tuple[VocabularyMemoryItem, ...]:
        ...


def may_publish_material(kind: LegendMaterialKind) -> bool:
    """Return whether the default project rule permits public-repo material."""
    return default_legend_data_layer(kind) is LegendDataLayer.PUBLIC_RUNTIME_SAFE
