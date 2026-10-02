# RealSolo Chord Chart Runtime Contract

## Purpose

RealSolo's chord chart is a live performance view, not an independent harmony
engine and not a separate song-form interpreter.

The live path is:

Shared Harmony / Form
-> ChordChart
-> Shared Core Form Cursor
-> ChordChartPosition
-> ChordChartRenderModel
-> ChordChartViewport
-> platform UI

## Ownership

Shared Harmony owns harmonic truth.

Shared Core owns the authoritative executed-form location, including repeat /
ending / D.S. / Coda traversal once CCR-TRANSCRIBE-002 is adopted.

Transcribe / Notation owns:

- chord-chart representation;
- chord-symbol spelling and transposition;
- notation shorthand display;
- current/next chord projection from a supplied position;
- renderer-neutral rows/cells;
- viewport and auto-follow planning;
- chart quality audit.

The platform UI owns pixels, typography, gestures, animation and scrolling.

## Render model

The renderer-neutral model exposes:

- title and meter;
- rows of measures;
- chord labels and beat positions;
- section / rehearsal labels;
- repeat / ending / navigation marks;
- active measure;
- active chord;
- next chord preview;
- current section;
- effective transposition.

Transposition is applied to rendered chord labels, not merely shown as metadata.
Enharmonic policy may respell the rendered chart without changing sounding pitch.

## Viewport / auto-follow

Viewport planning exposes:

- active row;
- rows currently visible;
- rows prefetched around the viewport;
- follow target row;
- whether the active row advanced;
- whether the section changed.

The viewport planner does not scroll the screen. A mobile, tablet or desktop
client chooses how to animate to the supplied follow target.

## Default presentation

A practical starting layout is four measures per row with two rows visible on a
tablet-sized performance view. These are presentation defaults, not musical
rules. Clients may choose different row widths while consuming the same chart.

## Important invariant

The UI must never independently infer harmony or execute form navigation.
It renders a projection of authoritative musical state.
