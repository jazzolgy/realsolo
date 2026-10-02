"""Instrument notation profiles for practical readable-score output.

Profiles describe how an already-decided musical part is normally written.
They do not generate notes and they do not replace Shared Core instrument
semantics.  The purpose is practical transcription/part preparation:
clefs, written transposition, staff count, and advisory written range.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ClefSpec:
    sign: str
    line: int
    octave_change: int = 0

    def validate(self) -> None:
        if self.sign not in {"G", "F", "C", "percussion"}:
            raise ValueError("unsupported clef sign")
        if self.sign != "percussion" and not 1 <= self.line <= 5:
            raise ValueError("clef line must be within 1..5")


@dataclass(frozen=True)
class TranspositionSpec:
    """Written-to-sounding transposition used by MusicXML.

    chromatic_semitones is added to written pitch to obtain sounding pitch.
    Examples: Bb clarinet = -2, F horn = -7.
    """

    chromatic_semitones: int = 0
    diatonic_steps: int | None = None
    octave_change: int = 0


@dataclass(frozen=True)
class InstrumentProfile:
    profile_id: str
    display_name: str
    family: str
    staff_count: int
    clefs: tuple[ClefSpec, ...]
    transposition: TranspositionSpec = TranspositionSpec()
    written_low_midi: int | None = None
    written_high_midi: int | None = None
    aliases: tuple[str, ...] = ()

    def validate(self) -> None:
        if not self.profile_id or not self.display_name or not self.family:
            raise ValueError("instrument profile identity is required")
        if self.staff_count <= 0:
            raise ValueError("staff_count must be positive")
        if len(self.clefs) != self.staff_count:
            raise ValueError("clef count must match staff_count")
        for clef in self.clefs:
            clef.validate()
        if (
            self.written_low_midi is not None
            and self.written_high_midi is not None
            and self.written_low_midi > self.written_high_midi
        ):
            raise ValueError("written range is inverted")


TREBLE = ClefSpec("G", 2)
BASS = ClefSpec("F", 4)
ALTO = ClefSpec("C", 3)
TENOR = ClefSpec("C", 4)
PERCUSSION = ClefSpec("percussion", 3)


_PROFILES = (
    InstrumentProfile(
        "piano", "Piano", "keyboard", 2, (TREBLE, BASS),
        aliases=("grand_piano", "acoustic_piano"),
    ),
    InstrumentProfile(
        "violin", "Violin", "strings", 1, (TREBLE,),
        written_low_midi=55, written_high_midi=103,
    ),
    InstrumentProfile(
        "viola", "Viola", "strings", 1, (ALTO,),
        written_low_midi=48, written_high_midi=91,
    ),
    InstrumentProfile(
        "cello", "Violoncello", "strings", 1, (BASS,),
        written_low_midi=36, written_high_midi=81,
        aliases=("violoncello",),
    ),
    InstrumentProfile(
        "double_bass", "Double Bass", "strings", 1, (BASS,),
        TranspositionSpec(octave_change=-1),
        written_low_midi=36, written_high_midi=84,
        aliases=("upright_bass", "contrabass"),
    ),
    InstrumentProfile(
        "flute", "Flute", "woodwind", 1, (TREBLE,),
        written_low_midi=60, written_high_midi=96,
    ),
    InstrumentProfile(
        "oboe", "Oboe", "woodwind", 1, (TREBLE,),
        written_low_midi=58, written_high_midi=91,
    ),
    InstrumentProfile(
        "clarinet_bb", "Clarinet in Bb", "woodwind", 1, (TREBLE,),
        TranspositionSpec(chromatic_semitones=-2, diatonic_steps=-1),
        written_low_midi=52, written_high_midi=96,
        aliases=("bb_clarinet", "clarinet_in_bb", "clarinet"),
    ),
    InstrumentProfile(
        "bassoon", "Bassoon", "woodwind", 1, (BASS,),
        written_low_midi=34, written_high_midi=77,
    ),
    InstrumentProfile(
        "horn_f", "Horn in F", "brass", 1, (TREBLE,),
        TranspositionSpec(chromatic_semitones=-7, diatonic_steps=-4),
        written_low_midi=41, written_high_midi=84,
        aliases=("f_horn", "french_horn", "horn"),
    ),
    InstrumentProfile(
        "trumpet_bb", "Trumpet in Bb", "brass", 1, (TREBLE,),
        TranspositionSpec(chromatic_semitones=-2, diatonic_steps=-1),
        written_low_midi=54, written_high_midi=86,
        aliases=("bb_trumpet", "trumpet"),
    ),
    InstrumentProfile(
        "trombone", "Trombone", "brass", 1, (BASS,),
        written_low_midi=40, written_high_midi=72,
    ),
    InstrumentProfile(
        "tuba", "Tuba", "brass", 1, (BASS,),
        written_low_midi=28, written_high_midi=60,
    ),
    InstrumentProfile(
        "tenor_sax", "Tenor Saxophone", "woodwind", 1, (TREBLE,),
        TranspositionSpec(chromatic_semitones=-14, diatonic_steps=-8),
        aliases=("tenor_saxophone",),
    ),
    InstrumentProfile(
        "alto_sax", "Alto Saxophone", "woodwind", 1, (TREBLE,),
        TranspositionSpec(chromatic_semitones=-9, diatonic_steps=-5),
        aliases=("alto_saxophone",),
    ),
    InstrumentProfile(
        "drum_set", "Drum Set", "percussion", 1, (PERCUSSION,),
        aliases=("drums",),
    ),
)

for _profile in _PROFILES:
    _profile.validate()

_BY_NAME: dict[str, InstrumentProfile] = {}
for _profile in _PROFILES:
    _BY_NAME[_profile.profile_id] = _profile
    for _alias in _profile.aliases:
        _BY_NAME[_alias] = _profile


def resolve_instrument_profile(name: str) -> InstrumentProfile | None:
    return _BY_NAME.get(name.strip().lower())


def all_instrument_profiles() -> tuple[InstrumentProfile, ...]:
    return _PROFILES


def written_range_warning(
    profile: InstrumentProfile,
    nominal_written_midi: int,
) -> str | None:
    """Return an advisory range warning, never a hard rejection."""

    profile.validate()
    if (
        profile.written_low_midi is not None
        and nominal_written_midi < profile.written_low_midi
    ):
        return "below advisory written range"
    if (
        profile.written_high_midi is not None
        and nominal_written_midi > profile.written_high_midi
    ):
        return "above advisory written range"
    return None
