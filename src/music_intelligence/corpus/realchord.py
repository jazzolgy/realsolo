"""Shared RealChord 1350 symbolic-corpus integration.

RealChord is treated as a structural / expected-harmony reference, not as a
claim about what a particular performance actually played.

The raw source may live privately outside the public repository.  This module
defines the shared registry metadata and the normalized contract that all
players / transcription / research code can consume once a RealChord parser
has produced structured records.

Canonical learning position is musical:
realchord_id -> section -> measure -> beat.
Elapsed audio time remains provenance only.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Mapping, Sequence

from music_intelligence.learning.score_alignment import (
    MusicalScoreCoordinate,
    PerformancePhase,
)

from .registry import (
    CorpusAccess,
    CorpusItem,
    CorpusKind,
    CorpusRegistry,
    CorpusUse,
    RightsProfile,
)


REALCHORD_1350_DATASET_ID = "symbolic.realchord.1350"
REALCHORD_1350_DEFAULT_RELPATH = "symbolic/realchord_1350"


@dataclass(frozen=True)
class RealChordChord:
    beat: float
    symbol: str
    confidence: float = 1.0

    def validate(self) -> None:
        if self.beat < 0:
            raise ValueError("beat may not be negative")
        if not self.symbol.strip():
            raise ValueError("chord symbol is required")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be within 0..1")


@dataclass(frozen=True)
class RealChordMeasure:
    measure: int
    section: str = ""
    chords: tuple[RealChordChord, ...] = ()
    repeat_start: bool = False
    repeat_end: bool = False
    ending: str = ""
    form_role: str = ""
    navigation: tuple[str, ...] = ()

    def validate(self) -> None:
        if self.measure < 1:
            raise ValueError("measure must be 1-based")
        for chord in self.chords:
            chord.validate()


@dataclass(frozen=True)
class RealChordSong:
    realchord_id: str
    title: str
    composer: str = ""
    style: str = ""
    key: str = ""
    form: str = ""
    measures: tuple[RealChordMeasure, ...] = ()
    provenance: tuple[str, ...] = ()

    def validate(self) -> None:
        if not self.realchord_id:
            raise ValueError("realchord_id is required")
        if not self.title.strip():
            raise ValueError("title is required")
        seen: set[int] = set()
        for measure in self.measures:
            measure.validate()
            if measure.measure in seen:
                raise ValueError(f"duplicate measure: {measure.measure}")
            seen.add(measure.measure)

    @property
    def form_length_bars(self) -> int | None:
        return max((m.measure for m in self.measures), default=None)

    def measure_at(self, measure: int) -> RealChordMeasure:
        for item in self.measures:
            if item.measure == measure:
                return item
        raise KeyError(measure)


@dataclass(frozen=True)
class ExpectedHarmonyReference:
    """Expected harmony from RealChord at one musical position.

    This is deliberately separate from observed / inferred performance harmony.
    """

    realchord_id: str
    measure: int
    beat: float
    chord_symbol: str
    section: str = ""
    confidence: float = 1.0
    provenance: tuple[str, ...] = ()

    def validate(self) -> None:
        if not self.realchord_id:
            raise ValueError("realchord_id is required")
        if self.measure < 1:
            raise ValueError("measure must be 1-based")
        if self.beat < 0:
            raise ValueError("beat may not be negative")
        if not self.chord_symbol.strip():
            raise ValueError("chord_symbol is required")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be within 0..1")


def realchord_1350_corpus_item(
    *,
    local_relpath: str = REALCHORD_1350_DEFAULT_RELPATH,
    rights: RightsProfile | None = None,
) -> CorpusItem:
    """Return the one shared registry item for the RealChord 1350 corpus.

    Rights are intentionally caller-supplied / unknown by default.  Registering
    the corpus never implies training permission.
    """
    return CorpusItem(
        item_id=REALCHORD_1350_DATASET_ID,
        kind=CorpusKind.MUSICAL_INTELLIGENCE,
        media_type="application/x-realchord-corpus",
        title="RealChord 1350",
        artist_or_source="RealChord",
        local_relpath=local_relpath,
        access=CorpusAccess.LOCAL_PRIVATE,
        uses=frozenset({CorpusUse.RESEARCH, CorpusUse.REFERENCE, CorpusUse.EVALUATION}),
        tags=frozenset({
            "shared_core",
            "symbolic",
            "chord_chart",
            "form",
            "section",
            "repeat",
            "ending",
            "expected_harmony",
            "realchord",
        }),
        instruments=frozenset({
            "piano","bass","drums","sax","soloist","transcribe","ensemble",
        }),
        rights=rights or RightsProfile(
            source="RealChord 1350 shared symbolic corpus",
            training_permission=None,
            research_permission=None,
            redistribution_permission=None,
            notes="Set explicit rights metadata before enabling training or redistribution.",
        ),
        provenance=("realchord:1350",),
        notes=(
            "Shared symbolic reference. Use as Expected Harmony / form evidence; "
            "never overwrite Observed or Inferred Harmony from a performance."
        ),
    )


def register_realchord_1350(
    registry: CorpusRegistry,
    *,
    local_relpath: str = REALCHORD_1350_DEFAULT_RELPATH,
    rights: RightsProfile | None = None,
) -> None:
    registry.add(realchord_1350_corpus_item(local_relpath=local_relpath, rights=rights))


def _tuple_strings(value: object) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, str):
        return (value,) if value else ()
    if isinstance(value, Sequence):
        return tuple(str(x) for x in value if str(x))
    raise TypeError("expected string or sequence of strings")


def song_from_normalized_record(record: Mapping[str, object]) -> RealChordSong:
    """Build a shared RealChordSong from parser-normalized data.

    This is intentionally *not* a raw-file parser.  It is the adapter boundary
    for whichever importer parses the user's RealChord source into normalized
    measure/chord records.
    """
    canonical = record.get("canonical")
    if isinstance(canonical, Mapping):
        raw_measures = canonical.get("measures", ())
    else:
        raw_measures = record.get("measures", ())
    if not isinstance(raw_measures, Sequence):
        raise TypeError("measures must be a sequence")

    measures: list[RealChordMeasure] = []
    for raw in raw_measures:
        if not isinstance(raw, Mapping):
            raise TypeError("each measure must be a mapping")
        raw_chords = raw.get("chords")
        if raw_chords is None:
            raw_chords = raw.get("expected_harmony", ())
        if not isinstance(raw_chords, Sequence):
            raise TypeError("chords/expected_harmony must be a sequence")

        chords: list[RealChordChord] = []
        for item in raw_chords:
            if isinstance(item, str):
                chords.append(RealChordChord(beat=1.0, symbol=item))
                continue
            if not isinstance(item, Mapping):
                raise TypeError("each chord must be a mapping or string")
            chords.append(RealChordChord(
                beat=float(item.get("beat", 1.0)),
                symbol=str(item.get("symbol", "")),
                confidence=float(item.get("confidence", 1.0)),
            ))

        measures.append(RealChordMeasure(
            measure=int(raw.get("measure", raw.get("bar", 0))),
            section=str(raw.get("section", "")),
            chords=tuple(chords),
            repeat_start=bool(raw.get("repeat_start", False)),
            repeat_end=bool(raw.get("repeat_end", False)),
            ending="" if raw.get("ending") is None else str(raw.get("ending", "")),
            form_role=str(raw.get("form_role", "")),
            navigation=_tuple_strings(raw.get("navigation")),
        ))

    song=RealChordSong(
        realchord_id=str(record.get("realchord_id", "")),
        title=str(record.get("title", "")),
        composer=str(record.get("composer", "")),
        style=str(record.get("style", "")),
        key=str(record.get("key", "")),
        form=str(record.get("form", "")),
        measures=tuple(measures),
        # RealChord musical records intentionally carry no source-tracking metadata.
        # The legacy dataclass field remains empty for API compatibility.
        provenance=(),
    )
    song.validate()
    return song


def expected_harmony_at(
    song: RealChordSong,
    *,
    measure: int,
    beat: float,
) -> ExpectedHarmonyReference | None:
    """Resolve the active Expected Harmony at a RealChord position.

    Chords are interpreted as becoming active at their beat until the next
    chord within that measure.  Cross-measure carry is intentionally not guessed
    when the current measure contains no chord.
    """
    song.validate()
    bar=song.measure_at(measure)
    eligible=[chord for chord in bar.chords if chord.beat <= beat]
    if not eligible:
        return None
    chord=max(eligible,key=lambda x:x.beat)
    ref=ExpectedHarmonyReference(
        realchord_id=song.realchord_id,
        measure=measure,
        beat=beat,
        chord_symbol=chord.symbol,
        section=bar.section,
        confidence=chord.confidence,
        provenance=(),
    )
    ref.validate()
    return ref


def coordinate_from_realchord(
    song: RealChordSong,
    *,
    measure: int,
    beat: float | None = None,
    chorus_index: int | None = None,
    performance_phase: PerformancePhase = PerformancePhase.UNKNOWN,
    confidence: float = 1.0,
) -> MusicalScoreCoordinate:
    """Create the shared canonical coordinate anchored to RealChord."""
    song.validate()
    bar=song.measure_at(measure)
    chord=""
    if beat is not None:
        harmony=expected_harmony_at(song, measure=measure, beat=beat)
        if harmony is not None:
            chord=harmony.chord_symbol

    return MusicalScoreCoordinate(
        song_id=song.title,
        score_source_id=f"realchord:{song.realchord_id}",
        realchord_id=song.realchord_id,
        section=bar.section,
        bar=measure,
        beat=beat,
        form_length_bars=song.form_length_bars,
        form_bar=measure if song.form_length_bars is not None else None,
        chorus_index=chorus_index,
        performance_phase=performance_phase,
        chord_label=chord,
        form_role=bar.form_role or song.form,
        navigation_state=";".join(bar.navigation),
        arrangement_segment="core_form",
        within_core_form=True,
        confidence=confidence,
        provenance=(),
    )
