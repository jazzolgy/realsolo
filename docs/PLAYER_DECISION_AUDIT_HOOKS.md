# Shared Player Decision Audit Hooks

Piano, Bass, and Drums now expose the same optional audit boundary around their
immediate decision/commit paths.

The goal is observability, not a new central composer.

```text
Player-local candidate generation/evaluation
        ↓
ONE immediate choice
        ├─ player-local commit/memory
        └─ optional shared DecisionContextLog
                 ↓
          Listen / perceive again
                 ↓
          Shared Ensemble State refresh
```

## Shared hook

The common helper is:

`append_ranked_decision(...)`

It accepts only instrument-neutral `CandidateAudit` data. Shared Core does not
import Piano, Bass, or Drums classes.

Each Player is responsible for adapting its own candidate type into:

- candidate id;
- total score;
- score components when available;
- tags;
- a compact descriptor;
- selected candidate;
- evaluator reasons/provenance.

## Current Player coverage

- Piano solo: logs all scored immediate note/rest candidates.
- Piano comping: logs all scored comping actions.
- Bass immediate choice: logs the ranked immediate bass candidates.
- Drums: logs all scored immediate gesture candidates.

The hooks are keyword-only and optional, preserving existing call sites.

## Important boundary

The audit hook does not choose music and does not change Player policy.

It also does not assign reward or success after the performance. Re-perception
remains a separate Shared Ensemble State update:

```text
Decision log = what was considered and chosen
Re-perception = what is observed next
Feedback learning = intentionally deferred
```

This common shape lets later orchestration code collect comparable traces across
players without moving instrument-specific reasoning into Shared Core.
