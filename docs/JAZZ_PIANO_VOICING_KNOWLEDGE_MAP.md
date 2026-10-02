# Jazz Piano Voicing Knowledge Map v0.1

Status: working knowledge map for the `player/piano` workstream.

Purpose: organize jazz-harmony, voicing, comping, and ensemble knowledge before
encoding detailed Piano Performance Grammar. This document separates:

1. shared musical semantics that belong in Core,
2. piano-specific realization that belongs in `players/piano/`, and
3. open questions that should be filled from professional voicing/harmony/comping
   textbooks and expert annotation.

This is not a finished pedagogy and not a list of hard rules.

---

## 1. Architectural principle

A chord symbol is not a voicing.

The system should distinguish at least:

```
Expected / Observed / Inferred Harmony
        ↓
Harmonic Function / Color Intention
        ↓
Sonority Intent
        ↓
Voicing Constraints
        ↓
Candidate Voice Structures
        ↓
Instrument-specific Realization
        ↓
Immediate Performance Gesture
```

For AI Pianist, the last two stages are piano-specific. The semantic meaning of
the sonority and its voices is shared.

---

## 2. Knowledge domains

### 2.1 Harmonic identity — Core

Questions:

- What harmonic function is active?
- Which tones define chord quality/function?
- Which extensions/tensions are available, expected, altered, or intentionally omitted?
- Is the harmony functional, modal, tonicizing, substitutive, or coloristic?
- What is expected harmony versus what is actually sounding?
- What is the next harmonic destination?

Core concepts:

- root / bass distinction
- 3rd / 7th guide-tone identity
- chord extensions: 9, 11, 13
- altered tensions
- suspension
- omission
- substitution
- tritone substitution
- modal / quartal color
- harmonic tension / release

Working principle:
Root, fifth, guide tones, extensions, and alterations do not have equal semantic
importance. A voicing should preserve or intentionally obscure harmonic identity
according to musical context.

### 2.2 Voice semantics — Core

Already supported by CR-001 and should remain shared:

- voice identity
- pitch / register
- semantic voice order
- physical onset order
- inter-voice spacing
- doubling
- top-note relation
- bass relation
- generic voice-leading
- harmonic role per voice
- orchestration assignment
- articulation / dynamics / local onset offsets
- provenance / confidence

Important distinction:

```
semantic voice order != physical onset order
```

A single immediate sonority may have slightly staggered onsets.

### 2.3 Voicing family — shared semantic label, instrument-specific realization

Potential families to represent without assuming one universal taxonomy:

- shell / guide-tone
- rootless
- close position
- open position
- drop-2
- drop-3
- drop-2-and-4
- spread
- quartal / fourth-based
- cluster
- upper-structure triad
- sus / modal
- hybrid / slash / polychordal structures
- block-chord / harmonized-line structures

Open design question:
Which of these should be first-class Core descriptors versus tags/taxonomy supplied
by style/instrument grammars?

Do not encode every textbook naming convention as a permanent Core class before
cross-source comparison.

---

## 3. Voicing selection variables

A good voicing is contextual. Candidate evaluation should eventually consider the
following dimensions together rather than treating a chord symbol as a lookup key.

### 3.1 Harmonic context — Core

- current function
- expected next harmony
- cadence / turnaround position
- altered dominant direction
- tonicization
- modal duration
- harmonic rhythm
- ambiguity tolerance
- current tension trajectory

### 3.2 Top-line context — Core + Piano

Core:
- melody/top-note target
- voice-leading destination
- whether the top voice is structural, decorative, doubled, or free

Piano:
- whether the pianist must preserve a sung/horn melody
- whether top voice is intentionally projected
- whether the pianist should stay below or away from another soloist

### 3.3 Bass context — Core + Piano

Core:
- actual/expected bass
- root versus inversion
- bass relation to harmony
- ensemble bass activity

Piano:
- bassist present / absent
- whether left hand should omit root
- whether root/10th/spread support is desirable in solo/duo playing
- low-register mud / collision avoidance

Important:
"Jazz pianists omit roots" must not become a hard rule. Root inclusion depends on
ensemble, register, style, pianist, function, and desired sound.

### 3.4 Register and spacing — shared semantics, Piano realization

Shared:
- register span
- adjacent spacing
- voice crossing
- top/bottom density
- open/close relationships

Piano-specific:
- keyboard range
- hand reach
- left/right hand assignment
- register-dependent clarity
- low-interval limits
- physical redistribution between hands

