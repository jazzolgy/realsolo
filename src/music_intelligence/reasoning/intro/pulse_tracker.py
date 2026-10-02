"""Shared intro pulse, tempo, beat-phase, and meter tracking."""
from __future__ import annotations

from statistics import mean, pstdev

from .representation import (
    IntroObservation,
    IntroState,
    MeterHypothesis,
    clamp01,
    with_generation,
)


def _tempo_from_iois(iois: tuple[float, ...]) -> tuple[float | None, float]:
    if not iois:
        return None, 0.0
    avg = mean(iois)
    if avg <= 0:
        return None, 0.0
    tempo = 60.0 / avg
    if len(iois) == 1:
        return tempo, 0.35
    cv = pstdev(iois) / avg if avg else 1.0
    stability = clamp01(1.0 - min(1.0, cv * 4.0))
    return tempo, stability


def update_pulse_state(
    state: IntroState,
    observation: IntroObservation,
) -> IntroState:
    state.validate()
    observation.validate()

    observed_tempo, observed_stability = _tempo_from_iois(observation.iois_seconds)
    tempo = state.tempo_estimate_bpm
    if observed_tempo is not None:
        tempo = observed_tempo if tempo is None else 0.6 * tempo + 0.4 * observed_tempo

    pulse_evidence = observed_stability
    if observation.vocal_count_confidence > 0:
        pulse_evidence = max(pulse_evidence, observation.vocal_count_confidence * 0.9)
    if observation.pickup_confidence > 0 and observation.iois_seconds:
        pulse_evidence = max(pulse_evidence, observation.pickup_confidence * 0.7)

    # Rubato evidence suppresses confidence in a fixed pulse, without erasing
    # the tempo hypothesis completely.
    pulse = clamp01(
        0.72 * state.pulse_confidence
        + 0.28 * pulse_evidence
        - 0.22 * observation.rubato_confidence
    )
    stability = clamp01(
        0.7 * state.tempo_stability
        + 0.3 * observed_stability
        - 0.18 * observation.rubato_confidence
    )

    phase_conf = state.beat_phase_confidence
    if observation.beat_phase_hint is not None:
        phase_conf = clamp01(0.55 * phase_conf + 0.45 * max(pulse, 0.35))

    meters = list(state.meter_hypotheses)
    if observation.meter_hint is not None:
        n, d = observation.meter_hint
        previous = next(
            (m.confidence for m in meters if (m.numerator, m.denominator) == (n, d)),
            0.0,
        )
        new_conf = clamp01(0.6 * previous + 0.4 * max(pulse, 0.4))
        meters = [m for m in meters if (m.numerator, m.denominator) != (n, d)]
        meters.append(MeterHypothesis(n, d, new_conf))
        meters.sort(key=lambda m: m.confidence, reverse=True)

    return with_generation(
        state,
        pulse_confidence=pulse,
        tempo_estimate_bpm=tempo,
        tempo_stability=stability,
        meter_hypotheses=tuple(meters[:4]),
        beat_phase_confidence=phase_conf,
        provenance=state.provenance + ("intro_pulse_update",),
    )
