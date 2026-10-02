# UMR v1.54 — Shared Scale & Linear Connection Intelligence

## Decision

The scale engine belongs to Shared Core.

It is not a bass-only theory layer.

Bass, piano, soloist, arranging, transcription, and ensemble research consume
the same semantic connection routes and realize them differently.

## Why not chord -> one scale

RealSolo already treats harmony as plural evidence and affordance rather than a
single compulsory chord-scale mapping.

Therefore the shared engine exposes a contextual ScaleField and immediate
LinearConnectionAffordances.

A ScaleField may contain:
- structural pitch classes explicitly supported by harmony evidence
- local-key pitch classes supplied by Core analysis
- contextual colour pitch classes
- contextual/avoid pitch classes

If local-key evidence is absent, the engine does not invent a seven-note scale
from the chord symbol alone.

## Route vocabulary

Initial shared route vocabulary:
- chordal
- diatonic passing
- chromatic passing / neighbor
- enclosure
- scale fragment
- arpeggio fragment
- common tone
- approach
- anticipation

These are semantic route families, not copied textbook lines.

## Runtime contract

The engine receives:
- current HarmonicFrame
- current pitch class
- explicit target pitch classes
- optional local-key pitch-class field

It returns immediate pitch-class affordances plus route identity, tension and
resolution semantics.

It never returns a frozen future phrase.

Player runtime remains:

Perceive -> Harmonic/Scale Context -> Linear Affordances -> Instrument Grammar
-> Commit one action -> Listen again -> Re-plan.

## Method-book / scorebook learning boundary

Uploaded method books and the nine Real/New Real/Vocal collections are used to
discover and evaluate abstract musical behaviour:
- connection types
- harmonic-rhythm variety
- feel changes
- route density
- contour behaviour
- scale/chord relation
- idiomatic bass realization where explicitly notated

Do not store or reproduce copyrighted melody/lick content as generated assets.
Store abstract features, statistics, provenance, and expert annotations.

## Important scorebook evidence

The scorebooks contain more than chord symbols. They include:
- written feel changes such as two-feel -> in four -> back to two
- bass-specific written parts in some arrangements
- explicit solo/blowing changes
- ballad, swing, bebop, bossa, funk, waltz, modal and modern-harmony examples

Therefore practice should preserve style/section context rather than flatten all
pages into one generic walking-bass dataset.

## Next integration

1. ingest scorebook page/song metadata into Shared Corpus Registry;
2. extract shared harmony/form/style evidence through Transcriber/chart parser;
3. run each song through Scale & Linear Core;
4. let Bass realize and evaluate route usage;
5. aggregate failures back into Shared Core vs Bass-specific grammar changes;
6. repeat across the full nine-book corpus.
