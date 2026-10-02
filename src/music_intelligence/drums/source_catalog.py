"""Catalog of uploaded drum sources and their role in the AI Drummer corpus.

The catalog separates source study status from permission status.  A source can
be deeply studied for reference/research without being approved for training or
redistribution.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class SourcePriority(str, Enum):
    CORE = "core"
    SUPPORTING = "supporting"
    VOCABULARY = "vocabulary"
    REFERENCE = "reference"


@dataclass(frozen=True)
class DrumSource:
    source_id: str
    title: str
    priority: SourcePriority
    domains: frozenset[str]
    contribution: frozenset[str]
    status: str
    notes: str = ""


DRUM_SOURCES: tuple[DrumSource, ...] = (
    DrumSource(
        "riley_art_bop",
        "John Riley - The Art of Bop Drumming",
        SourcePriority.CORE,
        frozenset({"jazz", "bebop", "swing"}),
        frozenset({
            "time_playing", "ride", "comping", "independence", "soloing",
            "brushes", "shuffle", "two_feel", "3_4", "samba", "12_8",
            "mambo", "uptempo",
        }),
        "active_ingestion",
        "Primary bebop grammar and source-pattern reference.",
    ),
    DrumSource(
        "riley_beyond_bop",
        "John Riley - Beyond Bop Drumming",
        SourcePriority.CORE,
        frozenset({"jazz", "post_bop", "modern_jazz"}),
        frozenset({
            "broken_time", "three_voice_comping", "counterpoint",
            "uptempo", "implied_time", "metric_modulation", "soloing",
            "listening_interaction",
        }),
        "active_ingestion",
        "Primary modern-jazz interaction/time-playing reference.",
    ),
    DrumSource(
        "moses_drum_wisdom",
        "Bob Moses - Drum Wisdom",
        SourcePriority.CORE,
        frozenset({"jazz", "improvisation", "conceptual"}),
        frozenset({
            "internal_hearing", "play_off_something", "groove_canon",
            "8_8_concept", "organic_drumming", "movement", "singing",
            "ensemble_reference",
        }),
        "active_ingestion",
        "Decision philosophy and internal-hearing model.",
    ),
    DrumSource(
        "plainfield_advanced_concepts",
        "Kim Plainfield - Advanced Concepts",
        SourcePriority.CORE,
        frozenset({"contemporary", "funk", "jazz", "latin", "afro_cuban"}),
        frozenset({
            "independence", "funk", "linear_funk", "swing_triplets",
            "samba", "baiao", "afro_cuban", "mozambique", "guaguanco",
            "mambo", "songo", "6_8", "rhythmic_concepts",
        }),
        "active_ingestion",
        "Broad style grammar and coordination/orchestration reference.",
    ),
    DrumSource(
        "badness_drum_programming",
        "Ray F. Badness - Drum Programming: A Complete Guide to Program and Think Like a Drummer",
        SourcePriority.SUPPORTING,
        frozenset({"popular", "programming", "straight"}),
        frozenset({
            "kick_snare", "hihat", "ride", "toms", "fills", "cymbals",
            "arrangement", "physical_feasibility", "midi_programming",
        }),
        "active_ingestion",
        "Useful for realistic kit orchestration and programmed-drum baseline.",
    ),
    DrumSource(
        "spagnardi_big_band_fills",
        "Ron Spagnardi - Big Band Drumming: Understanding Fills",
        SourcePriority.CORE,
        frozenset({"jazz", "big_band"}),
        frozenset({"setup", "fill", "ensemble_figure", "upbeat_figure"}),
        "pattern_seeded",
        "Fills are treated as preparation for ensemble figures, not decoration.",
    ),
    DrumSource(
        "holland_complete_fills",
        "Jim Holland - The Complete Book of Drum Fills",
        SourcePriority.SUPPORTING,
        frozenset({"popular", "fills"}),
        frozenset({
            "one_beat_fill", "half_measure_fill", "one_measure_fill",
            "two_measure_fill", "eighth", "sixteenth", "triplet",
            "sticking", "space", "crash_choice",
        }),
        "active_ingestion",
    ),
    DrumSource(
        "prushko_legendary_rock_fills",
        "Jason Prushko - 100 Legendary Rock Drum Fills",
        SourcePriority.VOCABULARY,
        frozenset({"rock", "fills"}),
        frozenset({"kit_motion", "hand_to_foot", "space", "broken_up_beats", "odd_time"}),
        "cataloged",
    ),
    DrumSource(
        "atkinson_unreel",
        "Marc Atkinson - The UnReel Drum Book / Vinnie Colaiuta",
        SourcePriority.CORE,
        frozenset({"fusion", "jazz", "odd_meter", "advanced"}),
        frozenset({
            "transcription", "rhythm_scale", "subdivision", "polyrhythm",
            "odd_meter", "soloing", "five_against_four", "seven_against_four",
        }),
        "cataloged",
        "High-value later source for advanced rhythmic/LegendProfile study.",
    ),
    DrumSource(
        "berklee_notation",
        "Berklee - Drum Set Notation in Finale",
        SourcePriority.REFERENCE,
        frozenset({"notation", "midi"}),
        frozenset({"pas_notation", "percussion_map", "midi_mapping", "voice_stems"}),
        "schema_reference",
    ),
    DrumSource(
        "drum_encyclopedia",
        "Dave Atkinson - Encyclopedia of Drum Terms",
        SourcePriority.REFERENCE,
        frozenset({"terminology"}),
        frozenset({"style_terms", "technique_terms", "instrument_terms"}),
        "reference",
    ),
    DrumSource(
        "yamaha_drum_fundamentals",
        "Drum Fundamentals",
        SourcePriority.SUPPORTING,
        frozenset({"fundamentals", "technique"}),
        frozenset({"stick_control", "syncopation", "accent", "double_time", "independence", "rudiments"}),
        "cataloged",
    ),
    DrumSource(
        "feldstein_snare_soloist",
        "Drum Soloist (Snare and Bass Drum)",
        SourcePriority.VOCABULARY,
        frozenset({"snare", "bass_drum", "solo"}),
        frozenset({"rudimental_vocabulary", "dynamics", "sticking"}),
        "cataloged",
    ),
    DrumSource(
        "tuke_tutorials",
        "Kevin Tuck - Drum Tutorials",
        SourcePriority.VOCABULARY,
        frozenset({"reading", "fundamentals"}),
        frozenset({"rhythm_reading", "rests", "subdivision"}),
        "cataloged",
    ),
    DrumSource(
        "beginning_snare",
        "Brendan Van Epps - Snare Drum",
        SourcePriority.VOCABULARY,
        frozenset({"snare", "fundamentals"}),
        frozenset({"notation", "sticking", "reading"}),
        "cataloged",
    ),
    DrumSource(
        "alfred_method",
        "Alfred's Drum Method Book 1",
        SourcePriority.VOCABULARY,
        frozenset({"snare", "fundamentals"}),
        frozenset({"rudiments", "reading", "technique", "meter"}),
        "cataloged",
    ),
    DrumSource(
        "modern_drummer_mag",
        "Modern Drummer article collection",
        SourcePriority.VOCABULARY,
        frozenset({"mixed", "fills", "independence"}),
        frozenset({"artist_patterns", "fills", "soloing", "independence"}),
        "cataloged",
    ),
    DrumSource(
        "drum_book_patterns",
        "Uploaded drum-book pattern collection",
        SourcePriority.VOCABULARY,
        frozenset({"mixed"}),
        frozenset({"pattern_vocabulary"}),
        "cataloged",
        "Image-heavy source; exact pattern transcription is queued.",
    ),
)


def sources_for_domain(domain: str) -> tuple[DrumSource, ...]:
    return tuple(s for s in DRUM_SOURCES if domain in s.domains)


def sources_for_contribution(contribution: str) -> tuple[DrumSource, ...]:
    return tuple(s for s in DRUM_SOURCES if contribution in s.contribution)
