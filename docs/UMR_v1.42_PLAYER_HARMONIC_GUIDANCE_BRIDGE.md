# UMR v1.42 — Player Harmonic Guidance Bridge

## Purpose

v1.41 made the Shared Harmony Core produce current HarmonicActionOptions.
v1.42 connects those options to player candidate evaluation.

The bridge is deliberately not an instrument generator.

Shared Core says:
- stabilize;
- connect;
- color;
- intensify;
- delay resolution;
- reharmonize;
- outside-and-return;
- anticipate.

A player branch decides what those actions mean physically and stylistically.

## Candidate contract

Players expose semantic tags on their current candidates.

Examples:

Sax / monophonic:
- guide_tone
- passing
- altered
- anticipation
- outside
- resolution_path

Piano / polyphonic:
- harmonic_identity
- upper_structure
- quartal_color
- substitute_dominant
- common_tone
- sparse / dense

Bass:
- root
- guide_tone
- chromatic_approach_harmony
- anticipation
- structural_target

Drums are different: most drum events should not receive pitch/harmony scoring.
A later ensemble-role bridge will consume harmonic rhythm, cadence, tension,
section state, and interaction cues rather than pretending drums realize chord
tones.

## Additive evaluation

The bridge adds a harmonic-guidance score component to the player's own
candidate score. It does not replace:
- instrument grammar;
- style / LegendProfile;
- physical feasibility;
- groove / microtiming;
- ensemble responsiveness;
- phrase and narrative logic.

This is important because a harmonically plausible note may still be a poor sax
phrase, a poor piano voicing, or a poor bass choice in the current ensemble.

## Ambiguity

Harmonic ambiguity dampens the strength of the guidance. When Shared Core is
uncertain, the player remains freer and the system can continue listening.

## Runtime invariant

The bridge re-ranks already-generated current candidates.

It does not:
- generate a future solo;
- fix a future voicing sequence;
- write a future bass line;
- prescribe drum patterns.

The runtime remains:

Shared Harmony Reasoning
-> Player candidate generation
-> Player/style/physical evaluation
-> Add harmonic guidance
-> Ensemble evaluation
-> Commit one immediate action
-> Listen/re-plan.
