# RealChord 1350 as Shared Canonical Symbolic Corpus

RealChord is treated as a Shared Core resource, not as a Player-owned chord
database.

The canonical reference coordinate is musical structure first:

```text
realchord_id
+ section
+ measure_in_section
+ measure_in_form
+ beat
+ chorus / occurrence when needed
```

Audio seconds are stored only in a separate alignment object.

## Alignment flow

```text
audio onset_sec
→ beat grid
→ RealChord form alignment
→ canonical musical coordinate
→ harmony / phrase / interaction analysis
```

This makes a timestamp a measurement attached to a musical location rather than
the identity of the location itself.

## Harmony channels

RealChord supplies **Expected Harmony** only.

```text
RealChord chart → Expected Harmony
audio detection → Observed Harmony
reasoning       → Inferred Harmony
```

Substitution, reharmonization, anticipation and performance-specific harmonic
behavior must remain in Observed/Inferred channels. They do not overwrite the
RealChord chart.

## Shared uses

The same coordinate is intended for:

- transcription alignment
- audio/score synchronization
- structural learning comparisons
- chorus-to-chorus comparison
- future-harmony awareness
- form awareness
- phrase/motif evidence
- cross-player ensemble analysis

## Current source

The project source `Jazz 1350.html` contains 1,350 iReal-style song entries.
The ingestion layer preserves each raw chart string and assigns stable
`realchord_id` by source order before structural normalization.

The current source order places Autumn Leaves at `realchord_id=96`, in G minor,
Medium Swing. The canonical quartet benchmark now references `realchord:96`.

## Parser boundary

The ingestion layer and structural parser are separate:

```text
playlist HTML
→ RealChordRawSong
→ chart parser
→ section / measure / repeat / ending / chord events
→ RealChordSong
→ CanonicalMusicalCoordinate
```

Raw chart encoding is always preserved so parser improvements do not destroy
source provenance.
