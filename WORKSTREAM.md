# Workstream: Live Ensemble App

Owns:
- chord-chart presentation and playback transport
- user-role / AI-role session configuration
- audio input and optional MIDI input
- cue recognition
- beat/form tracking
- ensemble-state updates
- low-latency scheduling
- performance output
- live UI

## Product stages

### Stage 1
A complete chart + playback application that works without microphone input.
The user can play as soloist while RealSolo accompanies, or comp while RealSolo
acts as soloist.

### Stage 2
Microphone-first interactive ensemble behavior is layered on top of Stage 1.

The runtime must commit only immediately playable events, listen again, and
re-plan. Musical policy comes from Core.
