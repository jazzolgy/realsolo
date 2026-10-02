# Jazz Piano Performance Grammar v0.1

Status: research design derived primarily from Jim McNeely, *The Art of Comping*,
with RealSolo architectural interpretation kept explicitly separate.

This document does **not** define universal jazz-piano law. It separates:

- **SOURCE-DERIVED** observations: directly supported by McNeely's workbook / paired recordings.
- **DESIGN INFERENCE**: proposed RealSolo representation motivated by those observations.
- **OPEN** items: require cross-source validation before promotion to shared grammar.

---

## 1. Central shift

### SOURCE-DERIVED

The workbook treats comping as a changing ensemble activity, not as a fixed sequence
of chord voicings. Across the six pieces, exercises repeatedly vary rhythm, amount of
activity, register, voicing size, substitutions, chromatic movement, phrase response,
and interaction with soloist/bass/drums.

The paired Listening / Playalong format also makes the student's own response part of
the pedagogy: the written/model part is not presented as the only valid realization.

### DESIGN INFERENCE

AI Pianist should be organized around a **performance decision grammar**:

```
Shared HarmonicFrame / HarmonicAffordances
          ↓
Perceived Ensemble + Phrase Context
          ↓
Interaction Intention
          ↓
Comping Action Family
          ↓
Voicing / Register / Density Candidate
          ↓
Piano Physical Realization
          ↓
Immediate Gesture Commit
          ↓
Listen Again
```

The primary runtime object is therefore not "the next chord voicing" but
"the next piano gesture serving a current interaction intention."

---

## 2. Interaction-role hypothesis

### SOURCE-DERIVED basis

McNeely's examples and exercises repeatedly distinguish moments where the pianist:

- supports the soloist,
- leaves room,
- punctuates,
- fills a gap,
- reinforces rhythmic/harmonic direction,
- increases energy,
- relaxes,
- responds to another player.

The book does not formalize these as an enum.

### DESIGN INFERENCE

Experimental piano-local role set:

```
LAY_OUT
SUPPORT
ANCHOR
PUNCTUATE
ANSWER
FILL
BUILD
RELEASE
```

These roles are **soft intentions**, not pattern generators.

Examples:

- `LAY_OUT`: silence is preferred unless new evidence demands intervention.
- `SUPPORT`: preserve harmonic/metric clarity with low intrusion.
- `ANCHOR`: make form/harmony/groove more explicit.
- `PUNCTUATE`: short event aligned with phrase or ensemble accent.
- `ANSWER`: respond to recently perceived material after rather than during it.
- `FILL`: occupy a genuine phrase-space window.
- `BUILD`: raise one or more of density, register, weight, activity, or tension.
- `RELEASE`: reduce pressure after a build/climax.

OPEN:
Cross-check these labels against at least one other comping pedagogy before making
them stable API names.

---

## 3. Silence must be first-class

### SOURCE-DERIVED

Space is repeatedly treated as a meaningful part of accompaniment. The player is asked
to compare different amounts of rhythmic activity and to react to phrase openings
rather than continuously filling the measure.

### DESIGN INFERENCE

Candidate selection must allow an immediate **silence/rest gesture**.

This cannot be represented merely as a very sparse voicing.

Suggested candidate family:

```
PianoCompingAction
  sounding_event: PolyphonicEventCandidate | None
  action_type: ...
  intended_duration_beats: ...
```

A silence action still has musical duration and intention.

OPEN:
Whether a shared Core "rest performance event" is needed should wait for bass/drums/
other player requirements. Do not request Core change yet.

---

## 4. Rhythm is not a post-processing layer

### SOURCE-DERIVED

Exercises in *Blues For Wanda*, *Crossroads*, *Karita*, and *Last Minute* explicitly
alter rhythmic placement/pattern while holding much of the harmonic situation stable.
The changed rhythm changes the comping effect.

### DESIGN INFERENCE

