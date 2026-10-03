"""Pitch and enharmonic spelling for notation.

This module does not infer harmony.  It consumes pitch evidence plus optional
notation context (for example key-signature preference supplied by Shared Core)
and produces auditable spelling candidates.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from math import isclose

from .events import PerformedPitch


class AccidentalPreference(str, Enum):
    AUTO = "auto"
    SHARPS = "sharps"
    FLATS = "flats"
    NATURALS = "naturals"


@dataclass(frozen=True)
class PitchSpellingContext:
    key_fifths: int | None = None
    accidental_preference: AccidentalPreference = AccidentalPreference.AUTO
    explicit_pitch_class_spellings: tuple[tuple[int, str], ...] = ()

    def validate(self) -> None:
        if self.key_fifths is not None and not -7 <= self.key_fifths <= 7:
            raise ValueError("key_fifths must be within -7..7")
        seen: set[int] = set()
        for pc, spelling in self.explicit_pitch_class_spellings:
            if not 0 <= pc <= 11:
                raise ValueError("explicit spelling pitch class must be 0..11")
            if pc in seen:
                raise ValueError("duplicate explicit pitch-class spelling")
            if not spelling:
                raise ValueError("explicit spelling may not be empty")
            seen.add(pc)

    def explicit_for(self, pitch_class: int) -> str | None:
        for pc, spelling in self.explicit_pitch_class_spellings:
            if pc == pitch_class:
                return spelling
        return None


@dataclass(frozen=True)
class WrittenPitch:
    step: str
    alter: int
    octave: int

    def validate(self) -> None:
        if self.step not in {"A", "B", "C", "D", "E", "F", "G"}:
            raise ValueError("written pitch step must be A..G")
        if not -2 <= self.alter <= 2:
            raise ValueError("initial spelling supports accidentals within double-flat/sharp")

    @property
    def accidental(self) -> str:
        return {
            -2: "bb",
            -1: "b",
            0: "",
            1: "#",
            2: "x",
        }[self.alter]

    @property
    def name(self) -> str:
        return f"{self.step}{self.accidental}{self.octave}"


@dataclass(frozen=True)
class PitchSpellingCandidate:
    written_pitch: WrittenPitch
    cost: float
    confidence: float
    reasons: tuple[str, ...] = ()

    def validate(self) -> None:
        self.written_pitch.validate()
        if self.cost < 0:
            raise ValueError("spelling cost may not be negative")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("spelling confidence must be within 0..1")


_NATURAL_PC = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}

# Common readable enharmonics.  More exotic spellings can later be proposed by
# harmony-aware context without changing this module's contract.
_PC_SPELLINGS: dict[int, tuple[tuple[str, int], ...]] = {
    0: (("C", 0), ("B", 1), ("D", -2)),
    1: (("C", 1), ("D", -1), ("B", 2)),
    2: (("D", 0), ("C", 2), ("E", -2)),
    3: (("D", 1), ("E", -1), ("F", -2)),
    4: (("E", 0), ("F", -1), ("D", 2)),
    5: (("F", 0), ("E", 1), ("G", -2)),
    6: (("F", 1), ("G", -1), ("E", 2)),
    7: (("G", 0), ("F", 2), ("A", -2)),
    8: (("G", 1), ("A", -1)),
    9: (("A", 0), ("G", 2), ("B", -2)),
    10: (("A", 1), ("B", -1), ("C", -2)),
    11: (("B", 0), ("C", -1), ("A", 2)),
}


def _parse_explicit_spelling(text: str) -> tuple[str, int]:
    if not text:
        raise ValueError("empty spelling")
    step = text[0].upper()
    suffix = text[1:]
    alters = {"": 0, "#": 1, "##": 2, "x": 2, "b": -1, "bb": -2}
    if step not in _NATURAL_PC or suffix not in alters:
        raise ValueError(f"unsupported explicit spelling: {text}")
    return step, alters[suffix]


def _preference(context: PitchSpellingContext) -> AccidentalPreference:
    if context.accidental_preference is not AccidentalPreference.AUTO:
        return context.accidental_preference
    if context.key_fifths is None or context.key_fifths == 0:
        return AccidentalPreference.NATURALS
    return (
        AccidentalPreference.SHARPS
        if context.key_fifths > 0
        else AccidentalPreference.FLATS
    )


def _written_pitch(midi_note: int, step: str, alter: int) -> WrittenPitch:
    natural_pc = _NATURAL_PC[step]
    numerator = midi_note - natural_pc - alter
    if numerator % 12:
        raise ValueError("spelling does not match MIDI pitch")
    octave = numerator // 12 - 1
    pitch = WrittenPitch(step, alter, octave)
    pitch.validate()
    return pitch


def spelling_candidates(
    pitch: PerformedPitch,
    context: PitchSpellingContext = PitchSpellingContext(),
) -> tuple[PitchSpellingCandidate, ...]:
    """Return ordered enharmonic candidates for a nominal performed pitch."""

    pitch.validate()
    context.validate()
    if pitch.nominal_midi is None:
        raise ValueError("written pitch spelling requires nominal_midi evidence")

    midi_note = round(pitch.nominal_midi)
    if not isclose(pitch.nominal_midi, midi_note, abs_tol=.5):
        raise ValueError("nominal_midi is too far from a semitone center")
    pc = midi_note % 12
    preference = _preference(context)

    spellings = list(_PC_SPELLINGS[pc])
    explicit = context.explicit_for(pc)
    if explicit is not None:
        explicit_pair = _parse_explicit_spelling(explicit)
        if explicit_pair not in spellings:
            spellings.insert(0, explicit_pair)

    results: list[PitchSpellingCandidate] = []
    for step, alter in spellings:
        wp = _written_pitch(midi_note, step, alter)
        cost = .08 * abs(alter)
        reasons: list[str] = []

        if abs(alter) >= 2:
            cost += .28
            reasons.append("double accidental is less readable")

        if preference is AccidentalPreference.SHARPS:
            cost += .18 if alter < 0 else 0.0
            if alter > 0:
                reasons.append("matches sharp-side notation context")
        elif preference is AccidentalPreference.FLATS:
            cost += .18 if alter > 0 else 0.0
            if alter < 0:
                reasons.append("matches flat-side notation context")
        elif preference is AccidentalPreference.NATURALS and alter == 0:
            cost -= .04
            reasons.append("natural spelling preferred when otherwise neutral")

        if explicit is not None and (step, alter) == _parse_explicit_spelling(explicit):
            cost -= .35
            reasons.append("explicit Shared Core / human spelling preference")

        cost = max(0.0, cost)
        confidence = max(0.0, min(1.0, 1.0 - cost))
        candidate = PitchSpellingCandidate(wp, cost, confidence, tuple(reasons))
        candidate.validate()
        results.append(candidate)

    results.sort(key=lambda x: (x.cost, -x.confidence, x.written_pitch.name))
    return tuple(results)


def preferred_spelling(
    pitch: PerformedPitch,
    context: PitchSpellingContext = PitchSpellingContext(),
) -> PitchSpellingCandidate:
    candidates = spelling_candidates(pitch, context)
    if not candidates:
        raise ValueError("no pitch spelling candidates")
    return candidates[0]
