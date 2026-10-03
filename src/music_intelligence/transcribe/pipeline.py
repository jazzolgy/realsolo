"""First transcription pipeline bridge: performance events -> notation intent/candidates.

The bridge is deliberately instrument-neutral.  It consumes only semantics that
are already present in the committed event and never imports player generation
policy or shared harmony logic.
"""
from __future__ import annotations

from dataclasses import replace
from fractions import Fraction

from .events import CommittedPerformanceEvent
from .notation import (
    NotationCandidate,
    NotationIntent,
    NotationRelevance,
    RhythmNotationContext,
    RhythmicFeel,
    TupletRatio,
)
from .rhythm import (
    QuantizationGrid,
    quantize_score_span,
    split_note_for_readability,
)


def notation_intent_from_event(
    event: CommittedPerformanceEvent,
    *,
    relevance: NotationRelevance = NotationRelevance.INCLUDE,
) -> NotationIntent:
    """Project a committed performance event into notation-facing intent.

    This is a semantic projection only.  It does not quantize, spell pitches,
    choose a staff, or reinterpret player policy.
    """

    event.validate()
    alternatives = tuple(
        f"{alt.attribute}:{alt.value}" for alt in event.alternatives
    )
    evidence_ids = tuple(ref.source_id for ref in event.evidence)

    intent = NotationIntent(
        intent_id=f"notation-intent:{event.event_id}",
        source_event_ids=(event.event_id,),
        relevance=relevance,
        gesture_id=event.gesture_id,
        phrase_context_id=event.phrase_context_id,
        harmonic_context_id=event.harmonic_context_id,
        preserve_as_single_gesture=event.gesture_id is not None,
        articulation_intent=event.articulation,
        technique_intent=event.technique,
        confidence=event.confidence.notation_relevance,
        alternatives=alternatives,
        evidence_ids=evidence_ids,
        provenance=event.provenance + ("transcribe:notation-intent",),
    )
    intent.validate()
    return intent


def _timing_error(
    performed_onset: Fraction,
    performed_offset: Fraction,
    written_onset: Fraction,
    written_offset: Fraction,
) -> float:
    return float(
        abs(performed_onset - written_onset)
        + abs(performed_offset - written_offset)
    )


def rhythm_candidate_from_event(
    event: CommittedPerformanceEvent,
    intent: NotationIntent,
    *,
    grid: QuantizationGrid,
    candidate_suffix: str,
    tuplet: TupletRatio | None = None,
    complexity_cost: float = 0.0,
) -> NotationCandidate:
    """Create one rhythmic notation candidate from beat-domain evidence."""

    event.validate()
    intent.validate()
    grid.validate()

    if intent.relevance is NotationRelevance.OMIT:
        raise ValueError("omitted notation intent does not produce score atoms")
    if event.event_id not in intent.source_event_ids:
        raise ValueError("intent does not reference the supplied event")
    if event.time.transport_beat is None or event.time.transport_offset_beat is None:
        raise ValueError("rhythm candidate requires transport beat onset and offset")

    performed_onset = Fraction(event.time.transport_beat).limit_denominator(4096)
    performed_offset = Fraction(event.time.transport_offset_beat).limit_denominator(4096)
    span = quantize_score_span(performed_onset, performed_offset, grid=grid)

    atoms = split_note_for_readability(
        span,
        intent.source_event_ids,
        grid=grid,
    )
    if tuplet is not None:
        tuplet.validate()
        atoms = tuple(replace(atom, tuplet=tuplet) for atom in atoms)

    candidate = NotationCandidate(
        candidate_id=f"{intent.intent_id}:{candidate_suffix}",
        intent_id=intent.intent_id,
        atoms=atoms,
        fidelity_cost=_timing_error(
            performed_onset,
            performed_offset,
            span.onset,
            span.offset,
        ),
        readability_cost=0.0 if grid.step.denominator <= 4 else 0.12,
        complexity_cost=complexity_cost + (0.18 if tuplet is not None else 0.0),
        confidence=intent.confidence,
        reasons=(
            f"quantized to step={grid.step}",
            "barline crossings and readable syncopation represented with ties",
        ),
        alternatives=intent.alternatives,
        evidence_ids=intent.evidence_ids,
        provenance=intent.provenance + ("transcribe:rhythm-candidate",),
    )
    candidate.validate()
    return candidate



