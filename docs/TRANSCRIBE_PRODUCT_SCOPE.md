# Transcribe Product Scope

## Product goal

The notation engine is not intended to reproduce Sibelius, Dorico, or another
full engraving application.

Its job is to make automatic transcription and AI-performer output readable
enough that a musician can rehearse or perform from it with little or no manual
cleanup.

## Quality target

Priority order:

1. correct musical events and score-time rhythm;
2. readable rhythmic spelling, rests, ties, tuplets and beaming;
3. correct pitch spelling and transposing-instrument notation;
4. stable voice/staff assignment;
5. clefs, articulations, dynamics and common technique markings;
6. practical collision avoidance and spacing;
7. clean individual parts and full score;
8. MusicXML interoperability.

Exact optical geometry, font metrics, page-breaking algorithms, publication
house-style controls and exhaustive engraving options are outside the core
product goal.

## Instrument expansion

The system must remain genre-neutral enough to support jazz and classical
instruments.

Initial practical profiles include:

- piano
- violin, viola, cello, double bass
- flute, oboe, Bb clarinet, bassoon
- F horn, Bb trumpet, trombone, tuba
- alto/tenor saxophone
- drum set

Profiles may define normal staff count, clef(s), written-to-sounding
transposition and advisory written range.

Instrument range is a warning/evaluation feature, not a hard rejection. A
professional player may intentionally exceed a nominal range.

## Engraving policy

Sibelius is used as a reference for sensible notation defaults, not as a
feature-completeness target.

We implement an engraving rule only when it materially improves one of:

- reading speed;
- rhythmic clarity;
- voice separation;
- pitch interpretation;
- rehearsal/performance usability;
- export quality.

This scope should prevent engineering time from drifting into features that do
not improve automatic transcription or playable score output.
