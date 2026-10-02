"""Transcription / notation workstream public API.

Performance Representation != Notation Representation.

This package consumes committed performance evidence and projects it through
notation intent/candidates into readable score structures and output adapters.
It must not contain player generation policy or duplicate Shared Core harmony /
ensemble reasoning.
"""

from .events import (
    CommittedPerformanceEvent,
    ConfidenceBundle,
    EventAlternative,
    EvidenceKind,
    EvidenceRef,
    PerformedPitch,
    PerformanceTimeSpan,
    UnpitchedToken,
)
from .notation import (
    NotatedAtom,
    NotatedAtomKind,
    NotationCandidate,
    NotationIntent,
    NotationRelevance,
    ScoreSpan,
    TupletRatio,
    choose_preferred_candidate,
)
from .rhythm import (
    QuantizationGrid,
    quantize_score_span,
    rest_for_gap,
    split_note_across_bars,
    tuplet_note,
)
from .pipeline import (
    basic_rhythm_candidates,
    notation_intent_from_event,
    rhythm_candidate_from_event,
)
from .spelling import (
    AccidentalPreference,
    PitchSpellingCandidate,
    PitchSpellingContext,
    WrittenPitch,
    preferred_spelling,
    spelling_candidates,
)
from .allocation import (
    AllocationEvidence,
    StaffProfile,
    VoiceStaffCandidate,
    allocation_candidates,
    preferred_allocation,
)
from .piano import PianoGestureCandidate, piano_gesture_candidates
from .instrument_rules import (
    InstrumentNotationDirective,
    NoteheadStyle,
    bass_notation_directive,
    drum_notation_directive,
    sax_notation_directive,
)
from .score import (
    LogicalScore,
    LogicalScoreEvent,
    LogicalScorePart,
    ReadableScore,
    ScoreEvent,
    ScorePart,
    assemble_logical_score,
    assemble_score,
    extract_individual_part,
)
from .musicxml import score_to_musicxml
from .engraving import (
    BeamState,
    EngravingIntent,
    EngravingPlan,
    EngravingProfile,
    StemDirection,
    TupletBracketMode,
    VerticalPlacement,
    beam_group_intents,
    build_default_engraving_plan,
    voice_stem_directions,
)
from .layout import (
    LayoutPressure,
    OpticalSpacingDecision,
    layout_pressures,
    optical_spacing_decisions,
)
from .sequence import assemble_monophonic_voice
from .projection import EventProjectionResult, project_pitched_event

__all__ = [
    "CommittedPerformanceEvent",
    "ConfidenceBundle",
    "EventAlternative",
    "EvidenceKind",
    "EvidenceRef",
    "PerformedPitch",
    "PerformanceTimeSpan",
    "UnpitchedToken",
    "NotatedAtom",
    "NotatedAtomKind",
    "NotationCandidate",
    "NotationIntent",
    "NotationRelevance",
    "ScoreSpan",
    "TupletRatio",
    "choose_preferred_candidate",
    "QuantizationGrid",
    "quantize_score_span",
    "rest_for_gap",
    "split_note_across_bars",
    "tuplet_note",
    "basic_rhythm_candidates",
    "notation_intent_from_event",
    "rhythm_candidate_from_event",
    "AccidentalPreference",
    "PitchSpellingCandidate",
    "PitchSpellingContext",
    "WrittenPitch",
    "preferred_spelling",
    "spelling_candidates",
    "AllocationEvidence",
    "StaffProfile",
    "VoiceStaffCandidate",
    "allocation_candidates",
    "preferred_allocation",
    "PianoGestureCandidate",
    "piano_gesture_candidates",
    "InstrumentNotationDirective",
    "NoteheadStyle",
    "bass_notation_directive",
    "drum_notation_directive",
    "sax_notation_directive",
    "LogicalScore",
    "LogicalScoreEvent",
    "LogicalScorePart",
    "ReadableScore",
    "ScoreEvent",
    "ScorePart",
    "assemble_logical_score",
    "assemble_score",
    "extract_individual_part",
    "score_to_musicxml",
    "BeamState",
    "EngravingIntent",
    "EngravingPlan",
    "EngravingProfile",
    "StemDirection",
    "TupletBracketMode",
    "VerticalPlacement",
    "beam_group_intents",
    "build_default_engraving_plan",
    "voice_stem_directions",
    "LayoutPressure",
    "OpticalSpacingDecision",
    "layout_pressures",
    "optical_spacing_decisions",
    "assemble_monophonic_voice",
    "EventProjectionResult",
    "project_pitched_event",
]
