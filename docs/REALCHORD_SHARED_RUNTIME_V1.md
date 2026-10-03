# RealChord Shared Runtime v1

## Role

RealChord is the shared harmonic/form chart layer for the entire RealSolo
platform. Ensemble, Score/Transcription, AI Player, instrument agents,
Composition, Practice/Education and Research all resolve the same stable
`realchord_id` and the same chart/runtime cursor.

## Compatibility rule

The existing raw-ingestion layer keeps source-order numeric ids such as the
current Autumn Leaves identity `realchord_id=96`. Structural normalization
must never silently replace those ids with a new hash/id scheme.

## Pipeline

```text
RealChord raw playlist
  -> realchord_ingestion (stable identity + raw payload)
  -> realchord_parser (bars / sections / Expected Harmony)
  -> RealChordSong
  -> RealChordLibrary shared hub
  -> playback FormGraph
  -> SharedRealChordSessionState
  -> all consumers
```

## Shared consumers

- Ensemble App
- Score / Transcription App
- AI Player
- Piano / Bass / Drums / Sax and future AI musicians
- Composition Assistant
- Practice / Education
- Research / Analysis

Consumers should not maintain their own incompatible chord-chart schema.

## Harmony layers

RealChord supplies **Expected Harmony** only.

- Expected Harmony: chart/form expectation
- Observed Harmony: what the performance actually plays
- Inferred Harmony: interpretation such as substitution, reharmonization,
  tonicization or upper structure

Observed/Inferred Harmony does not overwrite the shared RealChord chart.

## Structural parser

`realchord_parser.py` decodes the chart payload and normalizes:

- measure boundaries
- section markers
- time signatures
- chord symbols and beat positions
- repeat start/end
- first/second endings
- one/two-measure repeat symbols
- Segno / Coda / Fine
- D.C. / D.S. navigation

Non-standard chart-cell layouts receive reduced confidence instead of being
silently treated as exact timing.

## FormGraph / playback timeline

`expand_playback_timeline()` expands the common lead-sheet performance order:

- explicit repeats
- first/second endings
- D.C.
- D.S.
- D.C./D.S. al Fine
- D.C./D.S. al Coda

`source_measure` remains the stored chart bar.
`playback_measure` is the actual expanded order.

Internal repeats are one form traversal; they do **not** increment the solo
chorus. `chorus_index` is session state and advances only when the whole form
is looped again.

## Shared session cursor

Every consumer can share:

```text
realchord_id
playback_measure
source_measure
section
beat
chorus_index
transpose
tempo
style_override
transport
```

This is the common cursor for score highlighting, ensemble transport and AI
Future Harmony/Form Awareness.

## Future Harmony

`future_harmony()` exposes current + look-ahead measures from the expanded
timeline. Slow planning may use this context for phrase arc, cadence and section
planning, while immediate note choice remains responsive to live ensemble
state.

## Data-source tracking

The normalized/shared musical record produced by the new parser contains no
source/provenance tracking fields. Existing raw-ingestion compatibility fields
are left untouched so current research code and stable ids do not break; they
are not propagated into the new shared chart/session payload.

## Adapter compatibility

`song_from_normalized_record()` continues to accept the established shape:

```text
measures[].chords
```

and additionally accepts the canonical corpus shape:

```text
canonical.measures[].expected_harmony
```

This allows existing research code and the new shared parser/runtime to coexist.
