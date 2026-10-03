# Literal + Transformed Vocabulary Runtime Policy

RealSolo now treats literal jazz vocabulary and transformed vocabulary as two
normal reuse modes.

## Default mix

When a retrieved vocabulary item contains an admitted literal representation:

```text
30%  direct / literal use
70%  transformed use
```

The transformed side includes:

- transposed use
- adapted use
- fragment recall
- abstracted pattern
- hybrid composition

If an item has no literal representation, a "direct" slot automatically falls
back to a transformed use.

## Why both

Literal use preserves recognizable language and source identity.
Transformation keeps the system responsive to current harmony, register,
instrument, phrase state and ensemble interaction.

The ratio is a runtime usage target, not a requirement that every single phrase
contain exactly 30% literal material.

## Source storage

Exact symbolic material is kept together with:

- source id
- source title/page or recording location when known
- literal representation
- normalized representation
- harmony/context tags
- permitted reuse modes
- provenance

The first concrete bridge imports the exact symbolic patterns already present in
`players/drums/pattern_corpus.py` into the Shared Vocabulary index.

Future ingestion should do the same for structured melodic licks, bass lines,
piano figures and other exact vocabulary already available in project sources.

## Causal invariant

A complete stored lick/pattern may exist in memory, but realtime execution still
commits only the immediate event/gesture before listening again.

Stored phrase knowledge is memory.
Runtime commitment remains causal.
