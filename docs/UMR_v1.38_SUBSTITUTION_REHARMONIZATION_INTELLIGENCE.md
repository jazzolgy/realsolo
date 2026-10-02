# UMR v1.38 — Substitution / Reharmonization Intelligence

## Source basis

The uploaded jazz-theory material explicitly treats secondary and substitute
dominants, key-of-the-moment, interpolated chords, and modal interchange as
advanced harmonic topics. It also stresses that jazz study must remain tied to
aural practice, transcription, and keyboard voice-leading rather than theory
alone.

v1.38 therefore uses those categories as a source-grounded taxonomy, while the
actual scoring model is a project-level UMR abstraction.

## Core decision

A reharmonization is not valid merely because it appears in a substitution
table.

The engine asks what musical relation makes the substitute intelligible:
- target preservation
- function preservation
- common tone
- guide-tone / voice-leading path
- bass logic
- melody compatibility
- modal borrowing relation
- interval-shape continuity
- narrative tension

A proposal may deliberately weaken one axis if another relation is strong
enough. The result is graded continuity/risk, not legal/illegal.

## Reharmonization kinds

v1.38 can represent:
- secondary dominant
- substitute dominant
- extended dominant
- modal interchange
- interpolation
- key-of-the-moment
- diminished approach
- chromatic approach
- pedal reinterpretation
- nonfunctional color

These labels do not force one scale or one voicing.

## Tritone substitute

The helper for substitute dominants computes the tritone-related dominant root
and preserves the intended target as explicit metadata.

The important semantic relation is not the root shift by itself. The proposal
still has to be assessed for destination, function, common tones, melody,
voice-leading, and bass behavior.

## Relationship to v1.35–v1.37

v1.35 provides functional-family hypotheses and expected/actual resolution.

v1.36 provides detailed concrete voice-leading when actual voices are known.

v1.37 provides modal and nonfunctional orientation plus continuity mechanisms.

v1.38 sits above those layers as a proposal/evaluation object for changing the
harmonic surface while keeping the reasons auditable.

## Runtime invariant

Reharmonization generates a current harmonic alternative or soft route. It does
not prewrite a future chord sequence.

A live player still follows:

Perceive -> infer current/future harmony -> consider reharmonization affordance
-> generate current instrument candidate -> commit one immediate action
-> listen/re-plan.
