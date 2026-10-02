# UMR v1.34 — Shared Jazz Harmony Intelligence

## Architectural decision

Jazz harmony must be learned in Shared Core, not owned by the piano player.

The piano workstream may continue voicing research in parallel because voicing and harmony are different layers:

Harmony intelligence answers:
- what harmony is expected, observed, and inferred;
- what the local function/tonicization/cadential context is;
- which stable tones, tensions, alterations, substitutions, anticipations, or outside/return paths are musically available;
- what continuity or resolution makes a colour intelligible.

Piano intelligence answers:
- which of those harmonic possibilities should be distributed across the hands now;
- spacing, register, drop/open/closed structures, melody-top constraints;
- touch, pedal, onset spread, dynamics;
- physical playability and piano-specific stylistic grammar.

Therefore piano voicing work does not need to stop, but it should increasingly consume the shared harmony layer rather than embed its own independent theory.

## Core principles

1. Expected Harmony, Observed Harmony, and Inferred Harmony are separate evidence streams.
2. No chord has one compulsory scale.
3. Harmonic colour is an affordance, not a rule.
4. Voice-leading, current ensemble evidence, phrase narrative, and target direction may override a theoretical default.
5. Altered dominant tones may appear in connected chains when dominant identity and resolution direction remain audible.
6. Major7 natural 11 is contextual: exposed use is discouraged, but passing/enclosure/suspension contexts may justify it.
7. Minor harmony is interpreted by function and local key; Dorian/Aeolian is not hard-coded as a global answer.
8. Outside playing requires a modeled departure/return relationship.
9. Reharmonization must preserve an audible continuity mechanism such as common tone, target, voice-leading, or narrative reason.
10. The harmony layer produces intentions, roles, tensions, and routes — never exact future note sequences or instrument-specific voicings.

## v1.34 implementation

A new instrument-neutral harmony package introduces HarmonicEvidence, HarmonicFrame, HarmonicAffordance, HarmonicIntent and TensionChoice.

HarmonicFrame preserves expected/observed/inferred harmony separately and can also carry the next expected harmony, phrase position, current tension, cadence state and tonicization target.

build_basic_affordances() is deliberately a minimal baseline rather than a finished theory engine. It demonstrates the correct architecture by returning plural choices for dominant, major7, minor, future-harmony anticipation and controlled outside/return contexts.

## Relationship to earlier Levine layer

The older v0.92 Levine Harmonic Intelligence design already established the correct principle: Levine should supply harmonic affordances, not chord-to-scale lookup or copied musical examples. v1.34 promotes that concept into the shared runtime codebase.

Baker/Parker vocabulary, Bergonzi rhythm/interval ideas, LegendProfiles, piano voicing grammar, and live ensemble evidence all operate downstream or alongside this shared harmonic state.

## Relationship to piano branch

player/piano remains responsible for physical and stylistic realization. Shared Core owns harmonic semantics.

The intended flow is:

Expected / Observed / Inferred Harmony
-> HarmonicFrame
-> plural HarmonicAffordances
-> phrase/ensemble/style evaluation
-> instrument candidate generation
-> piano voicing / sax line / horn distribution
-> commit one immediate action
-> listen again

This lets piano research proceed now without making piano the owner of jazz harmony.
