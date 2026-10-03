# Confidence-Weighted Learning

Admission is not only a binary gate. Evidence that is usable but less direct
should influence Shared Learning less strongly than high-confidence direct
acoustic evidence.

## Effective learning weight

For the admission-gated path:

```text
effective_weight
= trust/admission weight
× LearningArtifact.confidence
```

The trust weight is configurable policy, not a claim about musical truth.

Default values:

```text
DIRECT_ACOUSTIC    1.00
CONTEXT_SUPPORTED  0.65
UNASSESSED         0.50 for evidence prior only
REVIEW_REQUIRED    0.00
```

Rights remain a separate gate for trainable priors.

## Weighted statistics

DomainLearningState preserves ordinary observation counts for compatibility,
while also accumulating weighted statistics:

- `observations` — number of admitted artifacts;
- `weighted_observations` — total effective influence;
- `numeric_counts` — raw admitted count per feature;
- `numeric_weights` — total effective weight per numeric feature;
- `categorical_counts` — raw category counts;
- `categorical_weights` — weighted category influence.

Numeric means are weighted online means. Categorical `category_weight()`
prefers weighted influence when available.

## Example

Two artifacts:

```text
direct acoustic:
value = 0.20
weight = 1.00

context-supported:
value = 1.00
weight = 0.50
```

The learned mean is:

```text
(0.20 × 1.00 + 1.00 × 0.50) / 1.50
= 0.4667
```

not the unweighted mean 0.60.

This preserves useful context-supported evidence without allowing it to pull a
prior as strongly as direct evidence.

## Compatibility

Legacy `observe()` remains full weight (1.0).

Legacy manually-created LearningAdmissionDecision objects without explicit
weights are also treated as full-weight when admitted. New
`admission_for_artifact()` decisions always carry explicit policy weights.
