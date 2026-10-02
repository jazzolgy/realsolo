# Piano Player

AI Pianist workstream. Shared harmony/phrase/ensemble reasoning and shared
polyphonic sonority semantics come from Core.

## Runtime contract

The pianist follows the project-wide online improvisation rule:

**Plan intention, not notes.**

The shared Core provides form, harmony, phrase, narrative, memory, ensemble state,
soft plans, `PolyphonicEventCandidate`, `VoiceEvent`, and generic polyphonic
evaluation. The piano layer owns only piano-specific realization.

Current piano-specific implementation:

- `PianoRealizationCandidate` wraps one shared Core polyphonic gesture
- acoustic-piano range validation
- piano hand assignment
- pedal mode
- touch metadata
- piano-specific feasibility penalties layered on top of Core evaluation
- staggered per-voice onsets are preserved as one musical gesture
- commit exactly one immediate piano realization, then listen/re-plan

## Boundary with Core

Core owns generic sonority, voice identity, spacing, register, doubling,
top/bass relations, generic voice-leading, orchestration semantics, and shared
polyphonic online evaluation.

Piano owns hand distribution, playable range, pedal, touch, physical feasibility,
and piano-specific voicing/comping grammar.

If future piano work reveals another genuinely shared musical concept, document it
first in `CORE_CHANGE_REQUEST.md` rather than duplicating it locally.


## Experimental context-aware comping slice

The first McNeely-derived vertical slice now lives in `comping.py`.

It deliberately tests only a small decision space:

- silence
- sparse support
- punctuation
- response
- sustained support

The current experimental context contains soloist activity, phrase-boundary
probability, available phrase space, bass/drummer activity, ensemble density,
recent piano density, section energy, and time feel.

These fields are piano-side research projections for now. They are **not** declared
stable shared-Core contracts yet.

The comping layer consumes a Core `HarmonicAffordance` by ID/alignment only; it does
not recreate chord-scale, tension, substitution, or harmonic-function theory.

Research rule: same harmony must be able to yield different immediate actions when
ensemble/phrase context changes, including choosing silence.
