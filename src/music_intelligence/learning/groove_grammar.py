"""Explicit shared groove grammar templates.

Templates encode cyclic onset/accent structure, not copyrighted performances.
They are soft references for learning and classification, never hard playback
patterns.
"""
from __future__ import annotations
from dataclasses import dataclass


@dataclass(frozen=True)
class GrooveGrammar:
    grammar_id: str
    family: str
    cycle_beats: float
    subdivisions_per_beat: int
    onset_slots: tuple[int, ...]
    accent_slots: tuple[int, ...] = ()
    role_hint: str = ""

    def validate(self) -> None:
        if not self.grammar_id or not self.family:
            raise ValueError("grammar_id and family are required")
        if self.cycle_beats <= 0 or self.subdivisions_per_beat <= 0:
            raise ValueError("cycle/subdivision must be positive")
        total=int(round(self.cycle_beats*self.subdivisions_per_beat))
        if any(not 0 <= x < total for x in self.onset_slots+self.accent_slots):
            raise ValueError("groove slot outside cycle")


SON_CLAVE_2_3 = GrooveGrammar(
    "salsa.son_clave.2_3","salsa",8.0,4,(0,12,16,22,28),(0,12,16,22,28),"clave",
)
SON_CLAVE_3_2 = GrooveGrammar(
    "salsa.son_clave.3_2","salsa",8.0,4,(0,6,12,16,28),(0,6,12,16,28),"clave",
)
TUMBAO = GrooveGrammar(
    "salsa.tumbao.basic","salsa",4.0,4,(7,12,15),(7,15),"bass_or_conga",
)
MONTUNO = GrooveGrammar(
    "salsa.montuno.syncopated","salsa",4.0,4,(0,3,6,8,11,14),(3,11),"piano",
)
FUNK_16TH = GrooveGrammar(
    "funk.16th_pocket","funk",4.0,4,(0,3,4,6,8,11,12,14),(4,12),"ensemble_pocket",
)
SHUFFLE = GrooveGrammar(
    "swing.shuffle_triplet","shuffle",4.0,3,(0,2,3,5,6,8,9,11),(0,3,6,9),"triplet_swing",
)
SWING_8TH = GrooveGrammar(
    "swing.eighth_triplet_feel","swing",4.0,3,(0,2,3,5,6,8,9,11),(0,3,6,9),"swing",
)
BOSSA = GrooveGrammar(
    "bossa.syncopated_pulse","bossa_nova",4.0,4,(0,3,6,8,11,14),(0,6,11),"guitar_or_piano",
)

DEFAULT_GROOVE_GRAMMARS=(
    SON_CLAVE_2_3,SON_CLAVE_3_2,TUMBAO,MONTUNO,
    FUNK_16TH,SHUFFLE,SWING_8TH,BOSSA,
)


def groove_similarity(observed_density: tuple[float,...], grammar: GrooveGrammar) -> float:
    grammar.validate()
    total=int(round(grammar.cycle_beats*grammar.subdivisions_per_beat))
    if len(observed_density)!=total:
        return 0.0
    active={i for i,v in enumerate(observed_density) if v>0}
    target=set(grammar.onset_slots)
    union=active|target
    inter=active&target
    return len(inter)/len(union) if union else 1.0


def best_matching_grammars(
    density: tuple[float,...],
    *,
    cycle_beats: float,
    subdivisions_per_beat: int,
    limit: int=3,
) -> tuple[tuple[GrooveGrammar,float],...]:
    matches=[]
    for g in DEFAULT_GROOVE_GRAMMARS:
        if g.cycle_beats!=cycle_beats or g.subdivisions_per_beat!=subdivisions_per_beat:
            continue
        matches.append((g,groove_similarity(density,g)))
    matches.sort(key=lambda x:(x[1],x[0].grammar_id),reverse=True)
    return tuple(matches[:max(0,limit)])
