"""Bar-level structured evidence for Benny Golson's "Along Came Betty".

Source: New Real Book 2, pp. 7-8, user-provided private scorebook scan.

The public repository stores chart structure, harmony symbols, navigation and
performance instructions. It intentionally does not store the copyrighted
written melody or written trumpet/tenor note payloads.
"""
from __future__ import annotations

from ..score_context import (
    ScorePerformancePhase,
    ScoreSpan,
    StructuredScoreEvidence,
)
from ..scorebooks import SEED_SONG_LOCATORS, ScoreEvidenceKind


ALONG_CAME_BETTY_LOCATOR = next(
    x for x in SEED_SONG_LOCATORS if x.song_id == "score.newreal2.along_came_betty"
)

_HEAD = frozenset({ScorePerformancePhase.HEAD, ScorePerformancePhase.HEAD_OUT})
_SOLO = frozenset({ScorePerformancePhase.SOLO})
_SOLO_LAST = frozenset({ScorePerformancePhase.SOLO_LAST})
_SOLOS = frozenset({ScorePerformancePhase.SOLO, ScorePerformancePhase.SOLO_LAST})
_PROV7 = ("scorebook:newreal2:p7", "manual-visual-review")
_PROV8 = ("scorebook:newreal2:p8", "manual-visual-review")


def _e(kind, value, page, start_bar=None, end_bar=None, *, confidence=.99, phases=frozenset(), provenance=None):
    return StructuredScoreEvidence(
        kind=kind,
        value=value,
        span=ScoreSpan(page=page, start_bar=start_bar, end_bar=end_bar),
        confidence=confidence,
        provenance=provenance or (_PROV7 if page == 7 else _PROV8),
        phases=phases,
    )


def _chord(page: int, bar: int, symbol: str, *, confidence: float = .99):
    return _e(ScoreEvidenceKind.CHORD, symbol, page, bar, bar, confidence=confidence)


