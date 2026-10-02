# Charlie Parker Intelligence v2

Canonical research home for Charlie Parker-derived evidence.

## Architecture

SOURCE -> OBSERVATION -> VOCABULARY / ABSTRACTION -> RUNTIME PRIOR

Parker is neither equivalent to bebop nor owned by the Sax player. Shared Parker
evidence lives here and in `src/music_intelligence/legends/parker/`; instrument
realization remains under `players/<instrument>/`.

## Vocabulary principle

Stored licks, motifs, fragments, clichés and phrase vocabulary are legitimate jazz
memory. Runtime may use these candidate families:

- LITERAL_QUOTE
- TRANSPOSED_LICK
- ADAPTED_LICK
- FRAGMENT_RECALL
- ABSTRACTED_PATTERN
- HYBRID_COMPOSITION

A stored vocabulary item should retain source/context provenance and usage/similarity
metadata. Literal quotation is allowed; it is not the only Parker model.

## Improvisation invariant

Memory may hold an intention, active fragments, target, direction and interaction role,
but not a frozen future solo. Runtime remains:

candidate generation -> commit ONE event -> listen -> re-evaluate

## Ownership boundary

Parker-specific register/breath/articulation tendencies belong to Legend Intelligence.
Generic sax fingering, breath feasibility, articulation-rate and register-transition
constraints belong to `players/sax/physical.py`.

## Layout

- `sources/`: source manifests and rights/provenance references
- `observations/`: grounded audio/score/alignment observations
- `vocabulary/`: lick/fragment/motif/template extraction metadata
- `analyses/`: cross-observation domain analysis and coverage
- `transfers/`: research notes about applying Parker evidence to an instrument

Executable policy is not owned here. Canonical runtime interfaces live under
`src/music_intelligence/legends/`.
