# Context-Correction Risk Diagnostics

Raw detector output and context-corrected posterior are both evidence. A large
difference between them is not automatically an error, but it is important
diagnostic information.

This layer quantifies that difference without deciding musical truth.

## Metrics

For categorical distributions such as instrument and role, the first metric is
**total variation distance**:

```text
TV(P, Q) = 0.5 * sum(|P(label) - Q(label)|)
```

It ranges from 0 (identical) to 1 (completely disjoint).

The diagnostic also preserves:

- raw top label and probability;
- posterior top label and probability;
- whether the top label changed;
- raw support for the posterior-winning label;
- posterior lift over that raw support;
- whether the result is context-dominated;
- review recommendation and reasons.

## Context-dominated interpretation

A posterior is marked context-dominated only when configurable policy thresholds
show all of the following:

- posterior confidence is high;
- the same label had weak raw acoustic support;
- context caused a large probability lift.

Example:

```text
raw bass       = 0.28
posterior bass = 0.91
lift           = +0.63
```

This does **not** mean the interpretation is wrong. It means downstream learning
or corpus admission should know that the conclusion depends heavily on context.

By contrast:

```text
raw bass       = 0.88
posterior bass = 0.93
```

is a small correction where acoustic and contextual evidence agree.

## Intended uses

- debug Shared Audio Intelligence;
- calibration analysis;
- detect context-dominated evidence before training;
- prioritize human review;
- compare detector/model versions;
- protect Shared Memory from silently accepting weak-acoustic/strong-context
  interpretations as if they were direct observations.

The diagnostics must not alter raw evidence or posterior evidence. They are an
additional audit layer only.
