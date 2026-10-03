# RealChord Shared Runtime v1

## Purpose

RealChord is the shared harmonic/form chart layer for RealSolo.

The same `realchord_id` namespace is consumed by:

- Ensemble App
- Score / Transcription App
- AI Player
- Piano / Bass / Drums / Sax and future AI musicians
- Composition Assistant
- Practice / Education
- Research / Analysis

No consumer maintains a separate copy of the song chart contract.

## Data flow

```text
Playlist export
  -> RealChord Parser
  -> normalized RealChordSong
  -> RealChordLibrary (Shared Hub)
  -> Playback Timeline / FormGraph
  -> SharedRealChordSessionState
  -> all apps and AI musicians
```

## Harmony layering

RealChord remains Expected Harmony only.

- Expected Harmony: chart/form expectation
- Observed Harmony: what a performance actually plays
- Inferred Harmony: musical interpretation such as substitution or reharmonization

Observed or Inferred Harmony never overwrites the RealChord chart automatically.

## Shared chart coordinate

```text
realchord_id
  -> playback_measure
  -> source_measure
  -> section
  -> beat
  -> chord
```

`playback_measure` follows the expanded performance order.
`source_measure` points back to the stored chart measure.

## Parser

`music_intelligence.corpus.realchord_parser` supports the current exported
playlist payload and normalizes:

- song title / composer / style / key
- measure boundaries
- A/B/C/D/V/Intro section markers
- time signature
- chord symbols and beat position
- repeat start / end
- first / second endings
- one-measure / two-measure repeat symbols
- Segno / Coda / Fine / D.C. / D.S. markers

Unusual cell layouts are retained with reduced chord confidence rather than
being promoted to exact timing.

## FormGraph / playback expansion

`expand_playback_timeline()` expands common lead-sheet navigation:

- explicit repeats
- first / second endings
- D.C.
- D.S.
- D.C. al Fine
- D.S. al Fine
- D.C. al Coda
- D.S. al Coda

Internal repeats are part of one form traversal and do not increment
`chorus_index`. Chorus number belongs to the live session because a solo may
loop the entire form any number of times.

## Shared session state

`SharedRealChordSessionState` is the common runtime cursor:

- `realchord_id`
- `playback_measure`
- `source_measure`
- `beat`
- `section`
- `chorus_index`
- `transpose`
- `tempo`
- `style_override`
- `transport`

A score cursor, ensemble transport and every AI musician therefore resolve the
same current bar and the same Future Harmony.

## Future Harmony

`future_harmony()` exposes the current measure plus an N-measure lookahead.
It is suitable for phrase planning, cadence anticipation and section-aware
ensemble behavior while preserving immediate listening/re-planning.

## Source tracking

RealChord musical records intentionally do not carry source/provenance tracking
metadata. Legacy API fields may remain empty where required for compatibility
with older shared coordinate types.

## Compatibility

The existing `song_from_normalized_record()` contract remains backward
compatible with the earlier top-level `measures[].chords` shape and now also
accepts:

```text
canonical.measures[].expected_harmony
```

This lets the parser/canonical corpus, score app and shared runtime converge on
one song model without breaking earlier RealChord integration tests.
