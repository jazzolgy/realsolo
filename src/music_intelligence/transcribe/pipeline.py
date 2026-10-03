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


def basic_rhythm_candidates(
    event: CommittedPerformanceEvent,
    intent: NotationIntent,
    *,
    meter_numerator: int = 4,
    meter_denominator: int = 4,
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

    if intent.allow_tuplet:
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

    return tuple(candidates)
