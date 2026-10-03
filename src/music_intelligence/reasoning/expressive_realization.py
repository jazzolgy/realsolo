"""Shared Expressive Realization Engine.

Owns HOW a selected musical idea should be expressed, not WHAT notes are chosen.

Shared Core outputs perceptual/musical expressive intention:
- intensity/dynamic level
- accent strength
- note-body/sustain intention
- local timing emphasis
- phrase contour
- foreground/background weight

Players translate that intention into instrument-specific controls.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from music_intelligence.reasoning.solo_grammar import SoloDevelopmentOperation


class DynamicContour(str, Enum):
    FLAT="flat"
    RISE="rise"
    FALL="fall"
    RISE_FALL="rise_fall"
    FALL_RISE="fall_rise"
    TERRACED="terraced"
    SUDDEN_DROP="sudden_drop"


class ExpressiveRole(str, Enum):
    FOREGROUND="foreground"
    SUPPORT="support"
    BACKGROUND="background"
    RESPONSE="response"
    RELEASE="release"


@dataclass(frozen=True)
class ExpressionProfile:
    """Source/memory profile attached to a vocabulary or motif identity.

    Values are relative musical tendencies. They are not MIDI velocities.
    """

    profile_id: str
    source_identity: str
    entry_dynamic: float=.45
    peak_position: float=.60
    peak_dynamic: float=.72
    release_dynamic: float=.52
    contour: DynamicContour=DynamicContour.RISE_FALL
    accent_positions: tuple[float,...]=()
    accent_strength: float=.65
    note_body: float=.55
    timing_emphasis: float=0.0
    foreground_weight: float=.65
    confidence: float=1.0
    provenance: tuple[str,...]=()

    def validate(self) -> None:
        if not self.profile_id or not self.source_identity:
            raise ValueError("profile_id and source_identity are required")
        for name in (
            "entry_dynamic","peak_position","peak_dynamic","release_dynamic",
            "accent_strength","note_body","foreground_weight","confidence",
        ):
            value=float(getattr(self,name))
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{name} must be within 0..1")
        if not -.25 <= self.timing_emphasis <= .25:
            raise ValueError("timing_emphasis must be within -.25..+.25 beats")
        if any(not 0.0 <= x <= 1.0 for x in self.accent_positions):
            raise ValueError("accent_positions must be normalized 0..1")


@dataclass(frozen=True)
class ExpressiveContext:
    phrase_position: float=.0
    form_position: float=.0
    tension: float=.0
    ensemble_density: float=.5
    register_position: float=.5
    repetition_index: int=0
    motif_operation: SoloDevelopmentOperation=SoloDevelopmentOperation.STATE
    role: ExpressiveRole=ExpressiveRole.FOREGROUND
    climax_pressure: float=.0
    release_pressure: float=.0
    available_space: float=.5

    def validate(self) -> None:
        for name in (
            "phrase_position","form_position","tension","ensemble_density",
            "register_position","climax_pressure","release_pressure","available_space",
        ):
            value=float(getattr(self,name))
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{name} must be within 0..1")
        if self.repetition_index < 0:
            raise ValueError("repetition_index may not be negative")


@dataclass(frozen=True)
class ExpressiveIntention:
    perceptual_intensity: float
    dynamic_level: float
    accent_strength: float
    note_body: float
    timing_emphasis_beats: float
    phrase_contour: DynamicContour
    foreground_weight: float
    articulation_pressure: float
    brightness_pressure: float
    reasons: tuple[str,...]=()
    provenance: tuple[str,...]=()

    def validate(self) -> None:
        for name in (
            "perceptual_intensity","dynamic_level","accent_strength","note_body",
            "foreground_weight","articulation_pressure","brightness_pressure",
        ):
            value=float(getattr(self,name))
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{name} must be within 0..1")
        if not -.25 <= self.timing_emphasis_beats <= .25:
            raise ValueError("timing emphasis must stay local")


def _clamp(value: float, lo: float=.0, hi: float=1.0) -> float:
    return max(lo,min(hi,float(value)))


def _profile_dynamic(profile: ExpressionProfile | None, position: float) -> tuple[float,DynamicContour]:
    if profile is None:
        return .52, DynamicContour.FLAT

    p=_clamp(position)
    peak=max(.01,min(.99,profile.peak_position))
    if p <= peak:
        t=p/peak
        value=profile.entry_dynamic+(profile.peak_dynamic-profile.entry_dynamic)*t
    else:
        t=(p-peak)/(1.0-peak)
        value=profile.peak_dynamic+(profile.release_dynamic-profile.peak_dynamic)*t
    return _clamp(value),profile.contour


_OPERATION_DYNAMIC_BIAS={
    SoloDevelopmentOperation.STATE: 0.00,
    SoloDevelopmentOperation.REPEAT: 0.01,
    SoloDevelopmentOperation.VARY: 0.04,
    SoloDevelopmentOperation.FRAGMENT: 0.03,
    SoloDevelopmentOperation.EXTEND: 0.06,
    SoloDevelopmentOperation.CONTRACT: -0.03,
    SoloDevelopmentOperation.INVERT: 0.02,
    SoloDevelopmentOperation.SEQUENCE: 0.08,
    SoloDevelopmentOperation.DISPLACE: 0.04,
    SoloDevelopmentOperation.AUGMENT: -0.02,
    SoloDevelopmentOperation.DIMINISH: 0.08,
    SoloDevelopmentOperation.REORCHESTRATE: 0.02,
    SoloDevelopmentOperation.CHANGE_REGISTER: 0.05,
    SoloDevelopmentOperation.ADD_SPACE: -0.12,
    SoloDevelopmentOperation.INTERNAL_REST: -0.15,
    SoloDevelopmentOperation.CONTRAST: 0.00,
    SoloDevelopmentOperation.RECAP: -0.03,
    SoloDevelopmentOperation.RESOLVE: -0.10,
    SoloDevelopmentOperation.TARGET_NEXT_HARMONY: 0.05,
    SoloDevelopmentOperation.ANSWER: 0.01,
}


def realize_expression(
    context: ExpressiveContext,
    *,
    profile: ExpressionProfile | None=None,
) -> ExpressiveIntention:
    """Derive Shared expressive intention for the already-selected idea.

    Relative profile contour is preserved, while absolute intensity adapts to
    current ensemble/tension/form/register/repetition context.
    """

    context.validate()
    if profile is not None:
        profile.validate()

    reasons=[]
    source_dynamic,contour=_profile_dynamic(profile,context.phrase_position)

    dynamic=source_dynamic
    dynamic += .18*(context.tension-.5)
    dynamic += .18*context.climax_pressure
    dynamic -= .16*context.release_pressure

    # Busy ensemble can lower absolute level while preserving relative contour.
    dynamic -= .14*max(0.0,context.ensemble_density-.55)

    # Foreground/background is separate from raw dynamic.
    role_bias={
        ExpressiveRole.FOREGROUND:.08,
        ExpressiveRole.RESPONSE:.03,
        ExpressiveRole.SUPPORT:-.07,
        ExpressiveRole.BACKGROUND:-.13,
        ExpressiveRole.RELEASE:-.10,
    }[context.role]
    dynamic += role_bias

    op_bias=_OPERATION_DYNAMIC_BIAS.get(context.motif_operation,0.0)
    dynamic += op_bias
    if op_bias:
        reasons.append(f"motif operation {context.motif_operation.value} shapes dynamic")

    # Repetition should evolve, not merely get louder. A four-state cycle gives
    # accent relocation / growth / surprise drop.
    rep=context.repetition_index%4
    repetition_dynamic=(0.0,.035,.08,-.11)[rep]
    dynamic += repetition_dynamic
    if context.repetition_index:
        reasons.append("repetition variation changes expression rather than copying it")

    # High register can perceptually project more strongly without requiring
    # proportionally more physical energy.
    register_projection=.08*(context.register_position-.5)
    perceptual=_clamp(dynamic+register_projection)

    accent=(profile.accent_strength if profile is not None else .52)
    accent += .16*context.tension
    accent += (0.0,.08,.14,-.05)[rep]
    if context.motif_operation in {
        SoloDevelopmentOperation.DISPLACE,
        SoloDevelopmentOperation.SEQUENCE,
        SoloDevelopmentOperation.TARGET_NEXT_HARMONY,
    }:
        accent += .08

    body=(profile.note_body if profile is not None else .55)
    if context.motif_operation in {
        SoloDevelopmentOperation.ADD_SPACE,
        SoloDevelopmentOperation.RESOLVE,
        SoloDevelopmentOperation.RECAP,
    }:
        body += .10
    if context.motif_operation is SoloDevelopmentOperation.DIMINISH:
        body -= .12

    timing=(profile.timing_emphasis if profile is not None else 0.0)
    if context.motif_operation is SoloDevelopmentOperation.DISPLACE:
        timing += .025
    if context.role is ExpressiveRole.RESPONSE:
        timing += .010

    foreground=(profile.foreground_weight if profile is not None else .65)
    foreground += {
        ExpressiveRole.FOREGROUND:.20,
        ExpressiveRole.RESPONSE:.08,
        ExpressiveRole.SUPPORT:-.18,
        ExpressiveRole.BACKGROUND:-.28,
        ExpressiveRole.RELEASE:-.12,
    }[context.role]
    foreground -= .10*max(0.0,context.ensemble_density-.65)

    articulation=.42+.28*accent+.14*context.tension
    brightness=.40+.24*context.tension+.12*context.register_position
    if context.role in {ExpressiveRole.SUPPORT,ExpressiveRole.BACKGROUND}:
        brightness -= .10
    if context.release_pressure>.55:
        articulation -= .12
        brightness -= .10

    out=ExpressiveIntention(
        perceptual_intensity=_clamp(perceptual),
        dynamic_level=_clamp(dynamic),
        accent_strength=_clamp(accent),
        note_body=_clamp(body),
        timing_emphasis_beats=max(-.25,min(.25,timing)),
        phrase_contour=contour,
        foreground_weight=_clamp(foreground),
        articulation_pressure=_clamp(articulation),
        brightness_pressure=_clamp(brightness),
        reasons=tuple(reasons),
        provenance=(
            "shared_expressive_realization",
            *((profile.provenance if profile is not None else ())),
        ),
    )
    out.validate()
    return out
