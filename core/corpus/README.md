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


## Shared Standard 100 charts

The canonical 100-standard practice set belongs to Shared Core, not to bass,
piano, drums, sax, or transcribe.

Source:
- iRealPro Corpus of Jazz Standards v1.0
- Daniel Shanahan and Yuri Broze
- DOI: 10.5281/zenodo.3546040
- License: CC BY 4.0

The repository stores the curated 100-title manifest, stable chart IDs, rights
metadata, and ingestion code. The official raw Humdrum/Kern files are installed
once under:

```text
REALSOLO_CORPUS_ROOT/
  symbolic/
    irealb_v1_0/
      standard100/
```

Every player resolves the same IDs such as:

```text
chart.standard100.autumn_leaves
chart.standard100.all_the_things_you_are
chart.standard100.cherokee
```

Do not create player-owned copies of these charts. Player-specific
interpretations, bass lines, voicings, drum parts, solos, and transcriptions are
derived outputs and must keep provenance back to the shared chart item.

Install from the official source archive with
`install_standard_100_from_archive(...)`. The installer preserves each source
chart's raw text while renaming only the local filename to a stable canonical
slug.