# Song-global bar numbering is used here:
# A=1-16, B=17-24, C=25-34, D=35-50, coda=51+.
# This numbering is an ingestion coordinate, not a claim about playback order.
ALONG_CAME_BETTY_EVIDENCE = (
    _e(ScoreEvidenceKind.TITLE, "Along Came Betty", 7),
    _e(ScoreEvidenceKind.STYLE, "medium swing", 7),
    _e(ScoreEvidenceKind.TEMPO, "quarter=110", 7),
    _e(ScoreEvidenceKind.METER, "4/4", 7),
    _e(ScoreEvidenceKind.FORM, "sections A-B-C-D with D.S. al Coda navigation", 7),
    _e(ScoreEvidenceKind.FORM, "solo on form ABC", 7, phases=_SOLOS),

    _e(ScoreEvidenceKind.SECTION, "A", 7, 1, 16),
    _e(ScoreEvidenceKind.SECTION, "B", 7, 17, 24),
    _e(ScoreEvidenceKind.SECTION, "C", 7, 25, 34),
    _e(ScoreEvidenceKind.SECTION, "D", 8, 35, 50),
    _e(ScoreEvidenceKind.SECTION, "Coda", 8, 51, 53, confidence=.96),

    # Written material versus improvised passes over the same ABC bars.
    _e(ScoreEvidenceKind.WRITTEN_MELODY, "written head melody", 7, 1, 34, phases=_HEAD),
    _e(ScoreEvidenceKind.SOLO_INDICATION, "open solo on form ABC", 7, 1, 34, phases=_SOLOS),
    _e(ScoreEvidenceKind.WRITTEN_PART, "D: written trumpet and tenor ensemble parts", 8, 35, 50, phases=_HEAD),
    _e(
        ScoreEvidenceKind.WRITTEN_PART_POLICY,
        "D is a written ensemble section; use the instrument-specific written part when available",
        8, 35, 50, phases=_HEAD, confidence=.97,
    ),

    # Navigation and ending instructions are stored literally rather than
    # converted into a guessed full playback route.
    _e(ScoreEvidenceKind.NAVIGATION, "Segno at section B", 7, 17, 17),
    _e(ScoreEvidenceKind.NAVIGATION, "To Coda marker at Eb7#9", 7, 32, 32),
    _e(ScoreEvidenceKind.NAVIGATION, "Use Till Cue ending", 7, 33, 34, phases=_SOLO),
    _e(ScoreEvidenceKind.NAVIGATION, "Take On Cue ending to last solo", 7, 33, 34, phases=_SOLO_LAST),
    _e(ScoreEvidenceKind.NAVIGATION, "D.S. al Coda", 8, 50, 50),
    _e(ScoreEvidenceKind.NAVIGATION, "Coda", 8, 51, 53),

    # Printed arrangement instructions.
    _e(ScoreEvidenceKind.ARRANGEMENT_NOTE, "Chords in parentheses are used for the head only.", 8),
    _e(ScoreEvidenceKind.ARRANGEMENT_NOTE, "No kicks during solos.", 8, phases=_SOLOS),
    _e(ScoreEvidenceKind.ARRANGEMENT_NOTE, "Piano lays out at A during solos.", 8, phases=_SOLOS),

    # A
    _chord(7, 1, "Bbm7"),
    _chord(7, 2, "Bm7 E7"),
    _chord(7, 3, "Bbm7"),
    _chord(7, 4, "Bm7 E7"),
    _chord(7, 5, "Amaj7"),
    _chord(7, 6, "G#7"),
    _chord(7, 7, "Gmaj7"),
    _chord(7, 8, "F#7"),
    _chord(7, 9, "F#m7"),
    _chord(7, 10, "Gm7 C7"),
    _chord(7, 11, "F#m7"),
    _chord(7, 12, "Gm7 C7"),
    _chord(7, 13, "Fmaj7"),
    _chord(7, 14, "A7"),
    _chord(7, 15, "Dm7"),
    _chord(7, 16, "G7 Cm9", confidence=.96),

    # B
    _chord(7, 17, "Cm9"),
    _chord(7, 18, "F7"),
    _chord(7, 19, "Am7b5 D7"),
    _chord(7, 20, "Gm7"),
    _chord(7, 21, "Gm7/F"),
    _chord(7, 22, "Em7b5 A7"),
    _chord(7, 23, "Fm7"),
    _chord(7, 24, "Bb7"),

    # C
    _chord(7, 25, "Bbm7"),
    _chord(7, 26, "Bm7 E7"),
    _chord(7, 27, "Bbm7"),
    _chord(7, 28, "Bm7 E7"),
    _chord(7, 29, "Cm7b5"),
    _chord(7, 30, "F7"),
    _chord(7, 31, "Bbm7b5"),
    _chord(7, 32, "Eb7#9"),
    _chord(7, 33, "Abmaj7"),
    _chord(7, 34, "Bm7 E7"),

    # D mirrors the written A-like harmonic cycle on p.8.
    _chord(8, 35, "Bbm7"),
    _chord(8, 36, "Bm7 E7"),
    _chord(8, 37, "Bbm7"),
    _chord(8, 38, "Bm7 E7"),
    _chord(8, 39, "Amaj7"),
    _chord(8, 40, "G#7"),
    _chord(8, 41, "Gmaj7"),
    _chord(8, 42, "F#7"),
    _chord(8, 43, "F#m7"),
    _chord(8, 44, "Gm7 C7"),
    _chord(8, 45, "F#m7"),
    _chord(8, 46, "Gm7 C7"),
    _chord(8, 47, "Fmaj7"),
    _chord(8, 48, "A7"),
    _chord(8, 49, "Dm7"),
    _chord(8, 50, "G7 Cm9", confidence=.96),

    # Coda harmony visible on p.8. The final Abmaj7 is sustained across the
    # notated ending; exact written note payload remains private source data.
    _chord(8, 51, "Eb7#9"),
    _e(ScoreEvidenceKind.CHORD, "Abmaj7", 8, 52, 53, confidence=.97),
)


def along_came_betty_evidence():
    return ALONG_CAME_BETTY_EVIDENCE
