"""v1.37 modal / nonfunctional harmony state.

The source-grounded part of this module follows the uploaded Berklee modal
harmony material:
- modal identity depends on a modal tonic and characteristic tone(s);
- bass anchoring strongly affects tonic/non-tonic perception;
- quartal structures reduce the automatic major/minor pull of tertian voicing;
- a modal tritone is not inherently an error when the modal tonic anchors it.

The nonfunctional-continuity portion is an architectural abstraction for UMR.
It records how a moving sonority remains intelligible without forcing a
tonic/predominant/dominant explanation.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Iterable, Sequence


class HarmonicOrientation(str, Enum):
    TONAL_FUNCTIONAL = "tonal_functional"
    MODAL = "modal"
    HYBRID = "hybrid"
    NONFUNCTIONAL = "nonfunctional"
    UNKNOWN = "unknown"


class VerticalTopology(str, Enum):
    TERTIAN = "tertian"
    QUARTAL = "quartal"
    SECUNDAL = "secundal"
    MIXED = "mixed"
    OPEN = "open"
    UNKNOWN = "unknown"


class ContinuityMechanism(str, Enum):
    PEDAL_ANCHOR = "pedal_anchor"
    MODAL_TONIC_ANCHOR = "modal_tonic_anchor"
    CHARACTERISTIC_TONE = "characteristic_tone"
    COMMON_TONE = "common_tone"
    VOICE_LEADING = "voice_leading"
    PARALLEL_SHAPE = "parallel_shape"
    INTERVAL_STRUCTURE = "interval_structure"
    MELODIC_ANCHOR = "melodic_anchor"
    BASS_ANCHOR = "bass_anchor"
    REGISTERAL_CONTINUITY = "registeral_continuity"
    NONE = "none"


@dataclass(frozen=True)
class ModalState:
    tonic_pc: int
    mode_name: str
    characteristic_pcs: frozenset[int] = frozenset()
    current_bass_pc: int | None = None
    pedal_pc: int | None = None
    pedal_strength: float = 0.0
    vertical_topology: VerticalTopology = VerticalTopology.UNKNOWN
    functional_pull: float = 0.0
    observed_pitch_classes: frozenset[int] = frozenset()
    confidence: float = 1.0
    provenance: tuple[str, ...] = ()

    def validate(self) -> None:
        if not 0 <= self.tonic_pc <= 11:
            raise ValueError("tonic_pc must be in 0..11")
        for pc in self.characteristic_pcs | self.observed_pitch_classes:
            if not 0 <= pc <= 11:
                raise ValueError("pitch classes must be in 0..11")
        if self.current_bass_pc is not None and not 0 <= self.current_bass_pc <= 11:
            raise ValueError("current_bass_pc must be in 0..11")
        if self.pedal_pc is not None and not 0 <= self.pedal_pc <= 11:
            raise ValueError("pedal_pc must be in 0..11")
        for value, name in (
            (self.pedal_strength, "pedal_strength"),
            (self.functional_pull, "functional_pull"),
            (self.confidence, "confidence"),
        ):
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{name} must be within 0..1")

    @property
    def tonic_in_bass(self) -> bool:
        return self.current_bass_pc == self.tonic_pc

    @property
    def tonic_pedal(self) -> bool:
        return self.pedal_pc == self.tonic_pc and self.pedal_strength > 0.0


@dataclass(frozen=True)
class ModalAssessment:
    orientation: HarmonicOrientation
    modal_anchor_strength: float
    tonic_perception: float
    characteristic_tone_support: float
    tonal_pull_risk: float
    continuity_mechanisms: tuple[ContinuityMechanism, ...]
    reasons: tuple[str, ...]


@dataclass(frozen=True)
class NonfunctionalState:
    """Context for coherence without requiring tonal-function labels."""

    continuity_mechanisms: frozenset[ContinuityMechanism]
    structural_anchor_pcs: frozenset[int] = frozenset()
    previous_pitch_classes: frozenset[int] = frozenset()
    current_pitch_classes: frozenset[int] = frozenset()
    shape_signature: tuple[int, ...] = ()
    previous_shape_signature: tuple[int, ...] = ()
    bass_pc: int | None = None
    previous_bass_pc: int | None = None
    confidence: float = 1.0
    provenance: tuple[str, ...] = ()

    def validate(self) -> None:
        for pc in (
            self.structural_anchor_pcs
            | self.previous_pitch_classes
            | self.current_pitch_classes
        ):
            if not 0 <= pc <= 11:
                raise ValueError("pitch classes must be in 0..11")
        for pc in (self.bass_pc, self.previous_bass_pc):
            if pc is not None and not 0 <= pc <= 11:
                raise ValueError("bass pitch class must be in 0..11")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be within 0..1")


@dataclass(frozen=True)
class NonfunctionalAssessment:
    coherence: float
    common_tone_count: int
    anchor_count: int
    shape_preserved: bool
    bass_continuity: float
    mechanisms_present: tuple[ContinuityMechanism, ...]
    reasons: tuple[str, ...]


def assess_modal_state(state: ModalState) -> ModalAssessment:
    state.validate()
    anchor = 0.15
    tonic_perception = 0.20
    characteristic = 0.0
    risk = state.functional_pull
    mechanisms: list[ContinuityMechanism] = []
    reasons: list[str] = []

    if state.tonic_in_bass:
        anchor += .42
        tonic_perception += .48
        mechanisms.extend((
            ContinuityMechanism.MODAL_TONIC_ANCHOR,
            ContinuityMechanism.BASS_ANCHOR,
        ))
        reasons.append("modal tonic is present in bass")

    if state.tonic_pedal:
        anchor += .22 * state.pedal_strength
        tonic_perception += .15 * state.pedal_strength
        mechanisms.append(ContinuityMechanism.PEDAL_ANCHOR)
        reasons.append("tonic pedal reinforces modal center")

    characteristic_hits = len(state.characteristic_pcs & state.observed_pitch_classes)
    if state.characteristic_pcs:
        characteristic = min(
            1.0,
            characteristic_hits / len(state.characteristic_pcs)
        )
    if characteristic_hits:
        anchor += .16 * characteristic
        mechanisms.append(ContinuityMechanism.CHARACTERISTIC_TONE)
        reasons.append("characteristic modal tone is audible")

    if state.vertical_topology is VerticalTopology.QUARTAL:
        risk -= .18
        anchor += .08
        mechanisms.append(ContinuityMechanism.INTERVAL_STRUCTURE)
        reasons.append("quartal topology reduces automatic tertian tonal pull")
    elif state.vertical_topology is VerticalTopology.TERTIAN:
        risk += .12
        reasons.append("tertian topology can strengthen major/minor tonal reading")

    if state.current_bass_pc is not None and not state.tonic_in_bass:
        tonic_perception -= .20
        reasons.append("non-tonic bass weakens immediate modal-tonic perception")

    anchor = min(1.0, max(0.0, anchor))
    tonic_perception = min(1.0, max(0.0, tonic_perception))
    risk = min(1.0, max(0.0, risk))

    if anchor >= .45 and risk <= .55:
        orientation = HarmonicOrientation.MODAL
    elif anchor >= .30 and risk > .55:
        orientation = HarmonicOrientation.HYBRID
    elif risk > .70:
        orientation = HarmonicOrientation.TONAL_FUNCTIONAL
    else:
        orientation = HarmonicOrientation.UNKNOWN

    # Preserve order while removing duplicates.
    ordered = tuple(dict.fromkeys(mechanisms))
    return ModalAssessment(
        orientation,
        anchor,
        tonic_perception,
        characteristic,
        risk,
        ordered,
        tuple(reasons),
    )


def assess_nonfunctional_state(state: NonfunctionalState) -> NonfunctionalAssessment:
    """Measure continuity without inventing a tonal-function analysis.

    This is a project-level abstraction. It does not claim that every listed
    mechanism comes from one textbook taxonomy.
    """
    state.validate()
    common = len(state.previous_pitch_classes & state.current_pitch_classes)
    anchors = len(state.structural_anchor_pcs & state.current_pitch_classes)
    shape_preserved = (
        bool(state.shape_signature)
        and state.shape_signature == state.previous_shape_signature
    )
    bass_continuity = 0.0
    if state.bass_pc is not None and state.previous_bass_pc is not None:
        distance = min(
            (state.bass_pc - state.previous_bass_pc) % 12,
            (state.previous_bass_pc - state.bass_pc) % 12,
        )
        bass_continuity = max(0.0, 1.0 - distance / 6.0)

    score = 0.0
    present: list[ContinuityMechanism] = []
    reasons: list[str] = []

    if common:
        score += min(.28, common * .10)
        present.append(ContinuityMechanism.COMMON_TONE)
        reasons.append("common-tone continuity")

    if anchors:
        score += min(.28, anchors * .12)
        present.append(ContinuityMechanism.MELODIC_ANCHOR)
        reasons.append("structural anchor tone retained")

    if shape_preserved:
        score += .24
        present.extend((
            ContinuityMechanism.PARALLEL_SHAPE,
            ContinuityMechanism.INTERVAL_STRUCTURE,
        ))
        reasons.append("interval shape preserved across sonority motion")

    if bass_continuity >= .65:
        score += .12 * bass_continuity
        present.append(ContinuityMechanism.BASS_ANCHOR)
        reasons.append("bass continuity")

    for mechanism in state.continuity_mechanisms:
        if mechanism is not ContinuityMechanism.NONE:
            score += .035
            present.append(mechanism)

    return NonfunctionalAssessment(
        coherence=min(1.0, score),
        common_tone_count=common,
        anchor_count=anchors,
        shape_preserved=shape_preserved,
        bass_continuity=bass_continuity,
        mechanisms_present=tuple(dict.fromkeys(present)),
        reasons=tuple(reasons),
    )


def modal_characteristic_pc(tonic_pc: int, scale_degree: int, alteration: int = 0) -> int:
    """Utility for storing characteristic scale degrees without scale lock-in."""
    if not 0 <= tonic_pc <= 11:
        raise ValueError("tonic_pc must be in 0..11")
    major_offsets = (0, 2, 4, 5, 7, 9, 11)
    if not 1 <= scale_degree <= 7:
        raise ValueError("scale_degree must be within 1..7")
    return (tonic_pc + major_offsets[scale_degree - 1] + alteration) % 12
