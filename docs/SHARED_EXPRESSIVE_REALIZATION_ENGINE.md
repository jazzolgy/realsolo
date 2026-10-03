# Shared Expressive Realization Engine

RealSolo separates four musical layers:

WHAT = notes / vocabulary / motif  
WHEN = beat / subdivision / duration  
WHY = harmony / form / interaction / phrase intention  
HOW = dynamics / accent / body / timing / foreground weight

The HOW layer is implemented in `expressive_realization.py`.

Shared outputs are instrument-neutral:
- perceptual intensity
- dynamic level
- accent strength
- note body
- timing emphasis
- phrase contour
- foreground weight
- articulation pressure
- brightness pressure

Inputs include phrase/form position, tension, ensemble density, register,
repetition index, motif operation, foreground/background role, climax/release
pressure, and available space.

`ExpressionProfile` is stored separately from lick/motif identity. One musical
identity may therefore have multiple observed expressive realizations.

Relative contour is preserved while absolute level adapts to context. Repeated
material also varies expression rather than simply becoming louder each time.

Players translate Shared intention into physical controls:
- Piano: velocity, touch, note body, voicing/pedal-capable controls
- Sax: air, attack, brightness, vibrato, note body
- Bass: pluck strength, body, release, ghost relation
- Drums: stroke intensity, articulation, surface, ghost contrast

The quartet runtime now exports Shared expression controls for Sax, Piano, Bass
and Drums. Browser rendering consumes timing/body/intensity hints where the
current sample engine supports them.

Causal order remains:

selected immediate event
→ Shared Expressive Realization
→ Player realization
→ commit
→ listen again

Future research targets include phrase dynamic shape, accent grammar, motif
development dynamics, vocabulary expression profiles, tension/register coupling,
foreground/background dynamics, repetition variation, cadential release, and
climax construction.
