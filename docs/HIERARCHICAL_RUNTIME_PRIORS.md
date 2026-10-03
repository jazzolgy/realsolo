# Hierarchical Runtime Priors

Runtime musical reasoning now distinguishes several prior layers instead of
collapsing every learned tendency into one undifferentiated score.

```text
Generic / domain prior
        +
Genre prior
        +
Style prior
        +
Legend prior
        +
Current ensemble / harmony / form context
        ↓
bounded candidate-score contributions
        ↓
existing evaluator competition
        ↓
one immediate commitment
```

## Layer meanings

### Domain prior

The closest learned behavior for the current decision domain, such as
`SOLO_PHRASE` or `COMPING`.

Default runtime layer weight: **1.00**.

### Genre prior

Broad idiom tendencies learned across performances, such as bebop, swing,
bossa, funk, or salsa behavior.

Default runtime layer weight: **0.45**.

Genre is intentionally weaker than the domain prior because an idiom should
shape a performance without reducing it to a stereotype.

### Style prior

Cross-domain performer/style tendencies.

Default runtime layer weight: **0.60**.

Style is more specific than genre but still remains a soft statistical tendency.

### Legend prior

Evidence-based musician-specific tendencies through the existing
`LegendBlend` / `LegendProfileView` interfaces.

Default layer weight: **1.00**, but the existing legend confidence and profile
weights still apply. Legend priors never copy a literal phrase and never bypass
instrument feasibility or current musical context.

## Current-context authority

Current ensemble, harmony, form, player feasibility, phrase-space and
interaction evidence are **not another learned-prior bucket**. They remain live
musical evidence inside the existing evaluators.

This distinction matters:

```text
prior = what tends to work / what was learned
context = what is happening now
```

The prior may bias a choice. Current context may override it.

## Current integrations

Piano comping now combines semantically equivalent density tendencies from:

- `COMPING.density`
- `GENRE.comping_density_mean`
- `STYLE.comping_density_mean`

Each contribution remains separately visible in score components.

Piano solo continues using the immediate `SOLO_PHRASE.entry_phase` prior.
Genre/style phrase-span statistics are deliberately not forced onto a single
note candidate because that would mix phrase-level and event-level semantics.

If a `HierarchicalPriorSet` supplies a legend blend, piano solo may consume it
as the default legend layer. An explicitly supplied legend blend still wins.

## Design rule

A new hierarchy mapping may be added only when the learned feature and runtime
candidate descriptor refer to the same musical quantity or a clearly documented
projection of it.

The system must not create artificial intelligence by connecting unrelated
statistics simply because both are numeric.
