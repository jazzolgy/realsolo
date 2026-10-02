# McNeely Comping Study v0.1

Source: Jim McNeely, *The Art of Comping* (workbook + paired listening/playalong recordings supplied by the project owner).

Purpose: extract evidence-backed comping concepts and candidate AI Pianist behaviors without treating one author's examples as universal jazz-piano law.

Status: first deep-pass study map. Detailed audio-aligned event annotation is the next step.

---

## 1. Why this source matters

This workbook is unusually useful for RealSolo because it does not present comping as a static chord-to-voicing lookup problem.

Its recurring study loop is:

1. listen to an ensemble performance with piano,
2. inspect the written example and discussion,
3. hear the same musical environment without the pianist,
4. make one's own comping decisions,
5. vary rhythm, voicing, register, density, dynamics, and interaction.

That structure maps naturally onto RealSolo's runtime principle:

```
listen → interpret context → prepare intention/candidates
→ commit one immediate gesture → listen again → re-plan
```

The source therefore supports development of a contextual comping policy, not merely a voicing dictionary.

---

## 2. Source set

### Workbook sections

- Introduction
- General Suggestions
- Blues For Wanda
- Crossroads
- 'Round Midnight
- Karita
- Give and Take
- Last Minute
- Suggested Listening

### Paired audio

Each piece has:

- one Listening Track with the model performance,
- one Playalong Track intended for the pianist to supply a new comping part.

Approximate durations observed from the supplied MP3 files:

| Piece | Listening | Playalong |
| --- | ---: | ---: |
| Blues For Wanda | 3:22 | 3:25 |
| Crossroads | 5:03 | 5:07 |
| 'Round Midnight | 7:57 | 7:57 |
| Karita | 3:47 | 3:49 |
| Give and Take | 6:11 | 6:14 |
| Last Minute | 3:43 | 3:41 |

Small duration differences mean score/form alignment should be structural rather than assuming identical sample indices.

---

## 3. General comping dimensions explicitly foregrounded by the workbook

The introductory material repeatedly asks the player to listen for and vary dimensions such as:

- interaction with the soloist,
- interaction with drums,
- relationship with bass,
- amount of space,
- rhythmic placement,
- register,
- voicing weight / size,
- dynamics,
- articulation,
- phrase-level development,
- whether the accompaniment supports, answers, anchors, builds, or leaves room.

AI implication:

A comping evaluator cannot be reduced to:

```
current chord → legal voicing → choose nearest
```

A more faithful abstraction is:

```
ensemble context
→ interaction intention
→ rhythmic action
→ sonority / voicing family
→ register and density
→ piano realization
→ immediate gesture
```

---

## 4. Piece studies

## 4.1 Blues For Wanda

### Pedagogical role

The blues acts as the clearest baseline environment for learning comping interaction.

The workbook asks the player to experiment with:

- different rhythmic placements,
- anticipation,
- short versus longer durations,
- two-and-four / offbeat-oriented possibilities,
- different activity levels,
- different voicings over the same progression,
- substitutions,
- comping with more or less rhythmic density,
- leaving space,
- responding to solo phrase shape,
- interaction during trading and bass/drum contexts.

### AI Pianist concepts

High-value state variables:

- `recent_piano_density`
- `soloist_activity`
- `phrase_boundary_probability`
- `metric_position`
- `interaction_role`
- `ensemble_activity`

Candidate action families:

- `LAY_OUT`
- `SHORT_STAB`
- `ANTICIPATE`
- `SUSTAIN`
- `ANSWER`
- `ANCHOR`

Important lesson:

Rhythmic placement itself changes the musical meaning even if the chord/voicing remains unchanged.

---

## 4.2 Crossroads

### Pedagogical role

This section broadens the vocabulary beyond basic comping patterns.

The exercises include:

- chromatic upper-neighbor motion,
- half-step approach into chordal targets,
- embellishment of chord voicings,
- moving internal chromatic lines,
- ostinato-derived rhythmic comping,
- energy building across a chorus,
- occasional fills,
- larger voicings,
- octave voicings.

### AI Pianist concepts

A voicing candidate may contain an internal trajectory or voice motion while still being one immediate/current gesture.

Need to distinguish:

