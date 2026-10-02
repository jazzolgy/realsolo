# UMR v1.40 — Harmonic Interpretation Candidates

## Why this layer

The project instructions explicitly require Expected Harmony, Observed Harmony,
and Inferred Harmony to remain distinct. They also state that interpretation
tasks should preserve alternatives, evidence, confidence, model source, and
human correction rather than assume one uniquely correct answer.

That principle applies directly to harmony.

## Source support

The uploaded modal-harmony material gives a concrete musical reason for this
architecture: an upper quartal structure can sound tonic/modal when the modal
tonic is in the bass and non-tonic when another bass note is used. The same
surface pitch collection therefore does not determine one function by itself.

The project instructions further require uncertainty and ambiguity to be modeled
rather than collapsed into one scalar truth.

## v1.40 representation

A HarmonicHypothesis stores:
- identity / label
- root
- function
- key or mode
- interpretation family
- ConfidenceVector
- evidence
- contradictions
- provenance
- optional human correction

ConfidenceVector keeps separate support from:
- expected chart/schema
- observed audio/ensemble
- inferred analysis
- voice leading
- bass
- melody
- harmonic time
- modal context
- form
- human correction

These components are not destructively collapsed in storage.

## Ranking

rank_harmonic_hypotheses() produces:
- ranked candidate interpretations
- normalized probabilities
- ambiguity estimate
- top-two margin
- needs-more-evidence flag

The ranking score is an operational decision aid, not an assertion that the
preferred analysis is ontologically the one true analysis.

## Human correction

Human correction is appended as additional evidence/provenance while retaining
the original expected/observed/inferred confidences. This follows the project's
Human Correction principle: correction should become future learning evidence,
not erase the original interpretation history.

## Runtime behavior

High confidence / low ambiguity:
- the player may use the preferred hypothesis more strongly for current
  candidate evaluation.

High ambiguity:
- keep multiple interpretations alive;
- prefer actions compatible with several hypotheses when musically useful;
- gather more ensemble evidence;
- avoid unnecessary irreversible harmonic commitment.

This still obeys the runtime invariant:

Perceive -> maintain competing harmonic interpretations -> evaluate current
affordances -> commit one immediate action -> listen -> update hypotheses.