def _explicit_tuplet_from_metadata(
    event: CommittedPerformanceEvent,
) -> TupletRatio | None:
    raw = event.metadata.get("notation_tuplet")
    if raw is None:
        return None
    parts = str(raw).split(":")
    if len(parts) != 2:
        raise ValueError("notation_tuplet metadata must use N:M form")
    try:
        ratio = TupletRatio(int(parts[0]), int(parts[1]))
    except ValueError as exc:
        raise ValueError("notation_tuplet metadata must use integer N:M values") from exc
    ratio.validate()
    return ratio


def _candidate_with_cost_adjustment(
    candidate: NotationCandidate,
    *,
    complexity_delta: float = 0.0,
    readability_delta: float = 0.0,
    reason: str | None = None,
) -> NotationCandidate:
    updated = replace(
        candidate,
        complexity_cost=max(0.0, candidate.complexity_cost + complexity_delta),
        readability_cost=max(0.0, candidate.readability_cost + readability_delta),
        reasons=candidate.reasons + ((reason,) if reason is not None else ()),
    )
    updated.validate()
    return updated


def basic_rhythm_candidates(
    event: CommittedPerformanceEvent,
    intent: NotationIntent,
    *,
    meter_numerator: int = 4,
    meter_denominator: int = 4,
    rhythm_context: RhythmNotationContext = RhythmNotationContext(),
) -> tuple[NotationCandidate, ...]:
    """Generate a small readable candidate family.

    Initial family:
    - quarter grid
    - eighth grid
    - sixteenth grid
    - triplet-eighth grid when tuplets are allowed

    This deliberately favors a small interpretable family over exhaustive
    timestamp fitting.  Later rhythm intelligence can expand the candidate set.
    """

    if intent.relevance is NotationRelevance.OMIT:
        return ()
    rhythm_context.validate()

    explicit_tuplet = _explicit_tuplet_from_metadata(event)

    grids = (
        ("quarter", Fraction(1, 1), None, 0.00),
        ("eighth", Fraction(1, 2), None, 0.02),
        ("sixteenth", Fraction(1, 4), None, 0.12),
    )
    candidates = [
        rhythm_candidate_from_event(
            event,
            intent,
            grid=QuantizationGrid(
                step=step,
                meter_numerator=meter_numerator,
                meter_denominator=meter_denominator,
            ),
            candidate_suffix=name,
            complexity_cost=complexity,
        )
        for name, step, _, complexity in grids
    ]

    if explicit_tuplet is not None:
        step = Fraction(explicit_tuplet.normal, explicit_tuplet.actual) * Fraction(1, 2)
        explicit_candidate = rhythm_candidate_from_event(
            event,
            intent,
            grid=QuantizationGrid(
                step=step,
                meter_numerator=meter_numerator,
                meter_denominator=meter_denominator,
            ),
            candidate_suffix=f"explicit-tuplet-{explicit_tuplet.actual}-{explicit_tuplet.normal}",
            tuplet=explicit_tuplet,
            complexity_cost=0.0,
        )
        candidates.append(
            _candidate_with_cost_adjustment(
                explicit_candidate,
                complexity_delta=-0.18,
                readability_delta=-0.12,
                reason="explicit notation tuplet evidence",
            )
        )
    elif (
        intent.allow_tuplet
        and rhythm_context.feel is RhythmicFeel.AUTO
    ):
        candidates.append(
            rhythm_candidate_from_event(
                event,
                intent,
                grid=QuantizationGrid(
                    step=Fraction(1, 3),
                    meter_numerator=meter_numerator,
                    meter_denominator=meter_denominator,
                ),
                candidate_suffix="triplet-eighth",
                tuplet=TupletRatio(3, 2),
                complexity_cost=.08,
            )
        )

    if (
        rhythm_context.feel is RhythmicFeel.SWING
        and rhythm_context.prefer_written_eighths_for_swing
        and explicit_tuplet is None
    ):
        candidates = [
            _candidate_with_cost_adjustment(
                candidate,
                complexity_delta=-0.04
                if candidate.candidate_id.endswith(":eighth")
                else 0.0,
                readability_delta=-0.04
                if candidate.candidate_id.endswith(":eighth")
                else 0.0,
                reason="swing feel prefers written eighth-note notation"
                if candidate.candidate_id.endswith(":eighth")
                else None,
            )
            for candidate in candidates
        ]

    return tuple(candidates)