- vertical harmonic validity,
- horizontal inner-voice motion,
- rhythmic identity,
- energy contribution.

Potential descriptors:

- `inner_voice_motion`
- `chromatic_approach`
- `ostinato_reference`
- `register_expansion`
- `voicing_weight`

Important lesson:

Comping development can come from moving an inner voice while preserving the larger harmonic role.

---

## 4.3 'Round Midnight

### Pedagogical role

Ballad context makes timing, sustain, resonance, space, chromatic movement, and long-form support especially audible.

The workbook discusses or demonstrates:

- sustained/long voicings,
- use of pedal,
- chromatic movement,
- approach chords,
- passing harmonies,
- fills between melodic phrases,
- different accompaniment behavior for different soloists,
- double-time sections versus rubato/ballad sections.

### AI Pianist concepts

The same harmonic progression should yield different policies under:

- rubato,
- ballad pulse,
- double-time feel,
- soloist phrase density,
- different ensemble roles.

Potential state:

- `time_feel`
- `phrase_space_window`
- `sustain_budget`
- `pedal_blur_risk`
- `fill_opportunity`

Important lesson:

The pianist should model available temporal space, not merely current harmony.

---

## 4.4 Karita

### Pedagogical role

Latin/bossa-oriented material emphasizes pattern identity while warning against mechanical repetition.

The section explores:

- clave-related or Latin-derived rhythmic shapes,
- repeating accompaniment cells,
- changing the order/placement of rhythmic figures,
- preserving ensemble feel while varying the piano part,
- larger voicings in later sections,
- moving internal lines,
- embellishment,
- upper-structure material,
- octave voicings.

### AI Pianist concepts

Need a distinction between:

```
groove identity
```

and

```
literal pattern repetition
```

A groove can remain stable while local realization changes.

Potential representation:

- `groove_schema_id`
- `pattern_variant_id`
- `syncopation_profile`
- `variation_pressure`
- `ensemble_lock_strength`

Important lesson:

A style grammar should constrain rhythmic character without forcing exact repetition.

---

## 4.5 Give and Take

### Pedagogical role

The title itself reflects reciprocal ensemble behavior.

The section emphasizes:

- comping through changing phrase lengths/sections,
- varying size of voicings,
- occasional fills,
- dynamic interaction,
- moving between harmonic support and melodic/rhythmic response,
- substitutions and harmonic color,
- changing texture depending on solo and section.

### AI Pianist concepts

This strongly supports an explicit interaction-role layer.

Candidate roles:

```
SUPPORT
PUNCTUATE
ANSWER
FILL
BUILD
RELEASE
ANCHOR
LAY_OUT
```

These should be intentions or policy states, not hardcoded output patterns.

Important lesson:

Comping role can change within the same chorus without any change in chord vocabulary.

---

## 4.6 Last Minute

### Pedagogical role

The fast/modal context provides a laboratory for sustained harmony and energy shaping.

The workbook explicitly presents multiple voicing families, including:

- quartal,
- inverted quartal,
- tertian,
- combination structures,
- octave voicings.

It also develops:

- larger phrase construction,
- contrary-motion ideas,
- chromatic motion,
- neighbor-voicing exercises,
- rhythmic pattern variation,
- increasingly active or heavier comping.

### AI Pianist concepts

This is especially valuable for candidate-family competition.

For one harmony, candidate generation should be able to propose structurally different sonority families:

```
quartal
inverted_quartal
tertian
mixed
octave
```

and let context/style/narrative choose among them.

Important lesson:

Long harmonic duration does not imply static accompaniment. Development can occur through register, internal motion, rhythm, density, and family changes while harmonic identity remains stable.

---

## 5. Cross-piece grammar emerging from the source

The following concepts recur strongly enough to become candidates for a general Jazz Piano Comping Grammar.

### 5.1 Space is an action

Silence should be a candidate in the same decision set as sounded gestures.

It may be chosen because:

- soloist activity is high,
- a phrase needs room,
- the previous piano event was dense,
- drums/bass already supply enough information,
- withholding increases later impact.

### 5.2 Rhythmic placement carries meaning

Two identical voicings at different metric locations are different comping actions.

Need representation for:

