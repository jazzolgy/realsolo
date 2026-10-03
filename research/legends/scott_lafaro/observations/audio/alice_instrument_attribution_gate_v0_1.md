# Alice instrument-attribution evidence gate v0.1

## Purpose

Define the boundary from private `SCORE_ALIGNED_HYPOTHESIS` records to
`INSTRUMENT_ATTRIBUTED` without treating low-frequency mixed-trio evidence as
Scott LaFaro by default.

This document contains no exact event list, note sequence, event time, or
ordered confidence series.

## Preconditions

Attribution is evaluated only when:

- the original private 60-event store passed the ingestion gate;
- the candidate has reached `SCORE_ALIGNED_HYPOTHESIS`;
- candidate identity and acoustic observation remain unchanged;
- score/form alignment uncertainty remains available as uncertainty, not as an
  attribution prior.

A candidate that has not passed the alignment gate cannot be promoted by this
gate.

## Evidence channels

For each private candidate, preserve evidence separately rather than collapsing
it prematurely into one confidence value.

### Bass-supporting evidence

Possible supporting evidence includes:

- low-frequency attack with bass-like harmonic continuation;
- fundamental/overtone consistency across adjacent analysis frames;
- decay/envelope compatible with the recorded acoustic bass;
- continuity with a locally plausible bass line or register trajectory;
- source-separation evidence that remains stable under reasonable analysis
  settings.

Musical plausibility is supporting context only. A note fitting the harmony or
forming a convincing bass line is not proof of instrument identity.

### Required confound checks

Explicitly test competing explanations:

- piano left-hand attack;
- piano resonance or pedal-related low-frequency energy;
- percussive leakage;
- simultaneous/overlapping sources;
- octave or subharmonic pitch error;
- onset split/merge error from the candidate detector.

Absence of evidence for a confound is not automatically positive bass evidence.

## Private attribution result

Use one of:

- `bass`
- `piano_left_hand`
- `piano_resonance`
- `percussive_leakage`
- `overlap`
- `unknown`

Store `instrument_attribution_confidence` only when it is actually estimated.
Unknown confidence remains null.

When two sources remain materially plausible, prefer `overlap` or `unknown`
with reviewer notes over forced bass classification.

## Promotion rule

Promote a record to `INSTRUMENT_ATTRIBUTED` only when all are true:

1. it is already `SCORE_ALIGNED_HYPOTHESIS`;
2. bass-supporting acoustic evidence has been examined;
3. the required mixed-trio confounds have been examined;
4. the selected label is supported independently of score compatibility;
5. provenance records the attribution method/version;
6. unresolved uncertainty is preserved.

The label `INSTRUMENT_ATTRIBUTED` means the instrument decision has passed
this evidence gate. It does not mean expert verification or transcription
ground truth.

No automatic action here may create `EXPERT_VERIFIED` or
`GROUND_TRUTH_TRANSCRIPTION`.

## Phrase-level caution

Do not bootstrap uncertain neighbors into bass facts merely because several
candidates form a musically coherent phrase. Phrase continuity can support
review, but each promoted event must retain sufficient event-level evidence.

Likewise, a known LaFaro stylistic tendency is not admissible as primary
identity evidence. Legend knowledge must not create circular attribution.

## Public-safe aggregate

Public reporting may include:

- counts by attribution label;
- unresolved and overlap counts;
- coarse confidence bins;
- counts of confound classes encountered;
- method/schema versions and provenance.

Never publish candidate IDs, ordered labels, exact pitches, event times,
performance-to-score anchor times, or reconstructive phrase sequences.

## Expert-review handoff

After this gate, selected private events or phrases may be queued for
professional-musician ear review. Expert review receives the underlying private
evidence and may promote only explicitly reviewed material to
`EXPERT_VERIFIED`.

Automation must not infer expert approval from a high attribution confidence.
