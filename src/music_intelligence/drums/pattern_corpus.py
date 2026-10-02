"""Source-aware symbolic drum pattern corpus.

The corpus may store literal pedagogical/transcribed patterns as references.
Runtime code never schedules an entire stored pattern blindly: it queries only
what is relevant at the current decision instant, then returns to listen/re-plan.

Rights metadata is intentionally explicit.  A pattern being present for
research/reference does not imply permission for model training,
redistribution, or commercial use.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .model import DrumVoice, GestureRole


class PatternUse(str, Enum):
    REFERENCE = "reference"
    RESEARCH = "research"
    TRAINING = "training"
    EVALUATION = "evaluation"
    REDISTRIBUTION = "redistribution"


@dataclass(frozen=True)
class PatternHit:
    """One symbolic hit inside a stored pattern.

    onset_beats is relative to the pattern origin.  duration is intentionally
    omitted for now because most drum strikes are onset-dominant events.
    """
    onset_beats: float
    voice: DrumVoice
    velocity_class: str = "medium"
    articulation: str = "normal"


@dataclass(frozen=True)
class SourceRights:
    source_title: str
    source_page: str
    source_kind: str = "uploaded_reference"
    license_note: str = "rights_not_verified_for_training_or_redistribution"
    allowed_uses: frozenset[PatternUse] = frozenset(
        {PatternUse.REFERENCE, PatternUse.RESEARCH}
    )


@dataclass(frozen=True)
class StoredDrumPattern:
    pattern_id: str
    name: str
    role: GestureRole
    length_beats: float
    hits: tuple[PatternHit, ...]
    tags: frozenset[str]
    source: SourceRights
    exact_source_pattern: bool = True
    notes: str = ""

    def validate(self) -> None:
        if self.length_beats <= 0:
            raise ValueError("pattern length must be positive")
        for hit in self.hits:
            if not 0.0 <= hit.onset_beats < self.length_beats:
                raise ValueError(
                    f"{self.pattern_id}: onset {hit.onset_beats} outside pattern"
                )


# Initial literal/source-derived seed corpus.
#
# These are deliberately compact examples whose notation/description can be
# recovered from the uploaded references.  They are not treated as universal
# jazz grammar; they remain source-attributed examples.
PATTERN_CORPUS: tuple[StoredDrumPattern, ...] = (
    StoredDrumPattern(
        pattern_id="riley_bop_ride_basic_01",
        name="Bop ride basic",
        role=GestureRole.TIME,
        length_beats=2.0,
        hits=(
            PatternHit(0.0, DrumVoice.RIDE, "medium", "tip"),
            PatternHit(1.0, DrumVoice.RIDE, "medium", "tip"),
            # Final swung note is stored canonically as 2/3 of beat 2.
            # Runtime timing adaptation may move it according to tempo.
            PatternHit(1.0 + 2.0 / 3.0, DrumVoice.RIDE, "medium", "tip"),
        ),
        tags=frozenset({"jazz", "bop", "ride", "time_playing", "swing"}),
        source=SourceRights(
            source_title="John Riley - The Art of Bop Drumming",
            source_page="pp. 7-9",
        ),
        notes="Source-derived ride-cymbal time pattern; runtime may tempo-warp the swung offbeat.",
    ),
    StoredDrumPattern(
        pattern_id="riley_bop_ride_hihat_24_01",
        name="Bop ride with pedal hi-hat 2 and 4",
        role=GestureRole.TIME,
        length_beats=4.0,
        hits=(
            PatternHit(0.0, DrumVoice.RIDE, "medium", "tip"),
            PatternHit(1.0, DrumVoice.RIDE, "medium", "tip"),
            PatternHit(1.0, DrumVoice.CLOSED_HIHAT, "soft", "chick"),
            PatternHit(1.0 + 2.0 / 3.0, DrumVoice.RIDE, "medium", "tip"),
            PatternHit(2.0, DrumVoice.RIDE, "medium", "tip"),
            PatternHit(3.0, DrumVoice.RIDE, "medium", "tip"),
            PatternHit(3.0, DrumVoice.CLOSED_HIHAT, "soft", "chick"),
            PatternHit(3.0 + 2.0 / 3.0, DrumVoice.RIDE, "medium", "tip"),
        ),
        tags=frozenset({"jazz", "bop", "ride", "pedal_hihat", "2_and_4"}),
        source=SourceRights(
            source_title="John Riley - The Art of Bop Drumming",
            source_page="pp. 7-9",
        ),
        notes="Literal pedagogical time-playing example with pedal hi-hat on 2 and 4.",
    ),
    StoredDrumPattern(
        pattern_id="spagnardi_upbeat2_two_eighth_setup",
        name="Two-eighth fill into upbeat of 2",
        role=GestureRole.SETUP,
        length_beats=1.0,
        hits=(
            PatternHit(0.0, DrumVoice.SNARE, "medium", "setup"),
            PatternHit(0.5, DrumVoice.SNARE, "medium", "setup"),
        ),
        tags=frozenset({"big_band", "fill", "setup", "upbeat_figure"}),
        source=SourceRights(
            source_title="Ron Spagnardi - Big Band Drumming: Understanding Fills",
            source_page="p. 1",
        ),
        notes="Source describes two eighth notes immediately prior to an upbeat-of-2 figure.",
    ),
    StoredDrumPattern(
        pattern_id="spagnardi_upbeat3_triplet_setup",
        name="Triplet fill into upbeat of 3",
        role=GestureRole.SETUP,
        length_beats=1.0,
        hits=(
            PatternHit(0.0, DrumVoice.SNARE, "medium", "setup"),
            PatternHit(1.0 / 3.0, DrumVoice.SNARE, "medium", "setup"),
            PatternHit(2.0 / 3.0, DrumVoice.SNARE, "medium", "setup"),
        ),
        tags=frozenset({"big_band", "fill", "triplet", "setup", "upbeat_figure"}),
        source=SourceRights(
            source_title="Ron Spagnardi - Big Band Drumming: Understanding Fills",
            source_page="p. 2",
        ),
        notes="Source describes a triplet fill immediately before the upbeat-of-3 figure.",
    ),
    StoredDrumPattern(
        pattern_id="spagnardi_upbeat4_four16_setup",
        name="Four-sixteenth fill into upbeat of 4",
        role=GestureRole.SETUP,
        length_beats=1.0,
        hits=(
            PatternHit(0.0, DrumVoice.SNARE, "medium", "setup"),
            PatternHit(0.25, DrumVoice.SNARE, "medium", "setup"),
            PatternHit(0.5, DrumVoice.SNARE, "medium", "setup"),
            PatternHit(0.75, DrumVoice.SNARE, "medium", "setup"),
        ),
        tags=frozenset({"big_band", "fill", "sixteenth", "setup", "upbeat_figure"}),
        source=SourceRights(
            source_title="Ron Spagnardi - Big Band Drumming: Understanding Fills",
            source_page="p. 2",
        ),
        notes="Source describes four 16th notes leading into the upbeat-of-4 figure.",
    ),
)


def get_pattern(pattern_id: str) -> StoredDrumPattern:
    for pattern in PATTERN_CORPUS:
        if pattern.pattern_id == pattern_id:
            pattern.validate()
            return pattern
    raise KeyError(pattern_id)


def patterns_with_tags(*tags: str) -> tuple[StoredDrumPattern, ...]:
    required = set(tags)
    out = tuple(p for p in PATTERN_CORPUS if required.issubset(p.tags))
    for pattern in out:
        pattern.validate()
    return out


def hits_at_current_position(
    pattern: StoredDrumPattern,
    position_beats: float,
    *,
    tolerance_beats: float = 0.04,
) -> tuple[PatternHit, ...]:
    """Return only source-pattern hits relevant *now*.

    This is the key boundary: the corpus stores whole patterns, while runtime
    realization exposes only the current slice.  Future hits remain reference
    knowledge, not a committed sequence.
    """
    pattern.validate()
    phase = position_beats % pattern.length_beats
    return tuple(
        hit for hit in pattern.hits
        if abs(hit.onset_beats - phase) <= tolerance_beats
    )
