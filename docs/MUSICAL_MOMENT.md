# MusicalMoment

`MusicalMoment` is the shared research/runtime representation for one aligned
musical situation.

It answers:

> What was happening together at this point in the performance?

It does **not** answer:

> Why did a musician do this?

or:

> Was the result good?

Those are later inference/evaluation questions.

## Structure

```text
MusicalMoment
├─ position
│  ├─ beat / bar
│  ├─ section
│  ├─ chorus
│  └─ form position
├─ harmony
│  ├─ expected ref
│  ├─ observed ref
│  ├─ inferred ref
│  ├─ local key ref
│  ├─ cadence state
│  └─ tension / confidence
├─ phrase
│  ├─ phrase id / position
│  ├─ maturity
│  ├─ boundary pressure
│  ├─ space
│  ├─ tension
│  └─ motif id
├─ groove
├─ Piano / Bass / Drums / other player actions
├─ interaction relations
├─ ensemble density / energy / tension / space
├─ confidence
├─ provenance
└─ source references
```

## Player-neutral action representation

A `MomentPlayerAction` describes behavior semantically:

- role;
- action type;
- interaction;
- density / energy / tension / space;
- normalized register center;
- phrase role;
- motif reference;
- semantic tags;
- confidence / provenance.

It does not contain concrete realization commands such as MIDI pitches,
voicings, strings/frets, or drum limbs/hits.

Those remain Player/Performance Evidence responsibilities.

## Observation, not explanation

A MusicalMoment may record:

```text
Piano density decreased
Bass entered foreground
Drums maintained support
phrase space increased
Bass interaction = answer
```

It must not silently rewrite this as:

```text
Piano caused Bass to enter
Bass entry was successful
therefore reinforce this behavior
```

Causal attribution and reward learning are outside this contract.

## Runtime bridge

`musical_moment_from_ensemble_state()` snapshots existing Shared Ensemble State
into the representation. It copies already-known facts and references; it does
not invent harmony confidence, phrase meaning, or player intention.

## Research use

For a trio study such as LaFaro / Evans / Motian, one aligned moment can hold the
three musicians' actions against the same form, harmony, phrase, groove, space,
and interaction state.

That enables study questions such as:

- what context preceded a Bass foreground entry?
- which phrase states coincide with rhythmic displacement?
- when does register expansion occur relative to Piano space and Drum activity?
- which relationships recur across tracks or musicians?

The result can later feed evidence, Legend/Learning/Motif layers, and then
`MusicalPolicyProjection` without requiring literal phrase copying.

## Intended learning flow

```text
Audio / Score / Performance Evidence
        ↓
aligned MusicalMoment
        ↓
relation / tendency study
        ↓
Learning / Legend / Motif
        ↓
MusicalPolicyProjection
        ↓
Player realization
```

The moment itself is descriptive and reusable by both research and runtime.
