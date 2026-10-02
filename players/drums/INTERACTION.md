# Interactive Drum Solo / Trading

The next solo layer treats a drum solo as ensemble dialogue rather than a closed
monologue.

## Source boundary

The uploaded drum books strongly support motif development, orchestration,
space, rhythmic displacement, and listening/interaction principles.  The
current uploaded excerpts do **not** by themselves provide a complete formal
algorithm for jazz "trading fours/eights."  Therefore the trade scheduler below
is an engineering realization of the project's Shared Ensemble principles, not
a claim that one uploaded book defines a canonical trade algorithm.

## Motif projection

The drum layer receives a small read-only rhythmic projection of the phrase
heard immediately before its turn:

- normalized onset positions
- accent positions
- density
- energy direction
- syncopation
- terminal space
- source musical role

Shared Core remains owner of canonical motif and ensemble memory.

## Response relations

A trade response can choose among:

- echo
- rhythmic variation
- orchestral answer
- density contrast
- answer with space
- continue the previous energy direction
- resolve / hand the music back to the ensemble

Literal echo is deliberately penalized after repetition.  The aim is audible
relationship without parroting.

## Trading fours / eights

The local drum adapter supports four- and eight-bar response windows.  It does
not precompose those bars.  The window only shapes the current response policy.
Each gesture is committed individually, followed by listening and re-planning.

Near the end of the turn, resolution/re-entry becomes more valuable than
continued complexity.  This is essential for musical handoff.

## Four-limb solo realization

Solo vocabulary now has a separate default physical model for:

- right hand: ride/crash/snare/toms/auxiliary percussion
- left hand: snare/toms/auxiliary percussion
- right foot: bass drum
- left foot: hi-hat

Every simultaneous solo gesture is validated for both duplicate-limb collision
and default kit reachability.  This becomes the foundation for later
limb-conditioned rudiment/sticking, double-stroke, foot-ostinato, and advanced
independence models.