- anticipation,
- on-beat support,
- offbeat punctuation,
- delayed response,
- sustained support,
- repeated rhythmic cell.

### 5.3 Density is multidimensional

Do not define density only as number of notes.

Track separately:

- voice count,
- register span,
- chordal weight,
- event frequency,
- duration/sustain,
- pedal,
- dynamic weight.

### 5.4 Register is interactive

Register choice should consider:

- soloist register,
- bass register/activity,
- previous piano register,
- energy trajectory,
- desired texture.

### 5.5 Voicing and rhythm are coupled

A large dense voicing played once may be less intrusive than repeated two-note attacks.

Therefore candidate evaluation must inspect the whole gesture, not score sonority and rhythm independently and simply add them.

### 5.6 Phrase-scale energy matters

The source repeatedly encourages changing:

- activity,
- voicing size,
- register,
- dynamics,
- rhythmic intensity

over larger stretches.

This supports the existing RealSolo concept of narrative / tension trajectory.

### 5.7 Interaction is role-based

The pianist does not have one permanent accompaniment role.

A useful policy layer is:

```
InteractionRole
  LAY_OUT
  SUPPORT
  ANCHOR
  PUNCTUATE
  ANSWER
  FILL
  BUILD
  RELEASE
```

These roles should bias candidate selection rather than prescribe exact notes.

---

## 6. Candidate data additions suggested by this source

Piano-local or shared fields to consider experimentally:

### Context

- soloist_activity
- soloist_register
- soloist_phrase_boundary_probability
- bass_activity
- drummer_activity
- ensemble_density
- section_energy
- recent_piano_density
- recent_piano_register
- available_space_window
- time_feel
- groove_schema

### Intention

- interaction_role
- density_direction
- register_direction
- energy_direction
- sustain_intention
- answer_strength

### Gesture descriptors

- rhythmic_action_type
- voicing_weight
- register_center
- register_span
- event_duration
- pedal_amount
- touch
- internal_voice_motion
- groove_variant
- onset_spread

Do not promote all fields to Core immediately. First determine which concepts recur in other instruments and sources.

---

## 7. Counterfactual training/evaluation method inspired by the exercises

The workbook repeatedly asks the player to keep some musical material fixed while changing one dimension.

This suggests a useful RealSolo evaluation framework.

For a fixed ensemble context, generate paired alternatives such as:

- same voicing, different onset,
- same rhythm, different register,
- same harmony, sparse vs dense,
- same gesture, pedal vs dry,
- same progression, root-present vs rootless,
- same phrase point, answer vs silence,
- same groove identity, literal repeat vs variation.

Expert labeling can then answer:

```
Which candidate better serves this context, and why?
```

This is more informative than asking experts to author complete ideal performances.

---

## 8. What this source does NOT establish by itself

Do not infer from this workbook alone that:

- one voicing family is universally preferred,
- one rhythmic pattern defines jazz comping,
- roots should always be omitted,
- minimum voice motion is always best,
- dense playing is always wrong under an active soloist,
- McNeely's examples define all jazz eras/styles,
- notated examples fully encode microtiming, touch, or ensemble perception.

Those require comparison with other pedagogies, recordings, and expert judgment.

---

## 9. Audio study plan

Next pass should align each Listening Track to the workbook's form and compare it with the corresponding Playalong Track.

For each section/chunk annotate:

```
form_position
ensemble_state
soloist_activity
piano_onset_density
piano_space
register_band
voicing_weight
gesture_duration
interaction_role
energy_direction
notable_response_event
```

The goal is not exact note transcription first.

The first goal is to recover the **decision grammar**:
why the pianist acts, waits, changes density, changes register, answers, sustains, or builds.

---

## 10. Status for RealSolo

Evidence from this source strengthens the following architecture:

```
Music Intelligence Core
  → musical / ensemble context
  → phrase / narrative / energy state
  → interaction intention

Jazz Piano Grammar
  → comping action family
  → voicing family candidates
  → rhythmic placement candidates
  → piano realization

Shared + Piano evaluators
  → immediate gesture selection

Runtime
  → commit one gesture
  → listen again
```

This study should be compared against at least one substantially different jazz-piano
voicing/comping source before promoting detailed McNeely-specific tendencies into
SharedJazzPianoGrammar.
