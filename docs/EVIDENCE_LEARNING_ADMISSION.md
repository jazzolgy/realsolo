# Evidence Admission into Shared Learning and Memory

Performance Evidence quality and legal/rights eligibility are separate gates.

A recording or event can be acoustically strong but not training-authorized.
Likewise, training-authorized material can still be too context-dominated to
enter a prior automatically.

## Trust classes

- **DIRECT_ACOUSTIC** — raw and contextual evidence agree, or correction is small.
- **CONTEXT_SUPPORTED** — context materially helped interpretation, but the shift
  is not high-risk.
- **REVIEW_REQUIRED** — high/context-dominated correction; preserve for audit,
  but do not update learning priors automatically.
- **UNASSESSED** — legacy or incomplete evidence without correction diagnostics.

## Default admission

```text
DIRECT_ACOUSTIC
  → evidence prior: yes
  → training prior: yes only if rights permit

CONTEXT_SUPPORTED
  → evidence prior: yes
  → training prior: yes only if rights permit and policy allows

REVIEW_REQUIRED
  → stored for audit
  → evidence prior: no
  → training prior: no

UNASSESSED
  → evidence prior: yes by default
  → training prior: no by default
```

The important rule is that review-required evidence is **not deleted**. It stays
available for debugging, human review, calibration, and future reprocessing.

## Why this matters

This prevents Shared Memory and Corpus Learning from treating a strongly
context-driven interpretation as if it were direct acoustic observation.

Example:

```text
raw bass       = 0.28
posterior bass = 0.91
risk           = HIGH
```

The event can remain in the evidence store with full provenance, while derived
learning artifacts are blocked from automatic prior updates until reviewed.

## Rights remain independent

Evidence admission never grants training permission.

```text
evidence quality gate
        AND
rights/training-permission gate
        ↓
trainable prior admission
```

This preserves the existing distinction between research/evidence priors and
rights-gated trainable/adaptive priors.
