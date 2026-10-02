# Portable Runtime Protocol v1

This is the stable boundary between RealSolo musical intelligence and the native
audio runtime.

## Ownership boundary

The portable musical core and instrument Players decide:

- pitch
- velocity
- duration
- beat-relative onset
- instrument role
- articulation semantics
- expression controls
- immediately committed gesture membership

The native audio runtime decides:

- sample file / sample layer
- round robin selection
- sample interpolation / crossfade
- envelopes and DSP implementation
- mixer / FX
- device audio clock mapping
- audio callback behavior

A Player must never emit a sample filename, SoundFont preset, sampler program,
platform audio handle, or DSP implementation command.

## Envelope

Every message crossing the future C ABI / FFI boundary is wrapped in a
`PortableRenderPacket`.

The packet contains:
- protocol version
- monotonically increasing sequence id
- EnsembleState generation
- tempo
- beat anchor
- one committed RenderGesture

Beat timing remains musical and platform-neutral. The native runtime maps the
packet's beat anchor to its own device/audio clock.

## Compatibility

Protocol v1 preserves the current RenderGesture fields. The generic
`expression_controls` map is intentionally open to new scalar controls so
instrument Players can evolve without forcing an ABI redesign for every new
expression dimension.

Existing convenience fields such as `attack_scale`, `release_shape`, and
`breath_before_beats` remain in v1 for compatibility.

## Golden fixture

`tests/fixtures/portable_runtime/render_packet_v1.json` is the canonical
cross-language fixture. Future Swift/Kotlin/C++/Rust implementations must parse
and re-emit its semantics without changing the musical meaning.

The JSON Schema is:
`protocol/portable_render_packet_v1.schema.json`.

## Versioning rule

- additive expression controls do not require a protocol bump
- changing field meaning, units, required timing semantics, or removing fields
  requires a new protocol version
- native runtimes must reject unsupported major protocol versions