Do not:

```
choose voicing → attach arbitrary rhythm
```

Prefer joint gesture candidates:

```
harmonic realization
+ onset position
+ duration
+ articulation
+ density
+ register
+ interaction role
```

Scoring must include interaction terms, e.g. a dense voicing on a phrase boundary can
have a different value from the same voicing inside a busy solo phrase.

---

## 5. Density vector

### SOURCE-DERIVED

McNeely varies small/large voicings, rhythmic activity, sustain, register, and dynamic
weight independently. Therefore "busy" versus "sparse" cannot be inferred from note
count alone.

### DESIGN INFERENCE

Represent piano density as a vector rather than scalar:

```
PianoDensity:
  voice_count
  onset_rate
  sustain_ratio
  register_span
  registral_concentration
  dynamic_weight
  pedal_blur
```

A later policy may derive one convenience score, but the components should remain
available.

Example:
A five-note sustained chord once every two bars may be less intrusive than repeated
two-note stabs.

---

## 6. Register as ensemble interaction

### SOURCE-DERIVED

The workbook repeatedly asks the pianist to consider register and uses changing
voicing/register as part of chorus development.

### DESIGN INFERENCE

Piano register choice should consume ensemble information, not just hand feasibility.

Potential inputs:

- soloist register estimate,
- bass register/activity,
- current piano register,
- section energy,
- phrase role,
- top-note constraint from the musical context.

Potential local descriptors:

```
register_center
register_span
low_register_weight
top_voice_projection
collision_risk
```

OPEN:
`soloist_register` / `bass_activity` are likely shared ensemble-state concepts,
but should be corroborated in another instrument workstream/source before a Core request.

---

## 7. Phrase-space model

### SOURCE-DERIVED

The book frequently uses phrase gaps and solo breathing points as places where the
pianist may answer or fill, while other passages call for less intervention.

### DESIGN INFERENCE

Introduce an experimental piano-side concept:

```
PhraseSpaceWindow:
  confidence
  start_offset_beats
  estimated_length_beats
  source  # solo phrase boundary / held tone / rest / form point / etc.
```

The intent is not to reserve future notes. It describes an inferred opportunity.

Potential behavior:

- short window → punctuation/answer or lay out,
- medium window → fill/counterline candidate,
- no reliable window → avoid intrusive fill unless another role dominates.

This remains compatible with "Plan intention, not notes."

---

## 8. Energy / narrative control

### SOURCE-DERIVED

Across the pieces, comping often changes over a chorus or section through voicing size,
activity, register, dynamics, or texture. *Last Minute* is particularly useful for
sustained/modal harmony where harmonic changes alone cannot generate development.

### DESIGN INFERENCE

Treat performance energy as multi-parameter trajectory:

```
EnergyIntent:
  direction: DOWN | STABLE | UP
  target_density
  target_register
  target_dynamic_weight
  target_harmonic_color
```

This should bias immediate candidates rather than freeze a future progression.

The existing `SoftPlan.density_direction` and `register_direction` are useful but
probably insufficient for full comping behavior.

---

## 9. Internal motion inside accompaniment

### SOURCE-DERIVED

*Crossroads*, *'Round Midnight*, *Karita*, and *Last Minute* contain exercises involving
chromatic approach, moving inner lines, passing/approach harmony, neighbor structures,
or contrary-motion patterns.

### DESIGN INFERENCE

A piano gesture can be evaluated on both:

- vertical sonority meaning,
- horizontal local voice-motion meaning.

CR-001 already provides stable voice identity, which is the correct substrate.

Possible piano descriptors:

```
inner_voice_motion
chromatic_neighbor
approach_gesture
contrary_motion
planed_motion
```

Do not convert these into fixed licks.

---

## 10. Groove identity versus literal repetition

### SOURCE-DERIVED

*Karita* uses Latin/bossa-related rhythmic material and exercises variation of pattern
order and placement rather than requiring mechanical repetition.

