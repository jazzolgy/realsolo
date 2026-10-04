# Alice in Wonderland ground-truth release gate v0.1

Scope: `BE-011 Alice In Wonderland`, first 0–30 s. This gate governs only promotion from `EXPERT_VERIFIED` to `GROUND_TRUTH_TRANSCRIPTION`.

## Preconditions

A candidate may enter this gate only after it has passed, in order:

1. `NOTE_HYPOTHESIS`
2. `SCORE_ALIGNED_HYPOTHESIS`
3. `INSTRUMENT_ATTRIBUTED`
4. `EXPERT_VERIFIED`

No stage may be inferred from a later-stage label, model confidence, score fit, stylistic plausibility, or neighboring candidates.

## Private evidence required

For each candidate, the private record must preserve:
- stable candidate identity;
- source/provenance identity;
- score/form alignment and any surviving alternatives;
- instrument attribution and confound review;
- explicit expert-review decision and reviewer provenance;
- correction history, if any;
- unresolved ambiguity flags.

The public repository must not contain the ordered event list, event-level pitch/time sequence, or any representation that allows reconstruction of the protected transcription.

## Release decision

`GROUND_TRUTH_TRANSCRIPTION` is permitted only when all of the following are true:
- the expert-reviewed pitch/onset/offset identity is explicitly accepted;
- score/form placement is resolved to the degree required by the research task;
- instrument identity is accepted as Scott LaFaro bass rather than a competing source;
- no unresolved correction changes the event identity;
- provenance is complete enough to reproduce the verification process from authorized private materials.

If any condition is false or unknown, retain the highest already-supported stage. Do not coerce coverage to 100%.

## Corrections and reversibility

Ground truth is versioned evidence, not an irreversible fact label. Later expert evidence may demote or correct an event. Corrections must preserve audit history and must not silently overwrite the prior private decision.

## Phrase-level boundary

Ground-truth note events do not automatically validate phrase boundaries, motif identity, development operations, interaction relations, causal explanations, or Legend-level tendencies. Those require their own evidence and promotion path.

## Public-safe reporting

Public status may expose only non-reconstructive aggregates such as:
- counts by promotion stage;
- unresolved/ambiguous counts;
- protocol/schema version;
- provenance class;
- coarse review completion state.

Do not publish ordered per-event confidence, pitch, timing, score position, or labels that can reconstruct the transcription.

## Current Alice state

Until the existing private 60-event candidate store is accessible and processed through the gates above, the public-safe state remains:

- `NOTE_HYPOTHESIS`: 60
- `SCORE_ALIGNED_HYPOTHESIS`: 0
- `INSTRUMENT_ATTRIBUTED`: 0
- `EXPERT_VERIFIED`: 0
- `GROUND_TRUTH_TRANSCRIPTION`: 0

Do not regenerate a replacement 60-event list merely to advance these counts.
