"""Runtime score context resolved from structured scorebook evidence.

The resolver is intentionally evidence-bounded. It never invents a section,
phrase boundary, feel, solo region, or written melody when the ingestion layer
has not located that information precisely enough.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from .scorebooks import (
    ScoreEvidenceKind,
    ScorebookSongLocator,
)


@dataclass(frozen=True, order=True)
class ScorePosition:
    page: int
    bar: int | None = None
    beat: float | None = None

    def validate(self) -> None:
        if self.page < 1:
            raise ValueError("page must be 1-based")
        if self.bar is not None and self.bar < 1:
            raise ValueError("bar must be 1-based")
        if self.beat is not None and self.beat < 0:
            raise ValueError("beat cannot be negative")
        if self.beat is not None and self.bar is None:
            raise ValueError("beat requires bar")


@dataclass(frozen=True)
class ScoreSpan:
    page: int
    start_bar: int | None = None
    start_beat: float | None = None
    end_bar: int | None = None
    end_beat: float | None = None

    def validate(self) -> None:
        if self.page < 1:
            raise ValueError("page must be 1-based")
        if self.start_bar is not None and self.start_bar < 1:
            raise ValueError("start_bar must be 1-based")
        if self.end_bar is not None and self.end_bar < 1:
            raise ValueError("end_bar must be 1-based")
        if self.start_beat is not None and self.start_bar is None:
            raise ValueError("start_beat requires start_bar")
        if self.end_beat is not None and self.end_bar is None:
            raise ValueError("end_beat requires end_bar")
        if (
            self.start_bar is not None
            and self.end_bar is not None
            and self.end_bar < self.start_bar
        ):
            raise ValueError("end_bar must be >= start_bar")

    @property
    def is_page_wide(self) -> bool:
        return self.start_bar is None and self.end_bar is None

    @property
    def specificity(self) -> int:
        if self.start_bar is None:
            return 0
        if self.start_beat is None and self.end_beat is None:
            return 1
        return 2

    def contains(self, position: ScorePosition) -> bool:
        self.validate()
        position.validate()
        if position.page != self.page:
            return False
        if self.is_page_wide:
            return True
        if position.bar is None:
            return False

        start = (self.start_bar or 1, self.start_beat or 0.0)
        end_bar = self.end_bar if self.end_bar is not None else self.start_bar
        end = (end_bar or start[0], self.end_beat if self.end_beat is not None else float("inf"))
        here = (position.bar, position.beat or 0.0)
        return start <= here <= end

    def starts_at(self, position: ScorePosition) -> bool:
        if position.page != self.page or self.start_bar is None or position.bar is None:
            return False
        if position.bar != self.start_bar:
            return False
        if self.start_beat is None:
            return position.beat in (None, 0.0)
        return position.beat == self.start_beat


@dataclass(frozen=True)
class StructuredScoreEvidence:
    kind: ScoreEvidenceKind
    value: str
    span: ScoreSpan
    confidence: float = 1.0
    provenance: tuple[str, ...] = ()

    def validate(self) -> None:
        if not self.value.strip():
            raise ValueError("score evidence value is required")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be within 0..1")
        self.span.validate()


@dataclass(frozen=True)
class ScoreContextSnapshot:
    book_id: str
    song_id: str
    position: ScorePosition
    style: tuple[str, ...] = ()
    meter: str | None = None
    section: str | None = None
    section_role: str | None = None
    current_feel: str | None = None
    feel_change_here: str | None = None
    pending_feel_change: str | None = None
    phrase_boundary_before: bool = False
    phrase_boundary_after: bool = False
    written_melody_active: bool = False
    written_part_role: str | None = None
    written_part_policy: str | None = None
    player_instructions: tuple[tuple[str, str], ...] = ()
    solo_indication: str | None = None
    navigation: tuple[str, ...] = ()
    unresolved_evidence: tuple[StructuredScoreEvidence, ...] = ()
    confidence: float = 1.0
    provenance: tuple[str, ...] = ()


def structured_evidence_from_locator(
    locator: ScorebookSongLocator,
) -> tuple[StructuredScoreEvidence, ...]:
    """Promote existing page-level evidence without inventing bar positions."""
    locator.validate()
    out: list[StructuredScoreEvidence] = []
    for item in locator.evidence:
        item.validate()
        page = item.source_page if item.source_page is not None else locator.start_page
        out.append(StructuredScoreEvidence(
            kind=item.kind,
            value=item.value,
            span=ScoreSpan(page=page),
            confidence=item.confidence,
            provenance=item.provenance,
        ))
    return tuple(out)


def _best(items: Iterable[StructuredScoreEvidence]) -> StructuredScoreEvidence | None:
    seq = tuple(items)
    if not seq:
        return None
    return max(seq, key=lambda x: (x.span.specificity, x.confidence))


def _future_start_distance(
    item: StructuredScoreEvidence,
    position: ScorePosition,
) -> tuple[int, float] | None:
    span = item.span
    if span.page != position.page or span.start_bar is None or position.bar is None:
        return None
    start = (span.start_bar, span.start_beat or 0.0)
    here = (position.bar, position.beat or 0.0)
    if start <= here:
        return None
    return (start[0] - here[0], start[1] - here[1])


def resolve_score_context(
    locator: ScorebookSongLocator,
    position: ScorePosition,
    evidence: Iterable[StructuredScoreEvidence] | None = None,
) -> ScoreContextSnapshot:
    """Resolve only evidence supported at the current score position."""
    locator.validate()
    position.validate()
    items = tuple(
        structured_evidence_from_locator(locator)
        if evidence is None
        else evidence
    )
    for item in items:
        item.validate()

    page_items = tuple(x for x in items if x.span.page == position.page)
    active = tuple(x for x in page_items if x.span.contains(position))

    def values(kind: ScoreEvidenceKind) -> tuple[str, ...]:
        return tuple(dict.fromkeys(
            x.value for x in active if x.kind is kind
        ))

    def best_value(kind: ScoreEvidenceKind) -> str | None:
        item = _best(x for x in active if x.kind is kind)
        return item.value if item is not None else None

    feel_change_here_item = _best(
        x for x in page_items
        if x.kind is ScoreEvidenceKind.FEEL_CHANGE and x.span.starts_at(position)
    )

    future_feel = []
    for item in page_items:
        if item.kind is not ScoreEvidenceKind.FEEL_CHANGE:
            continue
        distance = _future_start_distance(item, position)
        if distance is not None:
            future_feel.append((distance, item))
    future_feel.sort(key=lambda pair: (pair[0], -pair[1].confidence))
    pending = future_feel[0][1].value if future_feel else None

    boundary_before = False
    boundary_after = False
    for item in active:
        if item.kind is not ScoreEvidenceKind.PHRASE_BOUNDARY:
            continue
        token = item.value.strip().lower()
        if token in {"before", "start", "phrase_start", "both"}:
            boundary_before = True
        if token in {"after", "end", "phrase_end", "both"}:
            boundary_after = True

    written_melody = any(
        x.kind is ScoreEvidenceKind.WRITTEN_MELODY for x in active
    )
    written_part = _best(
        x for x in active
        if x.kind in {
            ScoreEvidenceKind.WRITTEN_PART,
            ScoreEvidenceKind.WRITTEN_MELODY,
            ScoreEvidenceKind.WRITTEN_BASS_PART,
        }
    )
    written_policy = _best(
        x for x in active
        if x.kind is ScoreEvidenceKind.WRITTEN_PART_POLICY
    )
    player_instructions = tuple(
        ("bass", x.value)
        for x in active
        if x.kind is ScoreEvidenceKind.BASS_INSTRUCTION
    )
    solo = _best(
        x for x in active
        if x.kind in {ScoreEvidenceKind.SOLO_INDICATION, ScoreEvidenceKind.SOLO_CHANGES}
    )

    # Page-level feel changes tell us that the page contains a change, but not
    # where it occurs. Do not promote them to current/pending runtime state.
    unresolved = tuple(
        x for x in page_items
        if (
            x.kind in {ScoreEvidenceKind.FEEL_CHANGE, ScoreEvidenceKind.PHRASE_BOUNDARY}
            and x.span.is_page_wide
        )
        or (not x.span.is_page_wide and position.bar is None)
    )

    resolved = tuple(x for x in active if x not in unresolved)
    confidence = min((x.confidence for x in resolved), default=1.0)
    provenance = tuple(dict.fromkeys(
        p for item in resolved for p in item.provenance
    ))

    return ScoreContextSnapshot(
        book_id=locator.book_id,
        song_id=locator.song_id,
        position=position,
        style=values(ScoreEvidenceKind.STYLE),
        meter=best_value(ScoreEvidenceKind.METER),
        section=best_value(ScoreEvidenceKind.SECTION),
        section_role=best_value(ScoreEvidenceKind.SECTION_ROLE),
        current_feel=best_value(ScoreEvidenceKind.FEEL),
        feel_change_here=(
            feel_change_here_item.value if feel_change_here_item is not None else None
        ),
        pending_feel_change=pending,
        phrase_boundary_before=boundary_before,
        phrase_boundary_after=boundary_after,
        written_melody_active=written_melody,
        written_part_role=(written_part.value if written_part is not None else None),
        written_part_policy=(written_policy.value if written_policy is not None else None),
        player_instructions=player_instructions,
        solo_indication=(solo.value if solo is not None else None),
        navigation=values(ScoreEvidenceKind.NAVIGATION),
        unresolved_evidence=unresolved,
        confidence=confidence,
        provenance=provenance,
    )
