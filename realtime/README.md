# Realtime — Live Ensemble App

RealSolo now has two product stages.

## Stage 1 — Chart + Playback

No microphone is required.

The user sees a chord chart and the app owns a deterministic chart transport:
tempo, beat, bar, form, section and expected harmony.

The user chooses a playing role:
- **Soloist** -> RealSolo provides accompaniment.
- **Comper** -> RealSolo provides the soloist.

This makes the first product useful before interactive listening is enabled.

## Stage 2 — Interactive Ensemble

The product target remains **audio-first**. The phone/tablet/laptop microphone
listens to the real performance and updates the ensemble state so the AI can
follow, respond and revise uncommitted intentions.

MIDI is optional and primarily useful for digital-instrument users, testing and
development ground truth. It is not a required product workflow.

See:
- `docs/PRODUCT_STAGES.md`
- `docs/AUDIO_FIRST_RUNTIME.md`
