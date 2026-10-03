# Autumn Leaves — expressive phrase-context learning pass v0.2

Date: 2026-10-04
Source: owner-supplied BE-003 `Autumn Leaves`
Status: DERIVED_ONLY / OBSERVATION_ONLY

## Goal

Continue learning the shared HOW layer after the initial expressive-realization
module landed on `main`.

This pass focuses on whether repeated form sections preserve one fixed dynamic
shape or instead re-realize expression according to performance phase and local
context.

Canonical learning coordinates remain musical:
form / section / chorus / bar / beat / subdivision.
Elapsed seconds remain provenance only.

## Input windows

Used the existing score-aligned navigation windows already stored in
`autumn_leaves_take1_sections_v0_1.json`:

- Head A1 / A2 / B / C
- Piano Solo Chorus 1 A1 / A2 / B / C

Each 8-bar section was divided into eight form-bar windows. Exact copyrighted
note content was not stored.

## Per-bar expressive proxy

For each bar, a source-normalized perceptual expression proxy combined:

- harmonic-component RMS / energy;
- onset strength;
- harmonic spectral brightness;
- attack sharpness;
- note-body / sustain proxy.

The proxy is explicitly not a MIDI velocity estimate and not isolated piano
ground truth. It is mixed-audio evidence used to study relative expression.

## Repeated-A evidence

### Head A2 vs Head A1

Barwise expressive-shape correlation: about **+0.42**.

A2 was stronger than A1 in 5 of 8 matched form bars, with a small positive mean
shift (~+0.037 on the source-normalized proxy).

Interpretation: the repeated A section retains some relationship to the first A,
but it is not an identical expressive replay.

### Solo A2 vs Solo A1

Barwise expressive-shape correlation: about **-0.15**.

A2 was stronger than A1 in 6 of 8 matched form bars, yet the detailed barwise
shape changed substantially.

This is stronger evidence that repeated form identity does not imply repeated
accent/dynamic realization.

## Head vs solo at the same form addresses

Mean solo-minus-head perceptual shifts were positive in all four 8-bar sections:

- A1: about +0.121
- A2: about +0.126
- B: about +0.133
- C: about +0.062

The solo was stronger than the head in:

- A1: 7/8 matched bars
- A2: 6/8
- B: 7/8
- C: 6/8

But the barwise shape correlations were weak:

- A1: about -0.12
- A2: about +0.02
- B: about +0.26
- C: about -0.26

Therefore performance phase changes both absolute expressive level and local
shape. A form address alone is insufficient to determine dynamics.

## Section-shape observations

Using coarse two-bar expression phases:

- Head A1: approximately stable
- Head A2: rising
- Head B: fall-then-rise
- Solo A1: rise-fall
- Solo A2: rising
- Solo B: rising
- Solo C: approximately stable

These labels are intentionally coarse and should not be promoted as Bill Evans
rules. Their value is architectural: the same tune contains several different
expression trajectories rather than one global crescendo template.

## Shared Expressive Intelligence consequence

Expression memory should be separated into:

1. **relative expressive identity**
   - contour family
   - peak/release relationship
   - accent-target tendencies
   - body/sustain tendency

2. **contextual realization**
   - form position
   - performance phase
   - phrase maturity
   - tension/release state
   - ensemble density
   - foreground/background role
   - repetition index
   - register

A vocabulary item or motif should therefore not own a frozen velocity array.

Recommended learning relation:

```text
phrase_or_motif_identity
× form_position
× performance_phase
× ensemble_state
× repetition_state
→ expressive_realization_distribution
```

rather than:

```text
phrase_or_motif_identity
→ fixed_velocity_pattern
```

## Repetition learning rule

When material repeats, the engine should compare the new realization to recent
HOW-memory and learn whether the repetition uses:

- absolute-level shift;
- contour expansion/compression;
- accent relocation;
- body/sustain change;
- foreground/background change;
- contrast through sudden reduction rather than escalation.

The current BE-003 evidence supports keeping these alternatives open.

## Promotion boundary

This pass does **not** promote a Bill Evans-specific runtime tendency.

Reasons:

- source remains mixed audio;
- exact Piano RH/LH attribution is incomplete;
- bar windows are score-aligned navigation windows rather than sample-accurate
  note ownership;
- recording/mastering effects remain possible.

The evidence is strong enough to continue training the shared representation and
annotation process, not to claim fixed Evans velocity/accent constants.

## Next learning target

After instrument attribution improves:

1. compare the same motif across repetitions;
2. attach absolute + relative dynamics to each note/event;
3. compare accent relocation across motif development states;
4. measure release as accent/body change, not volume only;
5. compare Piano phrase peaks against Bass/Drums foreground handoff;
6. promote only recurrent, cross-context behavior.
