# Shared Vocabulary Promotion Pass

This pass fixes a structural gap: RealSolo already contained many reusable
musical ideas, but most of them lived inside Player grammar, research notes,
Legend tendencies, motif code, or source-pattern corpora rather than one general
Vocabulary store.

## Why the general Vocabulary looked empty

Before this pass, `music_intelligence.vocabulary` was mostly a **retrieval and
ranking engine**:

- affinity
- ranking
- usage policy
- Legend vocabulary adapters

It did not own a populated general-purpose item catalog.

At the same time, musical knowledge was distributed across:

- Shared Solo Grammar
- Shared Motif Intelligence
- Parker promoted tendencies
- Piano comping grammar
- Bass walking / phrase grammar
- Bebop Drum runtime
- source-aware drum pattern corpus
- Bill Evans trio research notes
- player-specific studies

So "we studied it" did not automatically mean "a VocabularyMemoryItem exists."

## What is promoted now

`SHARED_VOCABULARY_ITEMS` collects reusable, non-literal abstractions from
those sources.

Current families include:

- generic solo development
- bebop linear language
- future-harmony targeting
- phrase space / answer / recap / resolve
- walking bass grammar
- two-feel and ghost-note behavior
- piano lay-out / support / answer / punctuation / continuity
- bebop ride / skip / snare phrase / non-response / setup behavior
- robust trio narrative and interaction abstractions from repeated Bill Evans
  research

The catalog is intended to grow continuously.

## What was deliberately not copied

Exact copyrighted phrases or pedagogical patterns are not moved wholesale into
the runtime catalog merely because they exist in a research/source corpus.

Examples:

- exact Riley/Spagnardi/Plainfield symbolic source patterns remain in the
  source-aware pattern corpus with their rights metadata;
- exact project-audio note hypotheses remain research evidence;
- literal Legend licks remain unavailable when no verified vocabulary item has
  been admitted.

Where useful, the system stores a **non-reconstructive abstraction** such as
"setup before ensemble figure", "ride + 2/4 pedal hi-hat family", or "directed
approach to future harmony."

## User-directed promotion in this pass

The project owner explicitly requested that existing reusable research be moved
into general vocabulary wherever reasonable.

Accordingly, robust non-reconstructive Bill Evans trio findings are promoted as
**generic ensemble vocabulary**, not as a fabricated Bill Evans Legend style.

Examples:

- position is a prior, not an action;
- form knowledge does not imply form marking;
- meter does not equal pulse responsibility;
- same form position can require a new realization on a later chorus;
- explicit foreground-role reassignment can override prior restraint.

These remain soft contextual vocabulary, never deterministic templates.

## Runtime connection

The quartet now receives Shared Vocabulary projections for:

- Sax
- Piano
- Bass
- Drums

Sax currently consumes the projection directly as:

- a Shared Motif vocabulary seed;
- a soft current-event tag-fit bias;
- an intentional-space bias.

Piano/Bass/Drums already implement many of the catalogued behaviors natively;
their projections are now available for later cross-player reuse and audit.

## Next ingestion rule

Whenever research produces a reusable musical behavior, ask:

1. Is it literal/reconstructive source material?
2. Is it a musician-specific tendency?
3. Is it a generic transferable musical behavior?
4. Is it only an observation/hypothesis?

Prefer:

```text
literal source → source corpus
musician-specific evidence → Legend
generic reusable abstraction → Shared Vocabulary
uncertain observation → research evidence
```

A single study may legitimately contribute to more than one layer, but with
different representations.