### 3.5 Voice leading — Core

Evaluate transitions, not isolated vertical stacks.

Potential features:

- common-tone retention
- semitone / whole-step motion
- contrary / oblique / similar motion
- guide-tone resolution
- top-line continuity
- bass continuity
- voice crossing
- aggregate motion
- identity-preserving motion
- intentional displacement / planing

The best candidate is not always the one with the least movement. Smoothness is one
variable among direction, color, register trajectory, rhythmic interaction, and
narrative.

---

## 4. Jazz Piano-specific realization grammar

These belong in `players/piano/`.

### 4.1 Hand distribution

Represent:

- LH only
- RH only
- two-hand distributed
- melody + inner voices
- bass + chord
- crossed / overlapping hands when intentional

Evaluation factors:

- physical span
- repeated-note feasibility
- hand crossing
- rapid re-voicing feasibility
- register balance
- independence required by rhythm/articulation

### 4.2 Root handling

Policy should consider:

- bass player present?
- solo piano / duo / trio / larger ensemble?
- root already strongly established?
- inversion or pedal point?
- style/era preference?
- low-register density?
- harmonic ambiguity intentional?

Candidate actions:

- omit root
- include root
- imply root through guide tones / upper structure
- use root as bass only
- double root intentionally

### 4.3 Guide-tone handling

3rd and 7th often carry strong functional identity in seventh-chord harmony.

Potential grammar:

- preserve one or both
- invert their vertical order
- connect by semitone into the next harmony
- omit one when melody/bass/context already supplies identity
- displace for color when harmonic identity remains sufficiently clear

Do not hard-code "3rd + 7th always required."

### 4.4 Extensions and color

Candidate-generation vocabulary:

- 9
- 11 / #11
- 13 / b13
- b9 / #9
- altered fifths
- suspensions
- upper-structure triads
- quartal collections
- clusters

Evaluation must depend on:

- chord function
- melody collision
- style
- register
- current tension
- next resolution
- ensemble density
- desired ambiguity

### 4.5 Upper structures

Represent upper structure as structure, not merely a bag of pitch classes.

Possible semantic decomposition:

```
lower identity layer
+ upper color structure
+ top-line target
```

This allows the system to understand that the same pitch collection may be heard
differently depending on lower guide tones, bass, register, and top note.

### 4.6 Quartal / modal voicing

Do not reduce fourth-based voicing to a synonym for one chord symbol.

Track:

- fourth-chain shape
- interval quality
- register
- relation to mode/scale
- pedal/bass context
- planing / parallel movement
- degree of functional versus coloristic interpretation

### 4.7 Drop / open structures

Drop terminology is top-down and depends on voice order.

Core should preserve enough voice order to describe transformations such as drop-2,
but Piano grammar should decide whether a resulting layout is playable and appropriate.

Potential transform model:

```
source close structure
→ structural transformation
→ register placement
→ piano hand realization
```

---

## 5. Comping is not only voicing

Voicing selection and comping rhythm must be coupled but separately represented.

### 5.1 Comping action types

Potential immediate actions:

- silence
- short chordal stab
- sustained support
- anticipation
- delayed answer
- rhythmic punctuation
- countermelody
- repeated rhythmic figure
- pedal/ostinato support
- chordal swell
- sparse shell
- dense color gesture

Silence is a valid action and should compete with sounded candidates.

### 5.2 Rhythmic interaction

Inputs eventually needed from ensemble state:

- soloist onset density
- phrase ending / breath
- rhythmic motif
- drummer accent / setup
- bass activity
- previous comping density
- metric location
- swing/microtiming state
- call / response opportunity
- phrase tension trajectory

The pianist should not simply fill every available space.

### 5.3 Density control

Density has several independent dimensions:

- number of voices
- register span
- spectral/registral concentration
- rhythmic event frequency
- sustain duration
- pedal amount
- articulation weight

A 5-note voicing played once can be less intrusive than repeated 2-note stabs.

---

## 6. Performance timing inside one voicing gesture

CR-001 explicitly supports per-voice onset offsets.

Piano grammar should eventually model gesture shapes such as:

- simultaneous
- low-to-high roll
- high-to-low roll
- bass anticipation
- delayed top note
- inner-voice delay
- loose near-simultaneous attack

These are realization policies, not separate future events.

Example:

```
gesture anchor
  bass      -0.015 beat
  tenor      0.000
  alto      +0.010
  soprano   +0.025
```

All four voices can still constitute one committed immediate gesture.

