"""Eliot Zigmund source-grounded rhythmic vocabulary."""
from __future__ import annotations
from dataclasses import dataclass

from music_intelligence.legends.interfaces import (
    LegendDomain,
    VocabularyDimension,
    VocabularyMemoryItem,
    VocabularyQuery,
    VocabularyUseType,
)


ELIOT_ZIGMUND_VOCABULARY = (
    VocabularyMemoryItem(
        vocabulary_id="ez_without_a_song_231",
        source_id="bill_evans_without_a_song_1977",
        recording_id="bill_evans_without_a_song_1977",
        tune_id="without_a_song",
        timestamp="06:42-07:07 analysis window; drum solo entry near 06:52",
        rhythm="triplet_grid_ioi_2_3_1",
        contour="accent_vector_0.638_0.720_0.613_0.659",
        transposition_normalized_representation="ioi:2,3,1|accent:0.638,0.720,0.613,0.659",
        articulation="mixed_kit_exact_voices_unverified",
        source_instrument="drums",
        dimensions=frozenset({
            VocabularyDimension.RHYTHM,
            VocabularyDimension.ACCENT,
            VocabularyDimension.PHRASE_SHAPE,
        }),
        transferable_to=frozenset({"drums"}),
        domains=frozenset({
            LegendDomain.RHYTHM_SUBDIVISION,
            LegendDomain.MOTIF_DEVELOPMENT,
            LegendDomain.REPETITION_VARIATION,
        }),
        context_tags=frozenset({
            "drum_solo", "jazz_trio", "late_foreground_allocation", "triplet_grid"
        }),
        candidate_uses=frozenset({
            VocabularyUseType.ADAPTED_LICK,
            VocabularyUseType.FRAGMENT_RECALL,
            VocabularyUseType.ABSTRACTED_PATTERN,
            VocabularyUseType.HYBRID_COMPOSITION,
        }),
        confidence=0.82,
        provenance=(
            "user_provided_bill_evans_compilation",
            "without_a_song_1977",
            "eliot_zigmund",
            "full_mix_signal_analysis",
            "abstracted_ioi_not_literal_transcription",
        ),
    ),
    VocabularyMemoryItem(
        vocabulary_id="ez_without_a_song_132",
        source_id="bill_evans_without_a_song_1977",
        recording_id="bill_evans_without_a_song_1977",
        tune_id="without_a_song",
        timestamp="06:42-07:07 analysis window; drum solo entry near 06:52",
        rhythm="triplet_grid_ioi_1_3_2",
        contour="accent_vector_0.662_0.741_0.757_0.748",
        transposition_normalized_representation="ioi:1,3,2|accent:0.662,0.741,0.757,0.748",
        articulation="mixed_kit_exact_voices_unverified",
        source_instrument="drums",
        dimensions=frozenset({
            VocabularyDimension.RHYTHM,
            VocabularyDimension.ACCENT,
            VocabularyDimension.PHRASE_SHAPE,
        }),
        transferable_to=frozenset({"drums"}),
        domains=frozenset({
            LegendDomain.RHYTHM_SUBDIVISION,
            LegendDomain.MOTIF_DEVELOPMENT,
            LegendDomain.REPETITION_VARIATION,
        }),
        context_tags=frozenset({
            "drum_solo", "jazz_trio", "late_foreground_allocation", "triplet_grid"
        }),
        candidate_uses=frozenset({
            VocabularyUseType.ADAPTED_LICK,
            VocabularyUseType.FRAGMENT_RECALL,
            VocabularyUseType.ABSTRACTED_PATTERN,
            VocabularyUseType.HYBRID_COMPOSITION,
        }),
        confidence=0.80,
        provenance=(
            "user_provided_bill_evans_compilation",
            "without_a_song_1977",
            "eliot_zigmund",
            "full_mix_signal_analysis",
            "abstracted_ioi_not_literal_transcription",
        ),
    ),
    VocabularyMemoryItem(
        vocabulary_id="ez_without_a_song_312",
        source_id="bill_evans_without_a_song_1977",
        recording_id="bill_evans_without_a_song_1977",
        tune_id="without_a_song",
        timestamp="06:42-07:07 analysis window; drum solo entry near 06:52",
        rhythm="triplet_grid_ioi_3_1_2",
        contour="accent_vector_0.812_0.620_0.555_0.706",
        transposition_normalized_representation="ioi:3,1,2|accent:0.812,0.620,0.555,0.706",
        articulation="mixed_kit_exact_voices_unverified",
        source_instrument="drums",
        dimensions=frozenset({
            VocabularyDimension.RHYTHM,
            VocabularyDimension.ACCENT,
            VocabularyDimension.PHRASE_SHAPE,
        }),
        transferable_to=frozenset({"drums"}),
        domains=frozenset({
            LegendDomain.RHYTHM_SUBDIVISION,
            LegendDomain.MOTIF_DEVELOPMENT,
            LegendDomain.REPETITION_VARIATION,
        }),
        context_tags=frozenset({
            "drum_solo", "jazz_trio", "late_foreground_allocation", "triplet_grid"
        }),
        candidate_uses=frozenset({
            VocabularyUseType.ADAPTED_LICK,
            VocabularyUseType.FRAGMENT_RECALL,
            VocabularyUseType.ABSTRACTED_PATTERN,
            VocabularyUseType.HYBRID_COMPOSITION,
        }),
        confidence=0.76,
        provenance=(
            "user_provided_bill_evans_compilation",
            "without_a_song_1977",
            "eliot_zigmund",
            "full_mix_signal_analysis",
            "abstracted_ioi_not_literal_transcription",
        ),
    ),
)


@dataclass(frozen=True)
class EliotZigmundVocabularyIndex:
    items: tuple[VocabularyMemoryItem, ...] = ELIOT_ZIGMUND_VOCABULARY

    def query(self, request: VocabularyQuery) -> tuple[VocabularyMemoryItem, ...]:
        if request.legend_id != "eliot_zigmund" or request.limit <= 0:
            return ()
        ranked = []
        for item in self.items:
            item.validate()
            if request.domain is not None and request.domain not in item.domains:
                continue
            if not item.candidate_uses.intersection(request.allowed_uses):
                continue
            if request.context_tags and not request.context_tags.issubset(item.context_tags):
                continue
            if request.required_dimensions and not request.required_dimensions.issubset(item.dimensions):
                continue
            if (
                request.target_instrument
                and item.transferable_to
                and request.target_instrument not in item.transferable_to
            ):
                continue
            score = item.confidence - min(0.25, 0.04 * item.recent_usage_count)
            ranked.append((score, item))
        ranked.sort(key=lambda pair: (pair[0], pair[1].vocabulary_id), reverse=True)
        return tuple(item for _, item in ranked[: request.limit])


ELIOT_ZIGMUND_VOCABULARY_INDEX = EliotZigmundVocabularyIndex()
