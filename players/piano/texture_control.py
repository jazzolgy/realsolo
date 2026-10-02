"""Independent harmonic-color, attack-density, and macro-arc controls.

The 1000-pass Bill Evans study showed that rich harmony and frequent attacks are not
the same dimension. This module provides the capability without encoding an
Evans-specific density curve.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .comping import PianoCompingCandidate


class HarmonicColorLevel(str, Enum):
    THIN = "thin"
    MODERATE = "moderate"
    RICH = "rich"
    ALTERED = "altered"


class AttackDensityLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class MacroArcPhase(str, Enum):
    OPEN = "open"
    DEVELOP = "develop"
    INTENSIFY = "intensify"
    PEAK = "peak"
    RELEASE = "release"
    STABLE = "stable"


@dataclass(frozen=True)
class PianoTextureIntent:
    harmonic_color: HarmonicColorLevel = HarmonicColorLevel.MODERATE
    attack_density: AttackDensityLevel = AttackDensityLevel.MEDIUM
    macro_arc: MacroArcPhase = MacroArcPhase.STABLE
    confidence: float = 0.5

    def validate(self) -> None:
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be within 0..1")


@dataclass(frozen=True)
class PianoTextureIntentBias:
    score_delta: float
    components: dict[str,float]
    reasons: tuple[str,...]


def _tension_count(candidate: "PianoCompingCandidate") -> int:
    if candidate.realization is None:
        return 0
    return int(candidate.realization.event.annotations.get("tension_count",0))


def evaluate_texture_intent(
    candidate: "PianoCompingCandidate",
    intent: PianoTextureIntent,
) -> PianoTextureIntentBias:
    """Bias one current candidate; never schedule future comping."""
    intent.validate()
    score=0.0
    components={}
    reasons=[]

    def add(key,value,reason):
        nonlocal score
        value *= intent.confidence
        score += value
        components[key]=components.get(key,0.0)+value
        reasons.append(reason)

    silent=candidate.realization is None
    tension_count=_tension_count(candidate)
    action=getattr(candidate.action_type,"value",candidate.action_type)
    role=getattr(candidate.role,"value",candidate.role)

    # Harmonic-color axis.
    if intent.harmonic_color is HarmonicColorLevel.THIN:
        if silent or tension_count==0:
            add("texture_color_fit",.055,"thin color intent favors sparse structural material")
        elif tension_count>=2:
            add("texture_color_overrich",-0.06,"two-tension color exceeds current thin texture intent")
    elif intent.harmonic_color is HarmonicColorLevel.MODERATE:
        if tension_count==1:
            add("texture_color_fit",.055,"one-tension color matches moderate harmonic richness")
    elif intent.harmonic_color is HarmonicColorLevel.RICH:
        if tension_count>=2:
            add("texture_color_fit",.075,"two-tension voicing matches rich harmonic color intent")
        elif tension_count==0 and not silent:
            add("texture_color_underfilled",-0.035,"plain sounding voicing underfills rich color intent")
    elif intent.harmonic_color is HarmonicColorLevel.ALTERED:
        tags=set(candidate.tags)
        if candidate.realization is not None:
            tags |= set(candidate.realization.event.tags)
            roles={v.harmonic_role or "" for v in candidate.realization.event.voices}
        else:
            roles=set()
        if roles & {"b9","#9","#11","b13"} or "high_tension" in tags:
            add("texture_altered_fit",.075,"explicit altered color matches altered harmonic intent")

    # Attack-density axis. This is deliberately independent from tension count.
    if intent.attack_density is AttackDensityLevel.LOW:
        if silent:
            add("texture_attack_fit",.08,"low attack-density intent supports space")
        elif action=="sustained_support":
            add("texture_attack_fit",.055,"sustain creates harmony without repeated attacks")
        elif action in {"punctuation","response"}:
            add("texture_attack_excess",-0.025,"punctuation/response may exceed a low attack-density intent")
    elif intent.attack_density is AttackDensityLevel.MEDIUM:
        if action in {"sparse_support","response","sustained_support"}:
            add("texture_attack_fit",.035,"current gesture matches medium attack-density intent")
    elif intent.attack_density is AttackDensityLevel.HIGH:
        if action in {"punctuation","response"} or role in {"build","answer","fill"}:
            add("texture_attack_fit",.055,"active current gesture matches high attack-density intent")
        elif silent:
            add("texture_attack_underactive",-0.035,"silence underfills a high attack-density moment")

    # Macro arc: longer-horizon context biases the present only.
    if intent.macro_arc is MacroArcPhase.OPEN:
        if silent or action in {"sparse_support","sustained_support"}:
            add("macro_arc_fit",.04,"opening arc favors space and lighter current weight")
        if role=="build":
            add("macro_arc_conflict",-0.04,"build role is premature in an opening arc")
    elif intent.macro_arc is MacroArcPhase.DEVELOP:
        if role in {"support","answer","punctuate"}:
            add("macro_arc_fit",.035,"development arc supports conversational elaboration")
    elif intent.macro_arc is MacroArcPhase.INTENSIFY:
        if role in {"build","punctuate","answer"}:
            add("macro_arc_fit",.05,"intensifying arc supports a more active current gesture")
    elif intent.macro_arc is MacroArcPhase.PEAK:
        if not silent and role in {"build","punctuate","anchor","answer"}:
            add("macro_arc_fit",.055,"peak arc tolerates stronger present-moment activity")
    elif intent.macro_arc is MacroArcPhase.RELEASE:
        if silent or role in {"release","lay_out"} or action=="sustained_support":
            add("macro_arc_fit",.055,"release arc favors space or sustained reduction")
        if role=="build":
            add("macro_arc_conflict",-0.055,"build role conflicts with release arc")

    return PianoTextureIntentBias(score,components,tuple(reasons))