### DESIGN INFERENCE

Represent groove at two levels:

```
GrooveSchema  # stable rhythmic character
GestureVariant  # current realization
```

A RealSolo pianist may preserve groove identity while varying exact attacks.

OPEN:
GrooveSchema is likely cross-instrument Core/realtime knowledge and should be discussed
with the ensemble/realtime workstream rather than embedded permanently in piano.

---

## 11. Voicing-family competition

### SOURCE-DERIVED

The workbook presents multiple structural voicing approaches, especially in later
sections: quartal, inverted quartal, tertian, combination, octave structures, plus
upper-structure examples and different voicing sizes/registers.

### DESIGN INFERENCE

Shared Harmony should not select a piano voicing family.

Given the same `HarmonicAffordance`, piano candidate generation can propose several
realizations:

```
shell
rootless
tertian_open
quartal
inverted_quartal
upper_structure
octave
mixed
```

Then evaluate them using:

- harmonic affordance fit from Core,
- top/bass constraints,
- current interaction role,
- previous voice identities,
- register/collision,
- density/energy target,
- physical piano feasibility,
- style evidence.

OPEN:
Family names/taxonomy should stay provisional until compared with additional voicing
texts. McNeely alone should not define the universal taxonomy.

---

## 12. Connection to v1.34 Shared Jazz Harmony

The new Core layer is a good fit for this research.

Example:

```
HarmonicFrame:
  Expected G7
  Inferred G7alt
  next_expected Cmaj7
  tension .72

Core affordances may include:
  dominant.stable_identity
  dominant.altered_color
  future_harmony.anticipation
  outside.return_path
```

Piano should not reinterpret G7 independently.

Instead:

```
dominant.altered_color
+ BUILD
+ phrase-space available
+ medium ensemble density
→ generate several piano gesture candidates
→ choose voicing family / register / tension distribution / rhythm
→ commit one gesture
```

A different context could yield:

```
dominant.altered_color
+ LAY_OUT
+ high soloist activity
→ silence
```

Thus harmonic availability and the decision to sound are separate.

---

## 13. Audio-pair technical finding

### OBSERVED FROM SUPPLIED FILES

All six Listening/Playalong pairs have closely related durations and correspond to the
same pieces/forms.

Initial automated comparison of *Blues For Wanda* found strong similarity in
onset-envelope timing after an approximately two-second alignment offset, but the raw
waveforms are not phase-identical.

Therefore the pair should **not** be treated as guaranteed identical backing mixes from
which piano can safely be isolated by direct waveform subtraction.

### RESEARCH CONSEQUENCE

Use:

- score/form alignment,
- beat/onset alignment,
- Listening-track piano/ensemble analysis,
- Playalong track as contextual comparison,

rather than assuming:

```
Listening - Playalong = clean piano stem
```

Any future source-separation output must be marked estimated.

---

## 14. First implementation target after research pass

Do **not** build a large voicing generator yet.

First create a minimal end-to-end comping decision slice that can compare:

1. silence,
2. sparse support gesture,
3. short punctuation,
4. response gesture,

under a small set of ensemble contexts.

Each sounding candidate should use the shared `PolyphonicEventCandidate`.

The experiment should answer:

- can the pianist choose silence when appropriate?
- can the same harmony produce different behavior under different phrase contexts?
- can density/register direction alter realization without changing harmonic meaning?
- can one Core HarmonicAffordance support multiple piano voicing families?
- does the system still commit only one immediate gesture and re-listen?

---

## 15. Promotion rule

A concept moves from this research document into stable Piano Grammar only when one of
the following holds:

- it is explicitly supported across multiple McNeely examples and survives expert review,
- it is independently supported by another professional source,
- or it is validated through controlled expert preference tests.

A concept moves from Piano into Shared Core only when it is demonstrably
instrument-independent.

