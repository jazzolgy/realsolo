# Alice private candidate ingestion gate v0.1

## Purpose

Validate the existing private 60-event store before any score alignment or
instrument attribution. This gate does not contain, reconstruct, or regenerate
the private events.

## Store identity gate

Reject the input unless all are true:

- `track_id == "BE-011"`
- `private_store_id == "private.legend.scott_lafaro.alice.v1"`
- track-relative analysis window is exactly `0..30 s`
- candidate count is exactly `60`
- every candidate has a stable, non-empty, unique `candidate_id`
- every candidate is still at `NOTE_HYPOTHESIS` on first load
- source provenance identifies the owner-supplied mixed trio audio

A mismatch is a hard stop. Do not silently repair, renumber, truncate, pad, or
replace candidates.

## Event integrity gate

For each private event:

- preserve original onset and pitch hypothesis;
- require finite onset within the analysis window;
- if offset exists, require `offset >= onset`;
- if duration exists, require non-negative duration;
- confidence values, when present, must be in `0..1`;
- unknown analytical fields remain null;
- score-derived fields must not overwrite acoustic observations.

Duplicate IDs, impossible timing, or malformed confidence values quarantine the
record for review; they do not authorize deletion or automatic correction.

## Promotion gate

A record may become `SCORE_ALIGNED_HYPOTHESIS` only after a score/form
location is supported or an explicit set of plausible alternatives is stored.
Alignment uncertainty is not evidence about instrument identity.

A record may become `INSTRUMENT_ATTRIBUTED` only after the alignment stage and
after mixed-trio confounds have been considered: bass fundamental/overtone,
piano left hand, piano resonance, percussive leakage, and overlap.

No automatic path in this gate can create `EXPERT_VERIFIED` or
`GROUND_TRUTH_TRANSCRIPTION`.

## Safe public aggregate

After a private validation pass, public reporting may include only:

- total input count and quarantined count;
- counts by promotion stage;
- coarse confidence bins;
- coarse form-coverage labels;
- unresolved error-class counts;
- provenance and protocol/schema versions.

Never publish candidate IDs, event times, pitches, ordered event-level
confidence values, or reconstructive phrase sequences.

## Failure behavior

Fail closed. Preserve the original private store unchanged and emit a validation
report identifying the failed rule. Never regenerate replacement candidates to
make the gate pass.
