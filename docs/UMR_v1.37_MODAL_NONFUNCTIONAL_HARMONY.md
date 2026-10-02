# UMR v1.37 — Modal / Nonfunctional Harmony State

## Source-grounded modal findings

This pass uses the uploaded Berklee modal-harmony material as its primary source.

The source makes several points that are directly useful for UMR:

1. Every mode has a characteristic note that helps establish its identity.
2. Roman-numeral/function labels can become unhelpful for modal quartal structures
   when bass context is missing.
3. Putting the modal tonic in the bass causes many quartal upper structures to be
   heard as tonic/modal; changing the bass away from the modal tonic makes those
   same upper structures sound non-tonic.
4. The modal tonic in the bass helps anchor the modal tritone rather than allowing
   it automatically to imply the relative major.
5. Quartal voicings are more ambiguous than tertian voicings and reduce automatic
   major/minor tonal identification.

Accordingly v1.37 models modal identity as context, not simply a scale name.

## ModalState

ModalState stores:
- tonic pitch class
- mode name
- characteristic pitch classes
- current bass
- optional pedal
- pedal strength
- vertical topology
- current functional-pull estimate
- observed pitch classes
- confidence / provenance

The resulting ModalAssessment contains:
- orientation hypothesis
- modal anchor strength
- tonic perception
- characteristic-tone support
- tonal-pull risk
- continuity mechanisms

A tritone or characteristic tone is therefore not globally classified as an
avoid note.

## Nonfunctional continuity

The uploaded modal material directly supports bass anchoring, modal tonic,
characteristic-tone identity, and quartal ambiguity.

The broader NonfunctionalState is a project architecture abstraction rather than
a claim that one source provides a complete nonfunctional-harmony taxonomy.
Its purpose is to let UMR say, "this progression is coherent because of these
relationships" without inventing a tonic/predominant/dominant analysis.

Available continuity mechanisms include:
- common tone
- structural/melodic anchor
- pedal/bass anchor
- voice-leading
- preserved interval shape / parallel shape
- register continuity

This is the semantic basis needed later for constant structures, planing, static
colour fields, post-bop harmony, and style-specific nonfunctional vocabularies.

## Piano / Bass / Drums boundary

Shared Core owns the modal center, bass-anchor semantics, vertical-topology
meaning, and continuity mechanisms.

Piano owns the physical voicing and spacing.
Bass owns the actual bass-line/pedal realization.
Drums may consume harmonic-rhythm / modal-stability information but does not
reimplement harmony.

## Runtime invariant

The state may influence the next candidate family but contains no fixed future
note or future voicing sequence.

Perceive -> update harmonic state -> generate current affordances -> commit one
immediate action -> listen/re-plan.
