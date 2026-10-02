"""Phase-aware score -> Shared Solo -> Sax realization bridge."""
from __future__ import annotations
from dataclasses import dataclass
import re

from music_intelligence.corpus.score_context import ScoreContextSnapshot
from music_intelligence.corpus.score_harmony import harmonic_frame_from_score
from music_intelligence.reasoning.ensemble_complementarity import EnsembleComplementarityEvidence
from music_intelligence.reasoning.feasibility import FeasibilityAssessment
from music_intelligence.reasoning.groove_context import GrooveFeel, GrooveTemporalContext, build_groove_context
from music_intelligence.reasoning.harmonic_turn import derive_harmonic_turn_context
from music_intelligence.reasoning.solo_expression import expression_from_solo_context
from music_intelligence.reasoning.solo_runtime import SoloTickPlan, build_solo_tick
from music_intelligence.reasoning.turn_taking import TurnTakingEvidence

from .feasibility import assess_sax_solo_feasibility
from .physical import SaxPhysicalConstraints
from .score_context import SaxScoreActivity, interpret_score_context
from .solo_realizer import SaxSoloRealization, SaxSoloRealizer, SaxSoloRealizerContext

@dataclass(frozen=True)
class SaxChartRealizationCandidate:
    realization: SaxSoloRealization
    feasibility: FeasibilityAssessment

@dataclass(frozen=True)
class SaxChartTickPlan:
    score_snapshot: ScoreContextSnapshot
    groove: GrooveTemporalContext | None
    shared_solo: SoloTickPlan | None
    realizations: tuple[SaxChartRealizationCandidate, ...]
    requires_written_material: bool = False
    reasons: tuple[str, ...] = ()

_TEMPO_RE=re.compile(r"(?:quarter|q|♩)\s*=\s*([0-9]+(?:\.[0-9]+)?)",re.I)
_METER_RE=re.compile(r"^\s*(\d+)\s*/\s*(\d+)\s*$")

def groove_from_score(snapshot: ScoreContextSnapshot)->GrooveTemporalContext|None:
    if snapshot.tempo is None or snapshot.meter is None:return None
    tm=_TEMPO_RE.search(snapshot.tempo); mm=_METER_RE.match(snapshot.meter)
    if tm is None or mm is None:return None
    style=" ".join(snapshot.style).lower()
    feel=GrooveFeel.SWING if "swing" in style else GrooveFeel.BOSSA if "bossa" in style else GrooveFeel.FUNK if "funk" in style else GrooveFeel.STRAIGHT if ("straight" in style or "even 8" in style) else GrooveFeel.UNKNOWN
    return build_groove_context(feel,tempo_bpm=float(tm.group(1)),meter_numerator=int(mm.group(1)),meter_denominator=int(mm.group(2)),confidence=snapshot.confidence,provenance=("structured_score_groove",))

def build_sax_chart_tick(
    score_snapshot: ScoreContextSnapshot,*,
    next_score_snapshot: ScoreContextSnapshot|None=None,
    previous_pitch_midi:int|None=None,
    turn:TurnTakingEvidence=TurnTakingEvidence(),
    complementarity:EnsembleComplementarityEvidence=EnsembleComplementarityEvidence(),
    phrase_position:float=0.0, phrase_maturity:float=0.0, tension:float=0.0,
    duration_beats:float=.5, low_midi:int=50, high_midi:int=94,
)->SaxChartTickPlan:
    policy=interpret_score_context(score_snapshot)
    groove=groove_from_score(score_snapshot)
    frame=harmonic_frame_from_score(score_snapshot,next_snapshot=next_score_snapshot,phrase_position=phrase_position,tension=tension)
    if policy.activity in {SaxScoreActivity.HEAD_WRITTEN,SaxScoreActivity.WRITTEN_SOLO,SaxScoreActivity.WRITTEN_PART}:
        return SaxChartTickPlan(score_snapshot,groove,None,(),True,("written material active",))
    if policy.activity is not SaxScoreActivity.OPEN_SOLO or frame.expected is None:
        return SaxChartTickPlan(score_snapshot,groove,None,(),False,("no explicit open solo with one resolved chord",))
    hturn=derive_harmonic_turn_context(frame,turn)
    plan=build_solo_tick(
        harmonic_frame=frame,harmonic_turn=hturn,turn=turn,complementarity=complementarity,
        current_pitch_class=None if previous_pitch_midi is None else previous_pitch_midi%12,
        target_pitch_classes=frozenset() if frame.next_expected is None else frame.next_expected.pitch_classes,
        structural_pitch_classes=frame.expected.pitch_classes,duration_beats=duration_beats,
    )
    expr=expression_from_solo_context(tension=tension,phrase_maturity=phrase_maturity,ensemble_activity=max(complementarity.low_harmonic_support,complementarity.percussive_support))
    rc=SaxSoloRealizerContext(low_midi=low_midi,high_midi=high_midi,previous_pitch_midi=previous_pitch_midi,beat_position_beats=score_snapshot.position.beat or 0.,groove=groove)
    constraints=SaxPhysicalConstraints(low_midi,high_midi,7,20,16.)
    out=[]
    realizer=SaxSoloRealizer()
    for spec in plan.candidates:
        r=realizer.realize(spec,expr,rc)
        a=assess_sax_solo_feasibility(r,previous_pitch_midi=previous_pitch_midi,notes_since_breath=0,beats_since_breath=0.,constraints=constraints)
        out.append(SaxChartRealizationCandidate(r,a))
    return SaxChartTickPlan(score_snapshot,groove,plan,tuple(out),False,("immediate candidates only",))
