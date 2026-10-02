"""v1.34 shared jazz harmony intelligence.

This is an instrument-neutral semantic layer between harmony perception and
candidate realization.  It deliberately avoids chord->one-scale lookup.

Expected, observed, and inferred harmony remain distinct evidence streams.
Affordances describe musically available functions/colours/routes, not exact
future notes and not piano voicings.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Iterable


class HarmonySource(str, Enum):
    EXPECTED = "expected"
    OBSERVED = "observed"
    INFERRED = "inferred"


@dataclass(frozen=True)
class HarmonicEvidence:
    source: HarmonySource
    symbol: str | None = None
    root_pc: int | None = None
    pitch_classes: frozenset[int] = frozenset()
    local_key: str | None = None
    function: str | None = None
    confidence: float = 1.0
    provenance: tuple[str, ...] = ()

    def validate(self) -> None:
        if self.root_pc is not None and not 0 <= self.root_pc <= 11:
            raise ValueError("root_pc must be in 0..11")
        if any(not 0 <= pc <= 11 for pc in self.pitch_classes):
            raise ValueError("pitch classes must be in 0..11")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be within 0..1")


@dataclass(frozen=True)
class HarmonicFrame:
    """Current harmonic state with evidence kept explicitly separate."""
    expected: HarmonicEvidence | None = None
    observed: HarmonicEvidence | None = None
    inferred: HarmonicEvidence | None = None
    next_expected: HarmonicEvidence | None = None
    phrase_position: float = 0.0
    tension: float = 0.0
    cadence_state: str = "open"
    tonicization_target: str | None = None

    def validate(self) -> None:
        for item, required in (
            (self.expected, HarmonySource.EXPECTED),
            (self.observed, HarmonySource.OBSERVED),
            (self.inferred, HarmonySource.INFERRED),
            (self.next_expected, HarmonySource.EXPECTED),
        ):
            if item is None:
                continue
            item.validate()
            if item.source != required:
                raise ValueError(f"{required.value} evidence stored in wrong slot")
        if not 0.0 <= self.phrase_position <= 1.0:
            raise ValueError("phrase_position must be within 0..1")
        if not 0.0 <= self.tension <= 1.0:
            raise ValueError("tension must be within 0..1")


class HarmonicIntent(str, Enum):
    STABILIZE = "stabilize"
    CONNECT = "connect"
    COLOR = "color"
    INTENSIFY = "intensify"
    DELAY_RESOLUTION = "delay_resolution"
    REHARMONIZE = "reharmonize"
    OUTSIDE_AND_RETURN = "outside_and_return"
    ANTICIPATE = "anticipate"


@dataclass(frozen=True)
class TensionChoice:
    label: str
    semitones_from_root: int
    role: str = "color"
    exposed_weight: float = 0.0
    requires_resolution: bool = False

    @property
    def pitch_class_offset(self) -> int:
        return self.semitones_from_root % 12


@dataclass(frozen=True)
class HarmonicAffordance:
    """A possible harmonic action, never a compulsory scale or exact line."""
    affordance_id: str
    intent: HarmonicIntent
    harmonic_role: str
    target_roles: tuple[str, ...] = ()
    tension_choices: tuple[TensionChoice, ...] = ()
    continuity_mechanisms: tuple[str, ...] = ()
    context_tags: frozenset[str] = frozenset()
    weight: float = 0.0
    confidence: float = 1.0
    provenance: tuple[str, ...] = ()
    note: str = ""

    def validate(self) -> None:
        if not self.affordance_id:
            raise ValueError("affordance_id is required")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be within 0..1")


def _symbol_tokens(frame: HarmonicFrame) -> str:
    parts = []
    for ev in (frame.inferred, frame.observed, frame.expected):
        if ev and ev.symbol:
            parts.append(ev.symbol.lower())
    return " ".join(parts)


def _function_tokens(frame: HarmonicFrame) -> str:
    parts = []
    for ev in (frame.inferred, frame.observed, frame.expected):
        if ev and ev.function:
            parts.append(ev.function.lower())
    return " ".join(parts)


def build_basic_affordances(frame: HarmonicFrame) -> tuple[HarmonicAffordance, ...]:
    """Return plural harmonic possibilities for the current context.

    This is intentionally a small semantic baseline, not a complete jazz theory
    engine.  The important contract is that multiple compatible choices may
    coexist and later candidate layers decide among them using melody, voice
    leading, style, ensemble state, and narrative.
    """
    frame.validate()
    symbols = _symbol_tokens(frame)
    funcs = _function_tokens(frame)
    out: list[HarmonicAffordance] = []

    out.append(HarmonicAffordance(
        "generic.guide_tone_connection",
        HarmonicIntent.CONNECT,
        "voice_leading",
        target_roles=("3rd", "7th"),
        continuity_mechanisms=("guide_tone_motion", "nearest_structural_target"),
        weight=.22,
        confidence=.95,
        provenance=("shared_jazz_harmony",),
        note="Guide tones remain available without making them compulsory.",
    ))

    dominant = (
        "7" in symbols and "maj7" not in symbols
        or "dominant" in funcs
        or funcs.strip() in {"v", "v7"}
    )
    if dominant:
        out.extend((
            HarmonicAffordance(
                "dominant.stable_identity",
                HarmonicIntent.STABILIZE,
                "dominant_identity",
                target_roles=("3rd", "b7", "root"),
                continuity_mechanisms=("chord_identity", "resolution_target"),
                weight=.20,
                confidence=.96,
                provenance=("shared_jazz_harmony",),
            ),
            HarmonicAffordance(
                "dominant.altered_color",
                HarmonicIntent.INTENSIFY,
                "altered_dominant",
                target_roles=("3rd", "b7", "next_chord_target"),
                tension_choices=(
                    TensionChoice("b9", 13, "altered_color", .08, True),
                    TensionChoice("#9", 15, "altered_color", .08, True),
                    TensionChoice("b13", 20, "altered_color", .06, True),
                ),
                continuity_mechanisms=("directed_resolution", "chromatic_voice_leading"),
                weight=.16,
                confidence=.92,
                provenance=("shared_jazz_harmony", "expert_editorial"),
                note="Altered tones may form chains when harmonic identity and direction remain audible.",
            ),
        ))

    major7 = "maj7" in symbols or "major7" in funcs or "tonic_major" in funcs
    if major7:
        out.append(HarmonicAffordance(
            "major7.color_field",
            HarmonicIntent.COLOR,
            "major_tonic_color",
            target_roles=("3rd", "7th", "9th", "13th"),
            tension_choices=(
                TensionChoice("9", 14, "color", .06, False),
                TensionChoice("13", 21, "color", .05, False),
                TensionChoice("11", 17, "contextual_color", -.12, True),
            ),
            continuity_mechanisms=("stepwise_passing", "enclosure", "suspension_resolution"),
            weight=.10,
            confidence=.90,
            provenance=("shared_jazz_harmony", "expert_editorial"),
            note="Natural 11 is contextual rather than globally forbidden.",
        ))

    minorish = "m7" in symbols or "minor" in funcs
    if minorish:
        out.append(HarmonicAffordance(
            "minor.contextual_color",
            HarmonicIntent.COLOR,
            "minor_color",
            target_roles=("3rd", "5th", "7th"),
            tension_choices=(
                TensionChoice("9", 14, "color", .05, False),
                TensionChoice("11", 17, "color", .05, False),
                TensionChoice("6/13", 21, "context_dependent", 0.0, False),
            ),
            continuity_mechanisms=("voice_leading", "modal_context", "melodic_direction"),
            weight=.08,
            confidence=.88,
            provenance=("shared_jazz_harmony",),
            note="Minor colour depends on local function/key; no one modal scale is compulsory.",
        ))

    if frame.next_expected is not None:
        out.append(HarmonicAffordance(
            "future_harmony.anticipation",
            HarmonicIntent.ANTICIPATE,
            "future_harmony",
            target_roles=("next_chord_guide_tone", "next_chord_structural_tone"),
            continuity_mechanisms=("anticipation", "common_tone", "chromatic_approach"),
            context_tags=frozenset({"future_harmony_known"}),
            weight=.12,
            confidence=.93,
            provenance=("shared_jazz_harmony",),
        ))

    if frame.tension >= .65:
        out.append(HarmonicAffordance(
            "outside.return_path",
            HarmonicIntent.OUTSIDE_AND_RETURN,
            "controlled_outside",
            target_roles=("return_target",),
            continuity_mechanisms=("side_slip", "sequence", "common_tone", "long_range_target"),
            context_tags=frozenset({"high_tension"}),
            weight=.04,
            confidence=.78,
            provenance=("shared_jazz_harmony",),
            note="Outside colour requires an audible departure/return relation.",
        ))

    return tuple(out)


def affordance_ids(items: Iterable[HarmonicAffordance]) -> frozenset[str]:
    return frozenset(x.affordance_id for x in items)
