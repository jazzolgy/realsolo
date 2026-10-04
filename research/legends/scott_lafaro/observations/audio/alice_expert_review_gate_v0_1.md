# Alice expert-review gate v0.1

## Scope

This gate governs promotion of private `BE-011 Alice In Wonderland` 0–30 s records from
`INSTRUMENT_ATTRIBUTED` to `EXPERT_VERIFIED`.

It does not expose or recreate the private 60-event note list.

## Preconditions

A record is reviewable only when all of the following are true:

- it belongs to `private.legend.scott_lafaro.alice.v1`;
- its acoustic candidate has passed the private ingestion gate;
- score/form alignment has been reviewed under `alice_score_form_alignment_gate_v0_1.md`;
- instrument attribution has been reviewed under `alice_instrument_attribution_gate_v0_1.md`;
- the current state is `INSTRUMENT_ATTRIBUTED`;
- provenance still points to the owner-supplied mixed trio audio.

If any precondition fails, retain the earlier state.

## Private review packet

The reviewer may receive, privately:

- a short audio context around the candidate;
- the candidate pitch/onset/duration hypotheses and their confidence;
- the performance-to-score alignment and plausible alternatives;
- expected harmony/form context;
- instrument attribution and competing explanations;
- neighboring candidates needed to judge continuity.

Exact ordered event data, timestamps, pitches, and reconstructive phrase material remain private.

## Reviewer decisions

Each review produces exactly one decision:

- `CONFIRM` — the proposed note identity, score/form placement, and bass attribution are sufficiently supported;
- `CORRECT` — the reviewer supplies a corrected private annotation and states what changed;
- `REJECT` — the candidate should not be retained as a verified LaFaro note;
- `AMBIGUOUS` — evidence supports more than one interpretation;
- `DEFER` — evidence is currently insufficient.

`AMBIGUOUS` and `DEFER` are valid outcomes and must not be coerced into verification.

## Promotion rule

`EXPERT_VERIFIED` may be assigned only after:

1. an eligible reviewer actually listens to the private audio context;
2. the reviewer explicitly returns `CONFIRM`, or returns `CORRECT` and the corrected private record is saved;
3. reviewer identity or stable reviewer ID, review time, and provenance are recorded privately;
4. the record retains its complete promotion history.

Model confidence, source-separation confidence, score fit, stylistic plausibility, or a phrase being “LaFaro-like” cannot substitute for human listening.

## Disagreement

When multiple reviewers disagree:

- do not average categorical judgments into verification;
- preserve each review privately;
- keep the event below `EXPERT_VERIFIED` until the conflict is adjudicated;
- record the adjudication and its evidence.

A later reviewer may not silently overwrite an earlier correction.

## Phrase-level claims

Verified constituent notes do not automatically verify:

- phrase boundaries;
- motif identity;
- development operation;
- interaction relation;
- causal interpretation;
- Legend tendency.

Those claims require their own evidence and provenance. A memorable phrase is not by itself a general Scott LaFaro tendency.

## Ground truth boundary

`EXPERT_VERIFIED` is not automatically `GROUND_TRUTH_TRANSCRIPTION`.

Ground-truth promotion requires a separate completeness/consistency review of the relevant private window. This gate never performs that promotion.

## Public-safe reporting

Public repository updates may include only non-reconstructive aggregates such as:

- total candidates reviewed;
- counts by review decision;
- count promoted to `EXPERT_VERIFIED`;
- unresolved/ambiguous count;
- review protocol version;
- non-reconstructive provenance and limitations.

Do not publish ordered event decisions, exact timestamps, exact pitches, exact durations, reviewer corrections that reconstruct a phrase, or private audio-derived phrase content.

## Fail-closed rule

If the private store, audio context, reviewer evidence, or provenance cannot be inspected, make no promotion and leave public counts unchanged.
