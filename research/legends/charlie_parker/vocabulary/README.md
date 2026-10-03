# Charlie Parker Vocabulary Memory

One observed phrase may yield multiple memory levels:

FULL LICK -> FRAGMENTS -> MOTIFS -> RHYTHMIC CELLS -> HARMONIC CELLS -> CONTOUR / INTERVAL SCHEMA

Canonical runtime use types are LITERAL_QUOTE, TRANSPOSED_LICK,
ADAPTED_LICK, FRAGMENT_RECALL, ABSTRACTED_PATTERN, and HYBRID_COMPOSITION.

Literal source material may remain private. Public artifacts should preserve
provenance, context, identifiers, and aggregate/derived representations that are
appropriate to commit.


## Current repository status

The Parker vocabulary index was historically empty because the research pipeline
stopped at two different representations:

1. **Legend / conditional priors** — contextual features such as passing,
   close approach, anticipation, space, leap recovery, phrase ending;
2. **aggregate corpus statistics** — e.g. 131 symbolic licks summarized into
   transition/rest statistics.

No ingestion step converted those results into `VocabularyMemoryItem` records,
and the public `vocabulary/` subdirectories contained README scaffolds rather
than item data.

The runtime index now promotes reusable source-grounded abstractions from those
existing studies. This makes Parker vocabulary immediately queryable without
inventing exact note sequences.

Exact/literal Parker phrases are a separate ingestion level. The current
repository does **not** contain the individual note/rhythm payloads behind the
131-lick aggregate, so exact licks cannot be reconstructed from the statistics.
When structured exact phrases are supplied, place them in
`src/music_intelligence/legends/parker/data/vocabulary*.json`; the loader will
preserve literal and normalized representations and allow literal quotation as
one of the normal runtime use modes.
