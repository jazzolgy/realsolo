# Realtime — Live Ensemble App

The product target is **audio-first, MIDI-parallel**.

RealSolo must be able to hear an ordinary acoustic performance through a phone,
tablet, laptop or interface microphone. MIDI is valuable when available, but it
must not be required for ensemble interaction.

## Input architecture

All live sources converge on the same realtime musical state:

```
phone / laptop / interface microphone
    -> PCM audio frames
    -> causal Audio Perception
       - level / energy
       - onset evidence
       - pitch evidence
       - later: polyphonic pitch, harmony, timbre, articulation
    -> AudioObservation ┐
                        ├-> Beat / Phrase / Cue -> EnsembleState -> Core
MIDI controller --------┘
```

The current Python audio adapter is a development harness using PortAudio via
`sounddevice`. The mobile product should implement the same contract natively
(e.g. AVAudioEngine/Core Audio on iOS) and feed equivalent timestamped evidence
to the shared runtime.

## Install for microphone + MIDI development

```bash
pip install -e ".[dev,live]"
realsolo-ensemble ports
```

Monitor a real acoustic instrument through the microphone:

```bash
realsolo-ensemble monitor-audio --device 0
```

Closed-loop audio perception with MIDI sound output:

```bash
realsolo-ensemble probe-audio --device 0 --output "YOUR MIDI OUTPUT"
```

This probe is not final accompaniment intelligence. It proves the required
closed loop: **hear acoustic performance -> derive evidence -> update ensemble
state -> Core immediate decision -> output -> listen again**.

The scheduler may cancel an unplayed future note after new evidence, but once a
note-on has sounded its cleanup note-off is mandatory.

## Development rule

Do not move music policy into the audio front-end. Perception reports evidence
and confidence; Music Intelligence Core decides what that evidence means in the
current musical context.
