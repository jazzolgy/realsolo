# Alice In Wonderland — MusicalMoment Study Case v0.1

## Purpose

This is the first real study case for the shared `MusicalMoment` contract.

It is intentionally small and partially observed. The goal is to test whether
form/phrase/player/interaction evidence can be aligned without inventing missing
trio behavior or collapsing the study into bass-only note transcription.

Source identity:
- BE-011 Alice In Wonderland
- Bill Evans / Scott LaFaro / Paul Motian
- Village Vanguard 1961 source identity
- project audio segment: 3388s–3809s
- score anchor: Realbk1.pdf p.12

## Selected moments

### 1. Long 3/4 rhythmic identity

Evidence anchor:
- literature analysis: chorus B, bars 2–26
- vocabulary: `lafaro.alice.long_3_4_rhythmic_cell.v1`

Question:
Can MusicalMoment represent a bass idea that preserves rhythmic identity over
a long span while pitch may vary?

Current evidence supports the bass behavior. Piano/drums actions are not filled
until independently aligned.

### 2. Offbeat / beat-one avoidance phrase

Evidence anchor:
- literature analysis: chorus A, bars 4–9
- vocabulary: `lafaro.alice.offbeat_downbeat_avoidance.v1`

Question:
Can the study distinguish a stable 3/4 metric environment from a bass phrase
whose entrance/landing behavior creates metric tension?

This should later test whether runtime policy can increase rhythmic
displacement without losing form awareness.

### 3. Eighth-note polyrhythm with harmonic retarget

Evidence anchor:
- literature analysis: chorus B, bars 43–44
- vocabulary: `lafaro.alice.eighth_polyrhythm_retarget.v1`

Question:
Can one moment carry both rhythmic identity and harmonic retarget information
without storing a literal line?

This is a direct candidate for later:
Vocabulary -> Motif -> MusicalPolicyProjection -> Player realization.

### 4. Space / foreground handoff

Evidence anchor:
- literature conversational-counterpoint example
- vocabulary: `lafaro.alice.space_triggered_foreground_answer.v1`

Observed description:
- piano leaves space;
- bass enters foreground;
- bass relation is tagged as an observed answer/handoff relation.

Important:
The moment does **not** assert that piano space causally caused the bass entry.
Causality remains a later relation-study question.

## What is deliberately unresolved

- absolute audio timestamps for the literature bar references;
- exact score/harmony references at each moment;
- piano/drums actions in bass-only evidence windows;
- ensemble density/energy/tension where not directly supported;
- exact interval/rhythm schemas unless separately verified;
- causal claims;
- aesthetic/reward judgments.

Zero-valued unresolved aggregate fields should not be interpreted as measured
zero. They are placeholders until the representation gains or consumes an
explicit unknown/optional aggregate convention.

## What this study case already tests

1. Partial observation is legal.
2. One MusicalMoment may contain only the players supported by evidence.
3. A relation can be recorded without claiming causality.
4. A motif/vocabulary reference can be aligned to a moment without literal
   note content.
5. Shared Core remains free of instrument realization commands.
6. The same study object can later be compared with runtime DecisionContextLog.

## Next alignment pass

For BE-011 project audio:

1. verify head / solo / out-head boundaries;
2. align score-form positions to audio timestamps;
3. identify the literature-referenced bar windows in the project audio;
4. add Piano and Drums actions only where audibly supported;
5. distinguish observed interaction from inferred interaction;
6. populate harmony expected/observed/inferred refs separately;
7. derive a sequence of adjacent MusicalMoments around one handoff, rather than
   only isolated snapshots.

The first high-value micro-sequence should be:

`before-space -> piano-space -> bass-entry -> bass-development -> handoff`

That sequence can later support relation study without putting causal
attribution inside MusicalMoment itself.
