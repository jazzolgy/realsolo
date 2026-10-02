# BebopStyleProfile v0.1

This profile is intentionally **not** a named-drummer model and intentionally
does not claim that one numerical setting defines bebop.

## Why an evidence-aware profile

The Parker compilation study and uploaded bop methods support a number of strong
qualitative relationships, but they do not yet support precise event
probabilities for every kit voice.  Therefore each prior carries provenance:

- METHOD_SUPPORTED
- AUDIO_SUPPORTED
- HISTORICALLY_SUPPORTED
- ENGINEERING_PROVISIONAL

A value can be useful for candidate scoring while still being marked
provisional.

## Current high-confidence relationships

- ride is the primary time-bearing drum-set voice;
- ride surface is more flexible than a fixed two-beat loop;
- pedal hi-hat 2&4 is a strong anchor but not a compulsory event;
- snare/bass comping should be selective and phrase-aware;
- quiet bass-drum floor support is a different intention from interactive
  bass-drum accents;
- form boundaries create punctuation opportunities rather than mandatory fills;
- soloist activity must not directly determine drummer density.

## Online adapter

`bebop_runtime.py` now wraps the generic immediate-gesture candidates.

The adapter adds:
- explicit intentional-non-response candidate;
- explicit low-dynamic bass-floor-support candidate;
- BUILD / COAST / COME_DOWN / HANDOFF interaction scoring;
- phrase-pacing penalty after recently dense drummer activity;
- ride salience reinforcement;
- form-boundary opportunity weighting.

This does not precompose a bar.  Every choice is still one immediate gesture
followed by listening and re-planning.

## Important limitation

The current numerical weights are **engineering priors**.  They must not be used
as claims about Max Roach, Kenny Clarke, Roy Haynes, or any other individual
drummer.

The next calibration step is expert/timestamp annotation on identified audio
segments, followed by pairwise A/B musical evaluation.
