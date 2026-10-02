"""Shared scorebook corpus and page-level ingestion contracts.

The nine user-provided Real/New Real/Vocal books are private source materials.
They are registered in Shared Core so every player can refer to the same book,
page and song identity without duplicating scans in player branches.

This module stores metadata, page/song locators, extraction status and
instrument-neutral score evidence. It does NOT store copied melodies or
verbatim copyrighted score pages in the public repository.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Iterable

from .registry import (
    CorpusAccess,
    CorpusItem,
    CorpusKind,
    CorpusRegistry,
    CorpusUse,
    RightsProfile,
)


class ScorebookFamily(str, Enum):
    REAL_BOOK = "real_book"
    NEW_REAL_BOOK = "new_real_book"
    VOCAL_REAL_BOOK = "vocal_real_book"
    CHRISTMAS_REAL_BOOK = "christmas_real_book"


class ScoreIngestStatus(str, Enum):
    UNSEEN = "unseen"
    LOCATED = "located"
    VISION_REVIEWED = "vision_reviewed"
    STRUCTURED = "structured"
    VERIFIED = "verified"
    REJECTED = "rejected"


class ScoreEvidenceKind(str, Enum):
    TITLE = "title"
    COMPOSER = "composer"
    STYLE = "style"
    TEMPO = "tempo"
    METER = "meter"
    FEEL = "feel"
    FORM = "form"
    SECTION = "section"
    SECTION_ROLE = "section_role"
    PHRASE_BOUNDARY = "phrase_boundary"
    NAVIGATION = "navigation"
    CHORD = "chord"
    SOLO_CHANGES = "solo_changes"
    SOLO_INDICATION = "solo_indication"
    FEEL_CHANGE = "feel_change"
    BASS_INSTRUCTION = "bass_instruction"
    WRITTEN_PART = "written_part"
    WRITTEN_MELODY = "written_melody"
    WRITTEN_BASS_PART = "written_bass_part"
    WRITTEN_PART_POLICY = "written_part_policy"
    ARRANGEMENT_NOTE = "arrangement_note"


@dataclass(frozen=True)
class ScorebookSpec:
    book_id: str
    filename: str
    family: ScorebookFamily
    volume: int | None
    local_relpath: str
    notes: str = ""


@dataclass(frozen=True)
class ScoreEvidence:
    kind: ScoreEvidenceKind
    value: str
    confidence: float = 1.0
    source_page: int | None = None
    provenance: tuple[str, ...] = ()

    def validate(self) -> None:
        if not self.value.strip():
            raise ValueError("score evidence value is required")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be within 0..1")
        if self.source_page is not None and self.source_page < 1:
            raise ValueError("source_page must be 1-based")


@dataclass(frozen=True)
class ScorebookSongLocator:
    song_id: str
    book_id: str
    title: str
    start_page: int
    end_page: int | None = None
    status: ScoreIngestStatus = ScoreIngestStatus.LOCATED
    evidence: tuple[ScoreEvidence, ...] = ()
    notes: str = ""

    def validate(self) -> None:
        if not self.song_id or not self.book_id or not self.title:
            raise ValueError("song_id, book_id and title are required")
        if self.start_page < 1:
            raise ValueError("start_page must be 1-based")
        if self.end_page is not None and self.end_page < self.start_page:
            raise ValueError("end_page must be >= start_page")
        for item in self.evidence:
            item.validate()


def _private_rights(note: str) -> RightsProfile:
    return RightsProfile(
        source="user-provided private scorebook scan",
        rights_holder="unknown / publisher-specific",
        license=None,
        training_permission=None,
        research_permission=True,
        commercial_permission=None,
        redistribution_permission=False,
        notes=(
            "Private project source. Use for analysis, research, evaluation and "
            "abstract feature extraction. Do not redistribute raw pages. " + note
        ),
    )


SCOREBOOK_SPECS: tuple[ScorebookSpec, ...] = (
    ScorebookSpec(
        "scorebook.real.1",
        "Realbk1.pdf",
        ScorebookFamily.REAL_BOOK,
        1,
        "scorebooks/real_book/Realbk1.pdf",
        "Classic handwritten-style Real Book volume.",
    ),
    ScorebookSpec(
        "scorebook.real.2",
        "RealBk2.pdf",
        ScorebookFamily.REAL_BOOK,
        2,
        "scorebooks/real_book/RealBk2.pdf",
        "Classic handwritten-style Real Book volume.",
    ),
    ScorebookSpec(
        "scorebook.real.3",
        "RealBk3.pdf",
        ScorebookFamily.REAL_BOOK,
        3,
        "scorebooks/real_book/RealBk3.pdf",
        "Real Book volume 3 style collection.",
    ),
    ScorebookSpec(
        "scorebook.newreal.1",
        "NewReal1.pdf",
        ScorebookFamily.NEW_REAL_BOOK,
        1,
        "scorebooks/new_real_book/NewReal1.pdf",
    ),
    ScorebookSpec(
        "scorebook.newreal.2",
        "NewReal2.pdf",
        ScorebookFamily.NEW_REAL_BOOK,
        2,
        "scorebooks/new_real_book/NewReal2.pdf",
    ),
    ScorebookSpec(
        "scorebook.newreal.3",
        "NewReal3.pdf",
        ScorebookFamily.NEW_REAL_BOOK,
        3,
        "scorebooks/new_real_book/NewReal3.pdf",
    ),
    ScorebookSpec(
        "scorebook.vocal.1",
        "VcRealBk1.pdf",
        ScorebookFamily.VOCAL_REAL_BOOK,
        1,
        "scorebooks/vocal_real_book/VcRealBk1.pdf",
    ),
    ScorebookSpec(
        "scorebook.vocal.2",
        "VcRealBk2.pdf",
        ScorebookFamily.VOCAL_REAL_BOOK,
        2,
        "scorebooks/vocal_real_book/VcRealBk2.pdf",
    ),
    ScorebookSpec(
        "scorebook.christmas",
        "RealChBk.pdf",
        ScorebookFamily.CHRISTMAS_REAL_BOOK,
        None,
        "scorebooks/christmas/RealChBk.pdf",
    ),
)


def scorebook_corpus_items() -> tuple[CorpusItem, ...]:
    items: list[CorpusItem] = []
    all_instruments = frozenset({
        "bass", "piano", "drums", "sax", "soloist", "transcribe", "ensemble"
    })
    for spec in SCOREBOOK_SPECS:
        items.append(CorpusItem(
            item_id=spec.book_id,
            kind=CorpusKind.MUSICAL_INTELLIGENCE,
            media_type="application/pdf",
            title=spec.filename,
            artist_or_source="user-provided scorebook",
            local_relpath=spec.local_relpath,
            access=CorpusAccess.PROJECT_PRIVATE,
            uses=frozenset({
                CorpusUse.RESEARCH,
                CorpusUse.REFERENCE,
                CorpusUse.EVALUATION,
            }),
            tags=frozenset({
                "scorebook",
                "jazz",
                "lead_sheet",
                "shared_core",
                spec.family.value,
            }),
            instruments=all_instruments,
            rights=_private_rights(spec.notes),
            provenance=("user_upload", "scorebook_manifest_v1"),
            notes=spec.notes,
        ))
    return tuple(items)


def register_scorebooks(registry: CorpusRegistry) -> None:
    for item in scorebook_corpus_items():
        registry.add(item)


# Seed locators are deliberately limited to pages visually reviewed in the
# project. They are evidence anchors, not a claim that the full books have been
# ingested yet.
SEED_SONG_LOCATORS: tuple[ScorebookSongLocator, ...] = (
    ScorebookSongLocator(
        "score.real1.a_foggy_day",
        "scorebook.real.1",
        "A Foggy Day",
        6,
        status=ScoreIngestStatus.VISION_REVIEWED,
        evidence=(ScoreEvidence(ScoreEvidenceKind.STYLE, "medium swing", .85, 6),),
    ),
    ScorebookSongLocator(
        "score.real1.a_night_in_tunisia",
        "scorebook.real.1",
        "A Night In Tunisia",
        7,
        status=ScoreIngestStatus.VISION_REVIEWED,
        evidence=(ScoreEvidence(ScoreEvidenceKind.STYLE, "medium afro", .90, 7),),
    ),
    ScorebookSongLocator(
        "score.real2.alfies_theme",
        "scorebook.real.2",
        "Alfie's Theme",
        4,
        status=ScoreIngestStatus.VISION_REVIEWED,
        evidence=(
            ScoreEvidence(ScoreEvidenceKind.FEEL_CHANGE, "two feel", .98, 4),
            ScoreEvidence(ScoreEvidenceKind.FEEL_CHANGE, "in four", .98, 4),
            ScoreEvidence(ScoreEvidenceKind.FEEL_CHANGE, "back to 2", .98, 4),
        ),
    ),
    ScorebookSongLocator(
        "score.newreal1.airegin",
        "scorebook.newreal.1",
        "Airegin",
        2,
        status=ScoreIngestStatus.VISION_REVIEWED,
        evidence=(
            ScoreEvidence(ScoreEvidenceKind.STYLE, "medium-up latin; head swings", .96, 2),
            ScoreEvidence(ScoreEvidenceKind.FORM, "ABAC", .92, 2),
        ),
    ),
    ScorebookSongLocator(
        "score.newreal1.anthropology",
        "scorebook.newreal.1",
        "Anthropology",
        11,
        status=ScoreIngestStatus.VISION_REVIEWED,
        evidence=(ScoreEvidence(ScoreEvidenceKind.STYLE, "fast bebop", .99, 11),),
    ),
    ScorebookSongLocator(
        "score.newreal1.autumn_leaves",
        "scorebook.newreal.1",
        "Autumn Leaves",
        12,
        status=ScoreIngestStatus.VISION_REVIEWED,
        evidence=(ScoreEvidence(ScoreEvidenceKind.STYLE, "medium swing", .99, 12),),
    ),
    ScorebookSongLocator(
        "score.newreal2.along_came_betty",
        "scorebook.newreal.2",
        "Along Came Betty",
        7,
        end_page=8,
        status=ScoreIngestStatus.VISION_REVIEWED,
        evidence=(
            ScoreEvidence(ScoreEvidenceKind.STYLE, "medium swing", .99, 7),
            ScoreEvidence(
                ScoreEvidenceKind.BASS_INSTRUCTION,
                "bass walks",
                .99,
                8,
                ("scorebook:newreal2:p8", "vision-reviewed"),
            ),
            ScoreEvidence(
                ScoreEvidenceKind.SECTION_ROLE,
                "D: explicit bass-walk instruction region; no dedicated written bass staff verified",
                .99,
                8,
                ("scorebook:newreal2:p8", "vision-reviewed"),
            ),
        ),
    ),
    ScorebookSongLocator(
        "score.newreal2.asa",
        "scorebook.newreal.2",
        "Asa (The Zoo Blues)",
        9,
        end_page=10,
        status=ScoreIngestStatus.VISION_REVIEWED,
        evidence=(
            ScoreEvidence(ScoreEvidenceKind.STYLE, "medium funk", .99, 9),
            ScoreEvidence(
                ScoreEvidenceKind.WRITTEN_BASS_PART,
                "dedicated syncopated funk bass page",
                .99,
                10,
                ("scorebook:newreal2:p10", "vision-reviewed"),
            ),
            ScoreEvidence(
                ScoreEvidenceKind.WRITTEN_PART_POLICY,
                "use as groove/ostinato and articulation evidence; not as walking-bass target",
                .98,
                10,
                ("scorebook:newreal2:p10", "vision-reviewed"),
            ),
        ),
    ),
    ScorebookSongLocator(
        "score.newreal3.actual_proof",
        "scorebook.newreal.3",
        "Actual Proof",
        1,
        end_page=2,
        status=ScoreIngestStatus.VISION_REVIEWED,
        evidence=(
            ScoreEvidence(ScoreEvidenceKind.STYLE, "medium funk", .99, 1),
            ScoreEvidence(
                ScoreEvidenceKind.WRITTEN_BASS_PART,
                "dedicated bass page",
                .99,
                2,
                ("scorebook:newreal3:p2", "vision-reviewed"),
            ),
            ScoreEvidence(
                ScoreEvidenceKind.WRITTEN_PART_POLICY,
                "bass line freely interpreted except last two bars of A are played every chorus",
                .99,
                2,
                ("scorebook:newreal3:p2", "vision-reviewed"),
            ),
            ScoreEvidence(
                ScoreEvidenceKind.SECTION_ROLE,
                "A last two bars: recurring fixed anchor; remainder: interpretive bass material",
                .98,
                2,
                ("scorebook:newreal3:p2", "vision-reviewed"),
            ),
        ),
    ),
    ScorebookSongLocator(
        "score.real3.after_you",
        "scorebook.real.3",
        "After You",
        1,
        status=ScoreIngestStatus.VISION_REVIEWED,
        evidence=(ScoreEvidence(ScoreEvidenceKind.STYLE, "medium even 8ths", .96, 1),),
    ),
    ScorebookSongLocator(
        "score.vocal1.a_foggy_day",
        "scorebook.vocal.1",
        "A Foggy Day",
        5,
        end_page=6,
        status=ScoreIngestStatus.VISION_REVIEWED,
        evidence=(ScoreEvidence(ScoreEvidenceKind.STYLE, "medium swing", .92, 5),),
    ),
    ScorebookSongLocator(
        "score.vocal2.lady_bird",
        "scorebook.vocal.2",
        "Lady Bird",
        1,
        end_page=2,
        status=ScoreIngestStatus.VISION_REVIEWED,
        evidence=(ScoreEvidence(ScoreEvidenceKind.STYLE, "vocal lead sheet", .85, 1),),
    ),
    ScorebookSongLocator(
        "score.christmas.a_caroling_we_go",
        "scorebook.christmas",
        "A Caroling We Go",
        6,
        status=ScoreIngestStatus.VISION_REVIEWED,
        evidence=(ScoreEvidence(ScoreEvidenceKind.STYLE, "medium-fast", .92, 6),),
    ),
)


def validate_song_locators(
    locators: Iterable[ScorebookSongLocator],
    *,
    known_books: Iterable[ScorebookSpec] = SCOREBOOK_SPECS,
) -> None:
    books = {x.book_id for x in known_books}
    seen: set[str] = set()
    for item in locators:
        item.validate()
        if item.book_id not in books:
            raise ValueError(f"unknown scorebook: {item.book_id}")
        if item.song_id in seen:
            raise ValueError(f"duplicate song_id: {item.song_id}")
        seen.add(item.song_id)


def songs_for_book(
    book_id: str,
    locators: Iterable[ScorebookSongLocator] = SEED_SONG_LOCATORS,
) -> tuple[ScorebookSongLocator, ...]:
    return tuple(x for x in locators if x.book_id == book_id)


def ingestion_queue(
    locators: Iterable[ScorebookSongLocator],
) -> tuple[ScorebookSongLocator, ...]:
    """Return songs still requiring structured extraction or verification."""
    priority = {
        ScoreIngestStatus.LOCATED: 0,
        ScoreIngestStatus.VISION_REVIEWED: 1,
        ScoreIngestStatus.STRUCTURED: 2,
        ScoreIngestStatus.UNSEEN: 3,
        ScoreIngestStatus.VERIFIED: 99,
        ScoreIngestStatus.REJECTED: 99,
    }
    return tuple(sorted(
        (x for x in locators if x.status not in {
            ScoreIngestStatus.VERIFIED,
            ScoreIngestStatus.REJECTED,
        }),
        key=lambda x: (priority[x.status], x.book_id, x.start_page),
    ))
