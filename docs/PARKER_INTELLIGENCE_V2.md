# Parker Intelligence v2

## Decision

Charlie Parker knowledge is organized as shared Legend Intelligence, not as Sax
ownership and not as a synonym for bebop.

Data flow:

SOURCE -> OBSERVATION -> VOCABULARY / ABSTRACTION -> RUNTIME PRIOR

## Vocabulary memory

RealSolo explicitly permits stored licks and literal quotations as legitimate jazz
memory. Six runtime candidate families are supported:

1. LITERAL_QUOTE
2. TRANSPOSED_LICK
3. ADAPTED_LICK
4. FRAGMENT_RECALL
5. ABSTRACTED_PATTERN
6. HYBRID_COMPOSITION

The system tracks source/context provenance and can distinguish literal from structural
similarity. A public repository need not contain every raw copyrighted payload for the
runtime schema to support it.

## Runtime contract

Legend memory may preserve intentions, active fragments, targets, direction and
interaction role. It must not freeze a future solo.

candidate generation -> ONE EVENT -> commit -> listen -> re-evaluate

## Interfaces

- `LegendProfileView(legend, domain, context)` exposes conditional tendencies.
- `VocabularyQuery` retrieves context-compatible memory.
- `VocabularyIndex` applies contextual fit and recent-use repetition pressure.
- multi-legend mixtures operate per domain/context rather than one global scalar.

## Ownership

Generic sax physical feasibility belongs to `players/sax`.
Parker-specific observed physical/performance tendencies belong to Parker Legend
Intelligence.

## Compatibility

Historical `music_intelligence.bebop.parker_*` imports remain thin shims while the
canonical implementation moves to `music_intelligence.legends.parker`.
