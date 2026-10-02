# UMR v1.45 — Shared Corpus Registry

## Problem

Research audio and derived analyses should not have to be supplied separately to
piano, bass, drums, sax, transcribe, and realtime workstreams.

The corpus is a Core resource. Player branches consume it through stable IDs and
queries.

## Architecture

One shared private corpus root:

REALSOLO_CORPUS_ROOT/
- audio/
- symbolic/
- derived/
- annotations/
- synthetic/
- evaluation/

The public Git repository stores code, schemas, manifests, and derived material
that is legally appropriate to publish. Copyrighted or rights-unclear raw audio
should normally stay outside the public repository.

All workstreams refer to the same CorpusItem ID.

Example:

audio.parker.ko_ko.master

The same item can be queried by:
- player/sax for solo-language research;
- player/piano for comping / interaction research;
- player/bass for bass-line / interaction research;
- player/drums for ride / comping / setup research;
- transcribe for source transcription;
- ensemble analysis for call/response and emergent meaning.

No duplicate audio copy is required per branch.

## Corpus layers

The registry follows the project data strategy:

- Audio Foundation Corpus
- Musical Intelligence Corpus
- Aesthetic Corpus
- Synthetic Corpus
- Expert Annotation Corpus

## Use classes

Each CorpusItem can declare:
- TRAINING
- RESEARCH
- REFERENCE
- EVALUATION
- REDISTRIBUTION

Those categories are intentionally separate.

## Rights / provenance

Each item can preserve:
- source
- rights holder
- license
- training permission
- research permission
- commercial permission
- redistribution permission
- derived-from lineage
- provenance notes

Unknown permission is not treated as permission.

## Player use

A player should request the material it needs rather than own a private copy.

Example conceptual query:

kind = AUDIO_FOUNDATION
legend_id = charlie_parker
instrument = bass
use = RESEARCH

This can return the same Parker ensemble recording used by sax, piano, and
drums because the recording contains ensemble evidence relevant to all parts.

Instrument tags describe relevance, not ownership.

## Derived analysis

One source recording can have many shared derived items:
- stem/separation references
- beat/downbeat maps
- chord/harmony analysis
- form/section annotations
- transcriptions
- interaction events
- phrase annotations
- timing measurements

Each derived item points back through derived_from so evidence provenance stays
traceable.

## Chat / branch note

Git branches can share this registry because it lives in Core. Separate ChatGPT
conversations do not automatically share raw file uploads as a filesystem.
Therefore reusable audio should be placed in the shared corpus storage once and
registered by stable ID; each workstream then references the ID rather than
requiring another upload.

## Initial policy

For commercially released Charlie Parker recordings, the safe default in this
project is RESEARCH / REFERENCE unless the actual rights metadata explicitly
supports broader use. Do not put those raw recordings in the public repository.

Training eligibility is a separate decision from research access.
