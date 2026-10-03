# Shared Legend Data Rule

This rule applies to **every Legend Intelligence target** in RealSolo.

## Three storage layers

### Layer 1 — PRIVATE RAW

Keep outside the public repository:

- source audio / video
- exact note-by-note transcription
- exact score-derived phrase
- exact bar-by-bar copied source material

These materials may be used for analysis, verification and private runtime
retrieval when allowed, but the public repository stores only manifests,
provenance and non-reconstructive status information.

### Layer 2 — PRIVATE DERIVED

Keep outside the public repository by default:

- normalized / transposed phrase representation
- literal vocabulary
- exact lick / motif representation
- similarity fingerprints capable of reconstructing recognizable source
  material

This layer may be queried by runtime through a private provider interface.

### Layer 3 — PUBLIC / RUNTIME SAFE

May live in the public repository:

- abstract vocabulary
- contour / interval-class / rhythm-schema summaries that are non-reconstructive
- motif identity
- Legend tendencies
- conditional priors
- interaction / form / phrase relations
- non-reconstructive aggregate statistics
- confidence / provenance / source manifests

## Runtime rule

Private does **not** mean unusable by the player.

The intended architecture is:

PRIVATE RAW
-> PRIVATE DERIVED
-> public-safe abstraction / or private retrieval provider
-> Shared Vocabulary / Motif / Legend / Policy
-> Player realization

Public Player code must not depend on a hard-coded local path.  Exact material
is accessed only through the shared private-provider interface.

## Musical rule

Stored licks and literal quotations remain musically legitimate jazz memory.
Storage/privacy policy is separate from musical legitimacy.

When private exact vocabulary is available, runtime may still request:

- LITERAL_QUOTE
- TRANSPOSED_LICK
- ADAPTED_LICK
- FRAGMENT_RECALL
- ABSTRACTED_PATTERN
- HYBRID_COMPOSITION

according to the existing similarity / reuse / context policy.

## Promotion rule

Exact source material does not become a public runtime prior merely because it
was transcribed.

Typical promotion:

exact transcription
-> verified phrase observation
-> normalized/private vocabulary
-> abstract motif / tendency
-> contextual runtime prior

Every promotion must retain provenance and confidence.

## Applies to all legends

This rule is global, including but not limited to:

- Charlie Parker
- Bill Evans
- Scott LaFaro
- all future musician-specific Legend Intelligence packages
