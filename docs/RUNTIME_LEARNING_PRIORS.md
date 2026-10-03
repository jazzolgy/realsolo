# Runtime Consumption of Weighted Learning Priors

Shared Learning is useful only if runtime musical reasoning can consume it
without turning learned statistics into deterministic playback.

This slice wires `LearningPriorView` into four runtime decision areas while
preserving the architecture rule:

> Learners produce priors. Runtime reasoning consumes only the stable prior
> view. Realtime execution does not own learning.

## Current runtime connections

### Solo

Piano solo candidate evaluation may consume the `SOLO_PHRASE` prior.
The first safe mapping is learned `entry_phase` against the candidate's
immediate metric placement.

This is a bounded score nudge, not a forced onset or precomposed phrase.

### Comping

Piano comping candidate evaluation may consume the `COMPING` prior.
Candidate piano-density/intrusion is compared with learned comping `density`.

Again, the prior is one score component beside ensemble space, harmony,
instrument feasibility, interaction, creativity, and variation.

### Ensemble interaction

The shared interaction scheduler may consume the
`ENSEMBLE_INTERACTION` prior. Learned `response_role` tendencies only
increase confidence for compatible response/support roles. They do not replace
the scheduler's current ensemble-state reasoning or force an interaction kind.

### Groove

`build_groove_context()` may consume the `RHYTHM_GROOVE` prior. When an
explicit grammar is absent, the strongest learned `best_groove_grammar` can
supply a soft default. Agreement with the learned grammar may slightly raise
confidence.

An explicit runtime grammar remains authoritative.

## Boundary

```text
SharedLearningEngine
    ↓ prior(...)
LearningPriorView
    ↓
Shared/Piano musical evaluators
    ↓ soft score/confidence bias
Existing candidate competition
    ↓
ONE EVENT / ONE DIRECTIVE commitment
```

Runtime modules do not access LearningStore, artifacts, admission logs, or
learner internals.

## Why this is intentionally conservative

The current learned feature schemas were built from structural evidence. Only
features with a clear runtime semantic match are wired now.

We do **not** invent mappings such as treating note duration as phrase span or
turning a corpus statistic directly into a mandatory musical action. Additional
prior mappings should be added only when the learned feature and runtime
candidate descriptor mean the same musical thing.
