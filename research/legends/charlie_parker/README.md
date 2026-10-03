# Charlie Parker Intelligence v2

Canonical research home for Charlie Parker in RealSolo.

## Fixed pipeline

SOURCE -> OBSERVATION -> VOCABULARY / ABSTRACTION -> RUNTIME PRIOR

Stored licks and literal quotations are allowed. Licks, motifs, fragments,
cliches, rhythmic cells, harmonic cells, and phrase vocabulary are legitimate
components of jazz memory. Every item should preserve provenance and musical
context. Runtime may quote, transpose, adapt, fragment, abstract, or hybridize
memory according to current harmony, form, phrase, ensemble state, and musical
intention.

Runtime still commits one immediate event, listens again, and replans. A stored
vocabulary item is a candidate source, not a requirement to pre-compose a whole
future solo.

## Intelligence domains

### Harmonic language
01 Harmony / Target Selection
02 Linear Connection
03 Tension / Release
04 Future Harmony Awareness

### Phrase language
05 Phrase Entrance
06 Phrase Ending
07 Breath / Space
08 Rhythm / Subdivision
09 Microtiming / Swing
10 Register Trajectory
11 Interval / Leap Grammar
12 Articulation

### Memory / development
13 Motif Development
14 Repetition / Variation
15 Head Interpretation

### Structural / social
16 Form Awareness
17 Call & Response
18 Ensemble Interaction

### Performance evidence
19 Parker-specific Physical Behavior

Generic sax feasibility is NOT a Parker domain. Fingering difficulty, generic
breath capacity, altissimo feasibility, articulation speed limit, and register
transition cost belong to players/sax/.

## Runtime vocabulary use types

1. LITERAL_QUOTE
2. TRANSPOSED_LICK
3. ADAPTED_LICK
4. FRAGMENT_RECALL
5. ABSTRACTED_PATTERN
6. HYBRID_COMPOSITION

## Ownership

- research/legends/charlie_parker/: source manifests, observations, analyses, vocabulary research, transfer studies
- src/music_intelligence/legends/parker/: Parker-specific runtime LegendProfile and vocabulary interfaces
- src/music_intelligence/style/bebop/: only musician-general Bebop grammar
- players/sax/: generic Sax policy and physical realization; Parker is consumed through LegendProfileView/VocabularyQuery

Raw private/copyrighted source audio, books, and transcriptions are not copied
into the public repository.


## Boundary with Shared Solo Grammar

Charlie Parker does not own general solo methodology.

Motif development, repetition/variation, phrase entrance/ending, tension and
release, rhythmic displacement, space, contour development, future-harmony
targeting, quotation/adaptation, and hybrid composition are shared
improvisation operations.

Parker Intelligence stores evidence for **which of those operations Parker
favored, in what context, with what melodic/rhythmic/harmonic tendencies**.


## Shared exact-data storage rule

This legend follows the project-wide rule in `research/legends/README.md`:
exact audio/transcription and reconstructive literal/normalized phrase data stay
private; public/runtime code stores only public-safe abstractions, priors,
provenance and provider interfaces. Private exact material may still be queried
at runtime through the shared private-provider contract.
