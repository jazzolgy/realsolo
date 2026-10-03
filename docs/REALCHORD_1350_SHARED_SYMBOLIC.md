# RealChord 1350 — Shared Symbolic Corpus Integration

## Status

RealChord 1350 is a Shared Core symbolic/reference corpus.

It is not owned by Piano, Bass, Drums, Sax, Transcription, or one research
branch. All workstreams consume the same stable `realchord_id`.

## Canonical coordinate

When RealChord alignment is available, the preferred symbolic coordinate is:

```text
realchord_id
→ section
→ measure/form_bar
→ beat
→ subdivision/event
```

Audio seconds remain provenance / re-alignment locators rather than the primary
learning coordinate.

## Harmony layering

RealChord is an **Expected Harmony** source.

It must not overwrite:

- Observed Harmony: what the performance audio/symbolic evidence actually shows;
- Inferred Harmony: the system's interpretation of substitution,
  reharmonization, anticipation, tonicization, upper structures, etc.

Expected / Observed / Inferred may disagree, and that disagreement is itself
useful musical evidence.

## Form role

RealChord normalized records may contribute:

- section identity;
- measure index;
- chord changes with beat positions;
- repeat starts / ends;
- endings;
- navigation;
- form role.

Performance-specific intros, vamps, interludes, tags, codas, extensions and
contractions remain separate arrangement/performance evidence and must not be
forced into the core chart grid without verification.

## Rights

Registration does not imply training permission.

The initial shared registry entry is RESEARCH / REFERENCE / EVALUATION only.
Training or redistribution requires explicit rights metadata.

## Parser boundary

`music_intelligence.corpus.realchord.song_from_normalized_record()` consumes
parser-normalized records. It deliberately does not invent or freeze one raw
HTML/JSON storage format.

The source importer may evolve independently while the normalized Shared Core
contract remains stable.
