"""Baseline open instrument catalog for RealSolo research.

Research recognition is broader than runtime generation. An instrument can be a
first-class research object before RealSolo has a dedicated player, feasibility
model, articulation grammar, or renderer for it.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class InstrumentCapability(str, Enum):
    RESEARCH = "research"
    GENERATION = "generation"
    RENDER = "render"


@dataclass(frozen=True)
class InstrumentDefinition:
    instrument_id: str
    display_name: str
    family: str
    aliases: tuple[str, ...] = ()
    default_roles: tuple[str, ...] = ()
    seed_articulations: tuple[str, ...] = ()
    capabilities: frozenset[InstrumentCapability] = frozenset({InstrumentCapability.RESEARCH})


BASELINE_INSTRUMENTS: tuple[InstrumentDefinition, ...] = (
    InstrumentDefinition(
        "piano","Piano","keyboard",
        aliases=("acoustic piano","grand piano"),
        default_roles=("comping","solo","melody","inner_voice"),
        seed_articulations=("legato","staccato","accent","pedal"),
        capabilities=frozenset({InstrumentCapability.RESEARCH,InstrumentCapability.GENERATION,InstrumentCapability.RENDER}),
    ),
    InstrumentDefinition(
        "acoustic_bass","Acoustic Bass","strings",
        aliases=("double bass","upright bass","contrabass"),
        default_roles=("walking","pedal","counterline","solo"),
        seed_articulations=("pizzicato","ghost_note","dead_note","legato","accent"),
        capabilities=frozenset({InstrumentCapability.RESEARCH,InstrumentCapability.GENERATION,InstrumentCapability.RENDER}),
    ),
    InstrumentDefinition(
        "drums","Drums","percussion",
        aliases=("drum kit","drumset"),
        default_roles=("timekeeping","comping","fill","solo"),
        seed_articulations=("ride","brush","rimshot","cross_stick","ghost_note"),
        capabilities=frozenset({InstrumentCapability.RESEARCH,InstrumentCapability.GENERATION,InstrumentCapability.RENDER}),
    ),
    InstrumentDefinition(
        "saxophone","Saxophone","woodwind",
        aliases=("sax","tenor sax","alto sax","soprano sax","baritone sax"),
        default_roles=("melody","solo","counterline","ensemble"),
        seed_articulations=("scoop","fall","doit","subtone","bend","vibrato","growl","ghost_note"),
        capabilities=frozenset({InstrumentCapability.RESEARCH,InstrumentCapability.GENERATION,InstrumentCapability.RENDER}),
    ),
    InstrumentDefinition(
        "trumpet","Trumpet","brass",
        aliases=("flugelhorn",),
        default_roles=("melody","solo","counterline","ensemble"),
        seed_articulations=("fall","doit","shake","bend","vibrato","ghost_note"),
    ),
    InstrumentDefinition(
        "guitar","Guitar","strings",
        aliases=("electric guitar","acoustic guitar","jazz guitar"),
        default_roles=("comping","melody","solo","counterline"),
        seed_articulations=("bend","slide","hammer_on","pull_off","palm_mute","harmonic","strum"),
    ),
    InstrumentDefinition(
        "electric_bass","Electric Bass","strings",
        aliases=("bass guitar","electric bass guitar"),
        default_roles=("walking","groove","pedal","counterline","solo"),
        seed_articulations=("fingerstyle","pick","slap","pop","ghost_note","dead_note","slide"),
    ),
    InstrumentDefinition(
        "vocal","Vocal","voice",
        aliases=("voice","singer","vocals"),
        default_roles=("melody","solo","ensemble","background"),
        seed_articulations=("legato","staccato","vibrato","scoop","fall","breath","growl"),
    ),
    InstrumentDefinition(
        "flute","Flute","woodwind",
        aliases=("concert flute","c flute"),
        default_roles=("melody","solo","counterline","ensemble"),
        seed_articulations=("legato","staccato","accent","flutter_tongue","vibrato","breath_attack"),
    ),
)


def normalize_instrument_label(label: str) -> str | None:
    needle=" ".join(label.strip().lower().replace("_"," ").split())
    if not needle:
        return None
    for item in BASELINE_INSTRUMENTS:
        names={item.instrument_id.replace("_"," "),item.display_name.lower(),*(a.lower() for a in item.aliases)}
        if needle in names:
            return item.instrument_id
    return None


def instrument_definition(label: str) -> InstrumentDefinition | None:
    normalized=normalize_instrument_label(label)
    if normalized is None:
        return None
    return next(item for item in BASELINE_INSTRUMENTS if item.instrument_id==normalized)


def is_baseline_instrument(label: str) -> bool:
    return normalize_instrument_label(label) is not None
