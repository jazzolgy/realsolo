# UMR v1.35 — Functional Graph + Contextual Tension

## Source basis

This pass is grounded primarily in the uploaded Berklee Harmony 2/3/4 materials,
Berklee Getting Inside Harmony 2: Melodic and Harmonic Tensions, and Berklee
Jazz Composition: Modal Harmony.

The sources are treated as pedagogical/theoretical evidence, not as universal
empirical laws. The runtime keeps alternate analyses and confidence rather than
silently turning textbook categories into hard truth.

## 1. Dominant function is a relationship, not a chord suffix

The new HarmonicFunctionGraph separates a chord/node from its outgoing
functional expectations.

Berklee Harmony 2 distinguishes secondary and extended dominants partly by
harmonic rhythm / metric stress and by whether dominant motion continues.
Harmony 3 distinguishes substitute dominant resolution by half-step from the
perfect-fifth expectation of primary/secondary dominants. Harmony 4 shows that
dominant function can survive deceptive resolution and also introduces
special-function dominant uses.

Therefore v1.35 represents primary, secondary, extended, substitute, extended
substitute and special-function dominants; expected versus actual resolution;
metric stress; and continuation of dominant chains.

A deceptive destination does not retroactively erase the source dominant
hypothesis.

## 2. Tension is role-dependent

Getting Inside Harmony 2 explicitly separates melodic and harmonic tension.
A scale note that conflicts with the chord may remain useful as a stepwise
melodic approach while being undesirable in supporting harmony.

The same pitch can therefore receive different evaluations depending on melody
versus supporting harmony versus bass versus inner voice, duration, metric
placement, stepwise resolution versus leap, chord-symbol inclusion, altered
arrangement status, exposure, register sensitivity, and modal context.

This replaces a single allowed/avoid switch with a multidimensional
TensionAssessment.

## 3. Modal exception to tonal avoid-note logic

The modal-harmony source emphasizes that a tritone can help establish a mode
when supported by the modal tonic in the bass, and that quartal voicing reduces
the major/minor tonal pull associated with tertian structures.

v1.35 therefore does not classify a modal characteristic tone as a universal
avoid note. Bass anchoring and voicing topology will be added to the modal state
layer rather than baked into one tension table.

## 4. Architectural boundary

Shared Core owns functional hypotheses and relationships, expected versus actual
resolution, harmonic-rhythm / stress context, tension-role semantics, and
confidence/provenance.

Instrument layers own exact voicing, hand/fingering feasibility, register
realization, articulation/touch/pedal, and physical execution.

## 5. Runtime invariant

No new object contains a future line or fixed future voicing sequence.

Harmony produces relationship hypotheses and affordances. The player still
commits one immediate action and then listens/re-plans.
