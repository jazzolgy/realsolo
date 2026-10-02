"""Instrument-neutral semantic solo candidate specifications."""
from __future__ import annotations
from dataclasses import dataclass
from music_intelligence.harmony.scale_linear_core import LinearConnectionAffordance,LinearRouteKind
from .solo_grammar import SoloDevelopmentOperation
from .solo_phrase_intent import SoloEntryMode,SoloPhraseIntent

@dataclass(frozen=True)
class SoloCandidateSpec:
    pitch_class:int|None
    duration_beats:float
    onset_offset_beats:float=0.
    tags:frozenset[str]=frozenset()
    source_family:str="generated"
    def validate(self)->None:
        if self.pitch_class is not None and not 0<=self.pitch_class<=11: raise ValueError("pitch_class must be within 0..11")
        if self.duration_beats<=0: raise ValueError("duration_beats must be positive")

def generate_solo_candidate_specs(*,intent:SoloPhraseIntent,linear_affordances:tuple[LinearConnectionAffordance,...]=(),structural_pitch_classes:frozenset[int]=frozenset(),duration_beats:float=.5)->tuple[SoloCandidateSpec,...]:
    intent.validate()
    if duration_beats<=0: raise ValueError("duration_beats must be positive")
    out=[]
    route_tags={
      LinearRouteKind.CHORDAL:{"chord_tone","harmonic_identity"},
      LinearRouteKind.DIATONIC_PASSING:{"passing","connector","diatonic_passing"},
      LinearRouteKind.CHROMATIC_PASSING:{"passing","connector","chromatic_passing"},
      LinearRouteKind.NEIGHBOR:{"neighbor","connector"},
      LinearRouteKind.ENCLOSURE:{"enclosure","connector","directed_target"},
      LinearRouteKind.APPROACH:{"close_approach","connector","directed_target"},
      LinearRouteKind.ANTICIPATION:{"anticipation","next_harmony_target"},
      LinearRouteKind.SCALE_FRAGMENT:{"scale_fragment","connector"},
      LinearRouteKind.ARPEGGIO_FRAGMENT:{"arpeggio_fragment","harmonic_outline"},
      LinearRouteKind.COMMON_TONE:{"common_tone","motif_continuation"},
    }
    for route in linear_affordances:
        route.validate()
        for pc in route.immediate_pitch_classes:
            tags=set(route_tags.get(route.route,set()))|set(route.context_tags)|{f"solo_method:{intent.solo_method.value}"}
            onset=-.125 if intent.entry_mode is SoloEntryMode.PICKUP and route.route in {LinearRouteKind.APPROACH,LinearRouteKind.ANTICIPATION,LinearRouteKind.ENCLOSURE} else 0.
            if intent.solo_method is SoloDevelopmentOperation.DISPLACE: onset+=.125; tags.add("rhythmic_displacement")
            if intent.solo_method is SoloDevelopmentOperation.ANSWER: tags.add("response")
            if onset<0: tags|={"pickup","syncopated_entry"}
            out.append(SoloCandidateSpec(pc,duration_beats,onset,frozenset(tags),f"linear:{route.route.value}"))
    if not linear_affordances:
        for pc in structural_pitch_classes:
            tags={"chord_tone","harmonic_identity",f"solo_method:{intent.solo_method.value}"}
            out.append(SoloCandidateSpec(pc,duration_beats,0.,frozenset(tags),"structural"))
    if intent.solo_method is SoloDevelopmentOperation.ADD_SPACE or intent.entry_mode is SoloEntryMode.HOLD_SPACE or intent.density_direction.value in {"sparse","release"}:
        out.append(SoloCandidateSpec(None,duration_beats,0.,frozenset({"rest","ensemble_space",f"solo_method:{intent.solo_method.value}"}),"space"))
    seen=set(); unique=[]
    for item in out:
        item.validate(); key=(item.pitch_class,item.duration_beats,item.onset_offset_beats,tuple(sorted(item.tags)),item.source_family)
        if key not in seen: seen.add(key); unique.append(item)
    return tuple(unique)
