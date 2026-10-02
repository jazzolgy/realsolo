# Bill Evans Trio Role Study — Pass 2: verified track map

## Why the track list changes the study

The supplied timestamps convert the earlier anonymous 24-region survey into a
usable historical comparison set.

The compilation contains three different kinds of material:

1. **Paul Motian / Bill Evans trio recordings** across several contexts:
   - Scott LaFaro era
   - Chuck Israels era
   - live Village Vanguard
   - studio Portrait in Jazz / Explorations / Moon Beams / How My Heart Sings!

2. **Eliot Zigmund / Eddie Gomez comparison recordings** from the
   `You Must Believe in Spring` sessions.

3. **non-drum recordings** such as `Peace Piece` and the Bennett/Evans
   `Some Other Time`, which must not contaminate drummer behavior estimates.

This means the source can support both:
- a broad **Bill Evans trio drummer-role study**
- a more specific **Motian vs Zigmund realization comparison**

The second comparison must remain context-controlled: differences may arise
from repertoire, recording era, bassist, arrangement, production, or drummer.
Do not attribute every measured difference directly to the drummer.

## Finding A — Waltz For Debby: role changes at a metric/form transition

External form analysis and discographic sources identify the famous 1961 trio
performance as beginning in 3/4 and moving to 4/4 for improvisation.

In the local audio, a strong surface change appears around **73–75 seconds**:
high-frequency spectral centroid rises sharply while transient activity becomes
more stable. This is consistent with a cymbal/time-surface change near the
metric transition, but signal evidence alone cannot label a specific drum stroke.

Engineering consequence:
**meter/feel transition should be a role change, not automatically a fill event.**

The drummer may clarify a new pulse primarily through:
- cymbal surface
- pulse hierarchy
- bass interaction
- density rebalancing

rather than "announce section change with fill."

## Finding B — Autumn Leaves: position inside the head matters

The project lead sheet gives a 32-bar standard form. A published listening guide
for this exact Portrait in Jazz performance marks:
- 0:00 arranged intro
- about 0:08 head begins
- about 0:28 B section begins

It describes Motian using light brush swing during the head while LaFaro initially
uses a nonstandard three-note grouping, then moves toward normal walking in the
B section.

The local audio confirms a large timbral/activity change inside the first
~40 seconds rather than one stationary accompaniment surface.

Engineering consequence:
**the drummer should react not only to "head vs solo" but to section-local rhythm
section responsibility.**

If the bass is metrically ambiguous or contrapuntal, drums may carry more pulse
clarity while remaining dynamically light. When bass returns to walking, the
drummer can gain surface freedom.

## Finding C — form repetition does not imply repeated drum realization

Autumn Leaves is a repeated 32-bar form. Chroma recurrence in the local recording
shows a strong cycle around **37.1 seconds**, corresponding to roughly **207 BPM**
for a 32-bar 4/4 chorus.

Yet attack density and spectral brightness do not repeat identically every cycle.
The middle of the performance becomes markedly brighter and more active than the
opening, then later contracts.

Therefore:
**same form position + different chorus history = different valid drummer action.**

Required inputs for drums:
- form position
- chorus index / development stage
- recent ensemble density
- recent drummer density
- current bass role
- current piano phrase ownership

## Finding D — Blue In Green: circular form requires non-obvious boundary handling

The score in the uploaded Real Book is a compact circular form, and external
references identify the standard as a 10-bar form.

Audio chroma recurrence in this recording shows a strong period near
**36.6 seconds**, consistent with repeated compact form cycles at ballad tempo.

A circular form is especially important for AI drums:
bar 1 is not necessarily a place to "mark the top" strongly.

Engineering consequence:
form boundary confidence and **boundary salience** must be separate variables.

A drummer may know with high confidence that the form restarted while choosing:
- no fill
- no crash
- brush continuation
- one color change
because perceptual continuity is part of the musical design.

## Finding E — Without A Song: foreground ownership is explicitly reassigned

The 1977 recording has a documented Eliot Zigmund drum solo around **6:52**.
Local transient activity rises around that part of the track.

This is an important counterexample to a naive "drummer should stay restrained"
policy.

Before the drum-solo allocation, restraint and accompaniment can be appropriate.
When the role assignment changes, a large increase in drummer foreground activity
becomes correct.

Therefore:
**restraint must be role-conditional, not globally preferred.**

## Motian vs Zigmund preliminary whole-mix positional proxy

Mean transient activity by normalized track position:

- Paul Motian-context tracks: 10% 3.56, 30% 4.52, 50% 4.49, 70% 4.35, 90% 4.00
- Eliot Zigmund-context tracks: 10% 3.62, 30% 4.13, 50% 5.10, 70% 4.19, 90% 3.18

These are whole-mix proxies, not isolated drum-hit counts.
They currently support only a weak hypothesis:
the Zigmund subset in this compilation shows a stronger mid-performance expansion
and stronger late contraction than the Motian subset.

Do not promote this to a LegendProfile until source-separated or manually
annotated evidence supports it.

## New drummer-role state hypothesis

The study increasingly suggests that the drummer needs a role state above
surface gesture selection:

- TIME_CLARIFIER
- TEXTURE_SUPPORT
- PHRASE_LISTENER
- COUNTERVOICE
- TRANSITION_AGENT
- DEVELOPMENT_PARTNER
- FOREGROUND_SOLOIST
- RELEASE_SUPPORT

This role should be conditioned by:
**score/form position + current ensemble texture + chorus history + explicit role
allocation**, not by energy alone.

Do not implement this enum yet. Continue evidence collection first.
