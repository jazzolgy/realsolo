# Piano Player

AI Pianist workstream. Shared harmony/phrase/ensemble reasoning must come from Core.

## Runtime contract

The pianist follows the project-wide online improvisation rule:

**Plan intention, not notes.**

The shared Core may provide form, harmony, phrase, narrative, memory, ensemble state,
and soft plans. The piano layer owns only piano-specific realization.

Current piano-specific implementation:

- polyphonic `PianoVoicingCandidate`
- piano-local performance state
- immediate voicing/comping candidate evaluation
- voice-leading preference
- ensemble-space / density interaction policy
- call-and-response and anticipation tags
- tension-sensitive color handling
- commit exactly one immediately playable piano action, then listen/re-plan

## Boundary with Core

Do not duplicate or fork shared harmony, phrase, form, narrative, memory, ensemble,
or legend reasoning here.

If the piano workstream requires a shared representation or Core contract change,
document it first in `CORE_CHANGE_REQUEST.md`.
