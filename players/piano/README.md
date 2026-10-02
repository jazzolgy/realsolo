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
