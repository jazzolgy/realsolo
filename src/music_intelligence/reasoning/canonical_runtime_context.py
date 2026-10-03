"""One canonical Shared-Core context consumed by realtime/player adapters.

This is the reconciliation boundary for the older #53-#56 runtime stack:
MusicalScoreCoordinate owns WHEN, RealChord supplies Expected Harmony,
music_intelligence.expression owns HOW, and Legend Vocabulary remains a
separate optional WHAT prior. This module schedules no future note sequence.
"""
from __future__ import annotations

from dataclasses import dataclass, replace

from music_intelligence.corpus.realchord import (
    ExpectedHarmonyReference,
    RealChordSong,
    expected_harmony_at,
)
from music_intelligence.expression import (
    ExpressiveContext,
    ExpressiveIntent,
    RelativeExpressionProfile,
    realize_expressive_intent,
)
from music_intelligence.learning.score_alignment import MusicalScoreCoordinate
from music_intelligence.legends.interfaces import (
    VocabularyMemoryItem,
    VocabularyQuery,
    VocabularyUseType,
)
from music_intelligence.vocabulary.usage_policy import choose_runtime_vocabulary_use
from .runtime_legend_resources import legend_runtime_resources


@dataclass(frozen=True)
class RuntimeVocabularyChoice:
    item: VocabularyMemoryItem
    use_type: VocabularyUseType


@dataclass(frozen=True)
class CanonicalRuntimeContext:
    position: MusicalScoreCoordinate
    expected_harmony: ExpectedHarmonyReference | None
    expressive_intent: ExpressiveIntent
    vocabulary: tuple[RuntimeVocabularyChoice,...] = ()

    def validate(self) -> None:
        self.position.validate()
        self.expressive_intent.validate()
        if self.expected_harmony is not None:
            self.expected_harmony.validate()
            if (
                self.position.realchord_id
                and self.expected_harmony.realchord_id != self.position.realchord_id
            ):
                raise ValueError("Expected Harmony does not match coordinate RealChord id")


def build_canonical_runtime_context(
    *,
    position: MusicalScoreCoordinate,
    expressive_context: ExpressiveContext,
    realchord_song: RealChordSong | None = None,
    expression_profile: RelativeExpressionProfile | None = None,
    legend_id: str | None = None,
    vocabulary_query: VocabularyQuery | None = None,
    vocabulary_opportunity_index: int = 0,
    vocabulary_limit: int = 4,
) -> CanonicalRuntimeContext:
    position.validate()
    if expressive_context.position is None:
        expressive_context=replace(expressive_context,position=position)
    elif expressive_context.position != position:
        raise ValueError("ExpressiveContext.position must match canonical position")

    expected=None
    if realchord_song is not None:
        realchord_song.validate()
        if position.realchord_id and position.realchord_id != realchord_song.realchord_id:
            raise ValueError("coordinate belongs to another RealChord song")
        if position.bar is not None and position.beat is not None:
            expected=expected_harmony_at(
                realchord_song,measure=position.bar,beat=position.beat
            )

    intent=realize_expressive_intent(expressive_context,profile=expression_profile)

    choices: list[RuntimeVocabularyChoice]=[]
    if legend_id is not None and vocabulary_query is not None:
        resources=legend_runtime_resources(legend_id)
        if vocabulary_query.legend_id != legend_id:
            raise ValueError("VocabularyQuery.legend_id must match legend_id")
        rows=resources.vocabulary(vocabulary_query)[:max(0,vocabulary_limit)]
        for offset,item in enumerate(rows):
            use=choose_runtime_vocabulary_use(
                item,
                vocabulary_query,
                opportunity_index=vocabulary_opportunity_index+offset,
            )
            choices.append(RuntimeVocabularyChoice(item,use))

    out=CanonicalRuntimeContext(position,expected,intent,tuple(choices))
    out.validate()
    return out
