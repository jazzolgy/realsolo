# RealSolo Score Views

## Decision

RealSolo keeps notation display even if a deeper transcription/editor product later ships separately.

RealSolo should expose three score-facing views backed by the same notation engine.

### 1. Chord Chart

Primary lightweight performance view.

Shows chord symbols by bar/beat, section labels, rehearsal marks, repeats, numbered endings, common navigation marks, N.C., current-measure/current-chord highlight, next-chord preview, and chart transposition.

The chart is a musical/form representation, not an implementation of another application's file format.

### 2. Player Part

Readable notation for the current human or AI instrument, using instrument-appropriate clefs/transposition and practical engraving. This covers written melodies, figures, ensemble hits, introductions, endings, arranged passages, and classical parts that cannot be communicated by chord symbols alone.

### 3. Full Score

Optional ensemble overview for arrangement review, education, debugging AI ensemble behavior, and score export. It does not need to be the default live-performance view.

## Live behavior

RealSolo application state supplies transport/form position. The notation engine resolves that position into chart or score presentation state.

For Chord Chart the minimum live flow is:

Transport position -> measure number + beat -> ChordChartPosition -> current section -> active chord -> next chord -> UI highlight.

The visual renderer is separate from the musical ChordChart model so mobile, tablet, and desktop clients can render differently.

## Shared data principle

Chord charts and full notation should share musical references rather than becoming two unrelated representations. Shared Harmony/form may provide the harmonic and structural truth. Transcribe/Notation decides whether to display that truth as a compact ChordChart or a detailed LogicalScore/player part.

The chart must not independently re-infer harmony when Shared Harmony already provides it.

## Product split

Standalone notation product focuses on deep transcription, detailed editing, score cleanup, and printable/exportable score preparation.

RealSolo permanently keeps Chord Chart and Player Part, with Full Score available when useful. RealSolo emphasizes live following/highlighting rather than deep engraving editing.

Both products consume the same notation engine.
