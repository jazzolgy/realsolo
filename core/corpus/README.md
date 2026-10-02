# Shared Corpus

All RealSolo workstreams should consume research/reference datasets through the
shared corpus registry rather than keeping branch-specific copies.

## Private corpus root

Set:

```bash
REALSOLO_CORPUS_ROOT=/path/to/realsolo-corpus
```

Suggested local layout:

```text
realsolo-corpus/
  audio/
    parker/
  symbolic/
  derived/
  annotations/
  synthetic/
  evaluation/
```

Raw copyrighted audio should normally stay here, outside the public repository.

## Stable IDs

A source is registered once with a stable `CorpusItem.item_id`.

Player branches query the same item by legend, instrument relevance, corpus
kind, use class, or tags.

Do not create `piano/parker.wav`, `bass/parker.wav`,
`drums/parker.wav`, etc. The source is shared; player-specific conclusions
belong in derived analyses or player research outputs.
