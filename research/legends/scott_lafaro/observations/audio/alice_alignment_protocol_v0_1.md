# Alice 0–30 s private candidate alignment protocol v0.1

## Scope

Track: `BE-011 Alice In Wonderland`  
Source: `The Complete Village Vanguard Recordings, 1961`  
Score anchor: `Realbk1.pdf p.12`  
Private store: `private.legend.scott_lafaro.alice.v1`

This protocol starts from the existing 60 private `NOTE_HYPOTHESIS` events.
It must not regenerate them as replacement ground truth.

## Required promotion order

`NOTE_HYPOTHESIS`
→ `SCORE_ALIGNED_HYPOTHESIS`
→ `INSTRUMENT_ATTRIBUTED`
→ `EXPERT_VERIFIED`
→ `GROUND_TRUTH_TRANSCRIPTION`

No stage may be skipped.

## Per-event private fields

- candidate_id
- onset_s
- offset_s / duration_s
- pitch_hypothesis
- pitch_confidence
- score_bar
- beat_position
- form_section
- expected_harmony
- previous_interval
- register
- phrase_id
- motif_id
- instrument_attribution
- instrument_attribution_confidence
- verification_status
- provenance
- reviewer_note

Unknown values remain null. Measured zero is not a substitute for unknown.

## Alignment procedure

1. Preserve the original candidate id and timing.
2. Align physical time to score/form before instrument attribution.
3. Use score harmony as expected harmony only; do not rewrite heard pitch to fit the chart.
4. When multiple score positions are plausible, keep alternatives rather than forcing one.
5. Instrument attribution must explicitly consider:
   - bass fundamental / overtone plausibility,
   - piano left-hand attacks,
   - piano resonance,
   - kick/percussive leakage,
   - overlapping trio events.
6. Only promote to `INSTRUMENT_ATTRIBUTED` when the bass attribution is supported strongly enough to survive manual review.
7. User/professional-musician ear review may promote selected events or phrases to `EXPERT_VERIFIED`.
8. Ground truth requires explicit verification; automation alone is insufficient.

## Public-repo rule

The exact event list, exact note sequence, and reconstructive phrase data remain private.

Public updates may contain only:

- candidate counts,
- stage counts,
- confidence distribution summaries,
- non-reconstructive form coverage,
- provenance,
- unresolved-error classes,
- abstract phrase / motif / interaction profiles.

## Conflict rule

Before every public update:

1. fetch current `main` HEAD,
2. compare this branch against current main,
3. re-read the target file SHA,
4. never overwrite a concurrent edit,
5. prefer a new small file over editing a hot shared file,
6. stop and report if the semantic contract changed upstream.
