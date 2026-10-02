# UMR v1.52 — Shared Standard 100 Chart Corpus

## Decision

The 100-standard repertoire is a Shared Core resource.

It is not owned by:
- bass
- piano
- drums
- sax
- transcribe
- realtime

All workstreams resolve the same canonical chart ID and therefore reason about
the same form/harmony source.

## Source and rights

Primary source:

- iRealPro Corpus of Jazz Standards v1.0
- Daniel Shanahan and Yuri Broze
- Zenodo DOI 10.5281/zenodo.3546040
- Creative Commons Attribution 4.0 International

The source archive contains 1,186 Kern/Humdrum files. RealSolo selects a
curated 100-title practice/evaluation subset while preserving source
provenance.

CC BY attribution and provenance must remain attached to raw and derived chart
data.

## Storage model

The Git repository contains:
- canonical 100-title manifest
- stable IDs
- rights metadata
- source DOI/URL
- installer/ingestion code
- tests

Installed original chart files live once in the shared corpus root:

REALSOLO_CORPUS_ROOT/symbolic/irealb_v1_0/standard100/

This avoids six separate copies for six player workstreams.

## Stable identity

Examples:

chart.standard100.autumn_leaves
chart.standard100.confirmation
chart.standard100.stella_by_starlight

The stable ID is the cross-workstream identity. A player may derive its own
analysis or realization but must not mutate the source chart.

## Player contract

Each player can consume the same chart but produce different derived material:

- bass: walking/two-feel realization and interaction study
- piano: voicing/comping realization
- drums: form-aware groove/setup decisions
- sax/soloist: phrase/harmony awareness
- transcribe: alignment and score reconstruction
- ensemble: shared form/harmony clock and interaction analysis

A derived item should retain the source chart ID in provenance.

## Installation

The official Zenodo archive is supplied to
`install_standard_100_from_archive()`.

The installer:
1. scans candidate Humdrum/Kern files;
2. reads the `!!!OTL:` title metadata;
3. matches only the curated 100;
4. preserves the raw chart bytes;
5. writes them to stable canonical local paths;
6. reports installed and missing titles.

No player-specific musical intelligence is present in the installer.

## Why raw charts are not duplicated into player branches

The source chart is evidence. Bass, piano, drums and soloist interpretations
are hypotheses/realizations built from that evidence.

Duplicating or editing the source independently in each player branch would
allow form/harmony drift between players and violate the Shared Core design.