---

## 7. Style and player variation

Do not assume a single canonical jazz-piano voicing grammar.

Future evidence should separate:

- SharedJazzPianoGrammar
- Era/Substyle tendencies
- Pianist/Legend tendencies
- RecordingContextProfile
- Current Ensemble State

Potential study areas:

- bebop
- hard bop
- modal
- post-bop
- ballad
- swing-era / stride-derived
- modern/contemporary
- Latin-jazz contexts

Legend studies should capture conditional decision tendencies, not literal voicing
phrase libraries.

---

## 8. Candidate-generation architecture

Proposed future pipeline:

```
Core musical context
→ sonority intention
→ constraint set
→ voicing-family candidates
→ voice-structure candidates
→ generic Core evaluation
→ piano realizations
→ piano feasibility/style evaluation
→ rhythmic interaction evaluation
→ immediate commit
→ listen again
```

Do not generate one "correct voicing." Generate plausible candidate families and let
contextual evaluation choose among them.

---

## 9. Knowledge that Wikipedia/public overview sources support reasonably well

Useful baseline areas:

- jazz commonly extends seventh-chord harmony with 9/11/13 and altered tensions
- root/fifth omission is common in ensemble voicing, but not universal
- 3rd and 7th frequently carry strong chord-quality/function information
- upper-structure triads are a jazz-piano/arranging voicing method
- drop voicing terminology is based on ordered voices from the top
- quartal harmony is a substantial jazz color/voicing practice
- comping evolved toward flexible, interactive chordal/countermelodic support with space

These are baseline concepts only, not sufficient rules for expert performance.

---

## 10. Knowledge still required from professional sources / expert annotation

High priority:

### A. Rootless and two-hand systems
- exact family taxonomies
- register conventions
- inversion/position systems
- progression-specific voice leading

### B. Tension selection
- chord-type-specific tension practice
- melody constraints
- style-dependent avoid-note concepts
- altered dominant resolution grammar

### C. Register science
- low-interval limits
- instrument-dependent masking
- soloist collision
- bass collision
- perceptual clarity by register

### D. Practical comping
- phrase-aware rhythm selection
- interaction with drummer/bassist
- accompaniment under horn versus bass versus drum solos
- when to answer, sustain, punctuate, or remain silent

### E. Piano physical grammar
- realistic hand span
- fingering-transition cost
- repetition/velocity constraints
- pedal interaction
- voicing feasibility at tempo

### F. Style / legend evidence
- pianist-specific conditional tendencies
- notated/transcribed examples with provenance
- audio-aligned timing, dynamics, and articulation where legally usable

---

## 11. Proposed first implementation milestones

### P0 — Knowledge schema
No large voicing generator yet.

Define piano-local descriptors for:

- hand assignment
- pedal/touch
- realization feasibility
- piano-specific voicing-family tags where needed

Use Core polyphonic representation for all shared sonority semantics.

### P1 — Guide-tone / shell vertical slice

Generate/evaluate a small, auditable set:

- 2-note and 3-note shell structures
- root-present and rootless alternatives
- stable voice identities across ii-V-I
- top-note constraint support
- bassist-present / absent contexts

Goal:
prove the full context → candidates → Core evaluation → Piano evaluation → immediate
commit loop.

### P2 — Rootless + extensions

Add:

- 9/13 color
- dominant alterations
- melody-aware top notes
- compact vs open positions

### P3 — Upper structure / quartal / drop families

Only after textbook/source comparison prevents taxonomy from hardening prematurely.

### P4 — Rhythmic comping interaction

Make silence and rhythmic gestures first-class immediate actions.

### P5 — Style/legend-conditioned policy

Introduce evidence-backed tendencies without literal phrase/voicing copying.

---

## 12. Source discipline

Wikipedia/public overview material is being used only to establish vocabulary and a
baseline concept map.

Professional textbooks, peer-reviewed literature, licensed/transcribed evidence, and
expert judgment should control detailed voicing rules and stylistic policy.

When sources disagree, preserve the disagreement as alternative grammars or contextual
tendencies rather than silently collapsing them into one rule.

---

## 13. Immediate next step

Implement P1 only after defining the minimal data needed to distinguish:

- harmonic role,
- voice identity,
- root-present/rootless context,
- bassist presence,
- shell/guide-tone family,
- top-note requirement,
- piano hand realization,
- voice-leading cost,
- ensemble activity.

Do not encode broad textbook-specific voicing tables yet.
