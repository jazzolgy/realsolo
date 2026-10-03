"""Charlie Parker vocabulary memory.

Why this index used to be empty
-------------------------------
The Parker research pipeline had already produced:
- contextual Legend tendencies,
- aggregate conditional statistics from 131 pedagogical symbolic licks,
- phrase-space statistics,
- alignment/source manifests,

but no ingestion step converted that evidence into VocabularyMemoryItem records.
The public Parker vocabulary directories were documentation-only and
PARKER_VOCABULARY_INDEX was instantiated with an empty tuple.

This module now promotes reusable source-grounded Parker material into the same
Shared Vocabulary contract used by other legends. Exact/literal structured
phrases can be loaded from parker/data/vocabulary*.json when available.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import json

from music_intelligence.legends.interfaces import (
    LegendDomain,
    SignatureStatus,
    VocabularyDimension,
    VocabularyMemoryItem,
    VocabularyQuery,
    VocabularyUseType,
)
from music_intelligence.vocabulary import rank_vocabulary_items


def _abstract_item(
    vocabulary_id: str,
    *,
    domains: tuple[LegendDomain,...],
    tags: tuple[str,...],
    dimensions: tuple[VocabularyDimension,...],
    harmonic_function: str="",
    phrase_position: str="",
    rhythm: str="",
    contour: str="",
    interval_pattern: str="",
    articulation: str="",
    tension_curve: str="",
    confidence: float=.84,
    provenance: tuple[str,...]=(),
) -> VocabularyMemoryItem:
    item=VocabularyMemoryItem(
        vocabulary_id=vocabulary_id,
        source_id="parker_intelligence_v2",
        harmony_context="bebop",
        harmonic_function=harmonic_function,
        phrase_position=phrase_position,
        rhythm=rhythm,
        contour=contour,
        interval_pattern=interval_pattern,
        articulation=articulation,
        tension_curve=tension_curve,
        source_instrument="alto_saxophone",
        dimensions=frozenset(dimensions),
        transferable_to=frozenset({
            "alto_saxophone","tenor_sax","sax","trumpet","piano","guitar",
        }),
        domains=frozenset(domains),
        context_tags=frozenset({"bebop","charlie_parker",*tags}),
        candidate_uses=frozenset({
            VocabularyUseType.ADAPTED_LICK,
            VocabularyUseType.FRAGMENT_RECALL,
            VocabularyUseType.ABSTRACTED_PATTERN,
            VocabularyUseType.HYBRID_COMPOSITION,
        }),
        signature_status=SignatureStatus.RECURRING,
        signature_evidence_count=2,
        confidence=confidence,
        provenance=(
            "research/legends/charlie_parker",
            *provenance,
        ),
    )
    item.validate()
    return item


PARKER_DERIVED_VOCABULARY: tuple[VocabularyMemoryItem,...]=(
    _abstract_item(
        "parker.vocab.syncopated_entry",
        domains=(LegendDomain.PHRASE_ENTRANCE,LegendDomain.FUTURE_HARMONY_AWARENESS),
        tags=("anticipation","offbeat_entry"),
        dimensions=(VocabularyDimension.RHYTHM,VocabularyDimension.PHRASE_SHAPE,VocabularyDimension.TARGET_BEHAVIOR),
        phrase_position="entry",
        rhythm="anticipated/offbeat entry",
        confidence=.94,
        provenance=("PARKER_ONLINE_PROFILE","omnibook/expert"),
    ),
    _abstract_item(
        "parker.vocab.passing_connector",
        domains=(LegendDomain.LINEAR_CONNECTION,),
        tags=("passing","connector"),
        dimensions=(VocabularyDimension.PITCH_INTERVAL,VocabularyDimension.CONTOUR),
        interval_pattern="close passing connection",
        confidence=.94,
        provenance=("PARKER_ONLINE_PROFILE","omnibook/expert"),
    ),
    _abstract_item(
        "parker.vocab.neighbor_glue",
        domains=(LegendDomain.LINEAR_CONNECTION,),
        tags=("neighbor","connector"),
        dimensions=(VocabularyDimension.PITCH_INTERVAL,VocabularyDimension.CONTOUR),
        interval_pattern="neighbor-tone melodic glue",
        confidence=.94,
        provenance=("PARKER_ONLINE_PROFILE","omnibook/expert"),
    ),
    _abstract_item(
        "parker.vocab.close_approach_target",
        domains=(LegendDomain.LINEAR_CONNECTION,LegendDomain.HARMONY_TARGET_SELECTION),
        tags=("close_approach","directed_target"),
        dimensions=(VocabularyDimension.PITCH_INTERVAL,VocabularyDimension.TARGET_BEHAVIOR),
        interval_pattern="semitone/step approach into target",
        confidence=.96,
        provenance=("PARKER_ONLINE_PROFILE","omnibook/book_or_paper/expert"),
    ),
    _abstract_item(
        "parker.vocab.altered_directed_route",
        domains=(LegendDomain.TENSION_RELEASE,LegendDomain.HARMONY_TARGET_SELECTION),
        tags=("altered","directed_target","resolution_path"),
        dimensions=(VocabularyDimension.TENSION_RELEASE,VocabularyDimension.TARGET_BEHAVIOR),
        harmonic_function="altered color with audible directed resolution",
        tension_curve="tension -> directed release",
        confidence=.94,
        provenance=("PARKER_ONLINE_PROFILE","book_or_paper/expert"),
    ),
    _abstract_item(
        "parker.vocab.syncopated_long_tone",
        domains=(LegendDomain.RHYTHM_SUBDIVISION,LegendDomain.PHRASE_ENTRANCE),
        tags=("syncopated_long_tone","anticipation"),
        dimensions=(VocabularyDimension.RHYTHM,VocabularyDimension.ACCENT,VocabularyDimension.PHRASE_SHAPE),
        rhythm="held note energized by syncopated/anticipated onset",
        confidence=.93,
        provenance=("PARKER_ONLINE_PROFILE","omnibook/expert"),
    ),
    _abstract_item(
        "parker.vocab.contextual_triplet",
        domains=(LegendDomain.RHYTHM_SUBDIVISION,),
        tags=("triplet","contextual_insertion"),
        dimensions=(VocabularyDimension.RHYTHM,),
        rhythm="triplet as local insertion rather than constant surface",
        confidence=.88,
        provenance=("PARKER_ONLINE_PROFILE","omnibook"),
    ),
    _abstract_item(
        "parker.vocab.ensemble_space_handoff",
        domains=(LegendDomain.BREATH_SPACE,LegendDomain.ENSEMBLE_INTERACTION,LegendDomain.CALL_RESPONSE),
        tags=("ensemble_space","handoff"),
        dimensions=(VocabularyDimension.INTERACTION_ROLE,VocabularyDimension.PHRASE_SHAPE,VocabularyDimension.DENSITY_ARC),
        phrase_position="intentional space / handoff",
        confidence=.91,
        provenance=("PARKER_ONLINE_PROFILE","greatest_hits_audio_study"),
    ),
    _abstract_item(
        "parker.vocab.step_motion_bias",
        domains=(LegendDomain.LINEAR_CONNECTION,),
        tags=("step_motion",),
        dimensions=(VocabularyDimension.PITCH_INTERVAL,VocabularyDimension.CONTOUR),
        interval_pattern="adjacent step motion favored",
        confidence=.82,
        provenance=("pedagogical_symbolic_131","conditional_stats"),
    ),
    _abstract_item(
        "parker.vocab.compact_motion_within_p4",
        domains=(LegendDomain.LINEAR_CONNECTION,LegendDomain.INTERVAL_LEAP_GRAMMAR),
        tags=("within_p4_motion",),
        dimensions=(VocabularyDimension.PITCH_INTERVAL,VocabularyDimension.CONTOUR),
        interval_pattern="most adjacent motion remains within P4",
        confidence=.82,
        provenance=("pedagogical_symbolic_131","conditional_stats"),
    ),
    _abstract_item(
        "parker.vocab.wide_leap_contrary_recovery",
        domains=(LegendDomain.INTERVAL_LEAP_GRAMMAR,LegendDomain.LINEAR_CONNECTION),
        tags=("wide_leap","after_wide_leap","contrary_recovery"),
        dimensions=(VocabularyDimension.PITCH_INTERVAL,VocabularyDimension.CONTOUR),
        interval_pattern="marked wide leap -> contrary recovery",
        confidence=.86,
        provenance=("pedagogical_symbolic_131","conditional_stats"),
    ),
    _abstract_item(
        "parker.vocab.wide_leap_compact_recovery",
        domains=(LegendDomain.INTERVAL_LEAP_GRAMMAR,LegendDomain.LINEAR_CONNECTION),
        tags=("wide_leap","after_wide_leap","recovery_within_p4"),
        dimensions=(VocabularyDimension.PITCH_INTERVAL,VocabularyDimension.CONTOUR),
        interval_pattern="wide leap -> compact recovery within P4",
        confidence=.86,
        provenance=("pedagogical_symbolic_131","conditional_stats"),
    ),
    _abstract_item(
        "parker.vocab.terminal_long_tone",
        domains=(LegendDomain.PHRASE_ENDING,LegendDomain.RHYTHM_SUBDIVISION),
        tags=("structural_terminal_long_tone","phrase_late"),
        dimensions=(VocabularyDimension.PHRASE_SHAPE,VocabularyDimension.RHYTHM),
        phrase_position="structural ending",
        rhythm="terminal duration longer than internal duration",
        confidence=.78,
        provenance=("pedagogical_symbolic_131","conditional_stats"),
    ),
    _abstract_item(
        "parker.vocab.rest_half_beat",
        domains=(LegendDomain.BREATH_SPACE,),
        tags=("rest","rest_half_beat"),
        dimensions=(VocabularyDimension.RHYTHM,VocabularyDimension.PHRASE_SHAPE),
        rhythm="half-beat punctuation",
        confidence=.74,
        provenance=("digital_omnibook_derived_rests","phrase_space_stats"),
    ),
    _abstract_item(
        "parker.vocab.rest_one_beat",
        domains=(LegendDomain.BREATH_SPACE,),
        tags=("rest","rest_one_beat"),
        dimensions=(VocabularyDimension.RHYTHM,VocabularyDimension.PHRASE_SHAPE),
        rhythm="one-beat phrase space",
        confidence=.76,
        provenance=("digital_omnibook_derived_rests","phrase_space_stats"),
    ),
    _abstract_item(
        "parker.vocab.rest_two_beats",
        domains=(LegendDomain.BREATH_SPACE,),
        tags=("rest","rest_two_beats"),
        dimensions=(VocabularyDimension.RHYTHM,VocabularyDimension.PHRASE_SHAPE),
        rhythm="two-beat / half-bar handoff",
        confidence=.72,
        provenance=("digital_omnibook_derived_rests","phrase_space_stats"),
    ),
    _abstract_item(
        "parker.vocab.rest_four_plus",
        domains=(LegendDomain.BREATH_SPACE,LegendDomain.ENSEMBLE_INTERACTION),
        tags=("rest","rest_four_beats_plus","ensemble_space"),
        dimensions=(VocabularyDimension.RHYTHM,VocabularyDimension.INTERACTION_ROLE,VocabularyDimension.PHRASE_SHAPE),
        rhythm="full-bar or longer structural handoff",
        confidence=.68,
        provenance=("digital_omnibook_derived_rests","phrase_space_stats"),
    ),
)


def _enum_set(values, enum_type):
    return frozenset(enum_type(value) for value in values)


def _literal_items_from_data() -> tuple[VocabularyMemoryItem,...]:
    """Load exact/normalized Parker phrases when structured files are present.

    Expected files are `parker/data/vocabulary*.json` with the same field names
    as VocabularyMemoryItem. No note material is invented from aggregate stats.
    """
    data_dir=Path(__file__).with_name("data")
    out=[]
    for path in sorted(data_dir.glob("vocabulary*.json")):
        payload=json.loads(path.read_text(encoding="utf-8"))
        source_id=str(payload.get("source_id","parker_structured_vocabulary"))
        recording_id=str(payload.get("recording_id",""))
        for raw in payload.get("items",()):
            literal=str(raw.get("literal_representation",""))
            uses=_enum_set(
                raw.get("candidate_uses",(
                    "literal_quote","transposed_lick","adapted_lick",
                    "fragment_recall","abstracted_pattern","hybrid_composition",
                )),
                VocabularyUseType,
            )
            if not literal:
                uses=frozenset(x for x in uses if x is not VocabularyUseType.LITERAL_QUOTE)
            item=VocabularyMemoryItem(
                vocabulary_id=str(raw["vocabulary_id"]),
                source_id=source_id,
                recording_id=recording_id,
                tune_id=str(raw.get("tune_id","")),
                chorus=str(raw.get("chorus","")),
                bar=str(raw.get("bar","")),
                timestamp=str(raw.get("timestamp","")),
                literal_representation=literal,
                transposition_normalized_representation=str(raw.get("transposition_normalized_representation","")),
                harmony_context=str(raw.get("harmony_context","")),
                local_key=str(raw.get("local_key","")),
                harmonic_function=str(raw.get("harmonic_function","")),
                phrase_position=str(raw.get("phrase_position","")),
                entrance=str(raw.get("entrance","")),
                ending=str(raw.get("ending","")),
                rhythm=str(raw.get("rhythm","")),
                contour=str(raw.get("contour","")),
                interval_pattern=str(raw.get("interval_pattern","")),
                articulation=str(raw.get("articulation","")),
                register=str(raw.get("register","")),
                tension_curve=str(raw.get("tension_curve","")),
                source_instrument=str(raw.get("source_instrument","alto_saxophone")),
                dimensions=_enum_set(raw.get("dimensions",()),VocabularyDimension),
                transferable_to=frozenset(raw.get("transferable_to",("alto_saxophone","tenor_sax","piano","trumpet","guitar"))),
                domains=_enum_set(raw.get("domains",()),LegendDomain),
                context_tags=frozenset(raw.get("context_tags",("bebop","charlie_parker"))),
                candidate_uses=uses,
                signature_status=SignatureStatus(raw.get("signature_status","recurring")),
                signature_evidence_count=int(raw.get("signature_evidence_count",2)),
                confidence=float(raw.get("confidence",1.0)),
                provenance=tuple(raw.get("provenance",()))+(f"structured_file:{path.name}",),
            )
            item.validate()
            out.append(item)
    return tuple(out)


def load_parker_vocabulary() -> tuple[VocabularyMemoryItem,...]:
    rows=list(PARKER_DERIVED_VOCABULARY)+list(_literal_items_from_data())
    seen=set()
    unique=[]
    for item in rows:
        if item.vocabulary_id in seen:
            continue
        seen.add(item.vocabulary_id)
        unique.append(item)
    return tuple(unique)


@dataclass(frozen=True)
class ParkerVocabularyIndex:
    items: tuple[VocabularyMemoryItem, ...] = ()

    def query(self, request: VocabularyQuery) -> tuple[VocabularyMemoryItem, ...]:
        if request.legend_id != "charlie_parker":
            return ()
        return rank_vocabulary_items(self.items, request)


PARKER_VOCABULARY_INDEX = ParkerVocabularyIndex(load_parker_vocabulary())
