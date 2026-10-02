# Shared Legend Intelligence → Drums Adapter

## Ownership

Shared Core owns:
- LegendProfileView
- VocabularyQuery / VocabularyProvider
- VocabularyMemoryItem
- vocabulary provenance and similarity metadata
- generic Legend domains

`players/drums/` owns only drum-set realization.

No Parker-, Roach-, Clarke-, Haynes-, Blakey-, or other named-musician profile is
embedded in this package.

## Shared candidate-use families

The drum player accepts the same six memory-use families fixed by Core:

1. LITERAL_QUOTE
2. TRANSPOSED_LICK
3. ADAPTED_LICK
4. FRAGMENT_RECALL
5. ABSTRACTED_PATTERN
6. HYBRID_COMPOSITION

For drums, "transposition" may mean rhythmic displacement, orchestration
transfer, register/kit transfer, or metric relocation when that interpretation
is supplied by the source vocabulary semantics.  The adapter itself does not
rewrite the Shared definition.

## Runtime contract

Legend memory changes **ranking**, not the improvisation contract.

Shared LegendProfileView
→ drummer-specific feature projection
→ current DrumGesture candidates
→ legend-aware score adjustment
→ commit ONE immediate gesture
→ listen
→ re-plan

Vocabulary memory is kept as a source reference plus descriptors. The drum
adapter intentionally does not copy a complete future fill into its state.

## Drum-specific feature vocabulary

Current instrument-level features are:
- ride_surface_flexibility
- comping_conversation
- space_preference
- bass_drum_interactivity
- form_punctuation
- motif_development
- orchestration_mobility
- dynamic_responsiveness

These are *realization features*. The evidence and named-musician profile remain
in Shared Legend Intelligence.

## Important boundary

A drummer legend is not identical to Bebop.

Shared Bebop Grammar and a named drummer's conditional tendencies remain
separate layers, exactly as Parker Intelligence is separate from Shared Bebop
Grammar.

The next evidence step is to register actual drummer sources in the shared
Legend research/corpus layer, then query them through the generic interfaces
rather than creating `max_roach.py` inside `players/drums/`.
