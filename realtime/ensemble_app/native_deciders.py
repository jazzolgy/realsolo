from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping

from players.bass import (
    BassCommittedAction,
    BassContext,
    BassInteractionContext,
    BassMode,
    BassPerformanceMemory,
    choose_bass_interaction_intent,
    choose_immediate_bass_action,
)
from players.drums import (
    DrummerPerformanceMemory,
    DrummerRuntimeContext,
    DrummerSoftPlan,
    BebopPhraseMemory,
    SoloistEnergyProjection,
    BebopRuntimeProjection,
    perform_one_bebop_gesture,
    RideContinuityMemory,
    RideSurfaceAction,
    RidePhase,
    classify_ride_phase,
    update_ride_memory,
    SnarePhraseMemory,
    CompPhraseAction,
    update_snare_phrase_memory,
    DrumVoice,
    TimeFeel,
    perform_one_gesture,
)
from music_intelligence.corpus import ScoreContextSnapshot, ScorePosition
from music_intelligence.legends import LegendDomain
from music_intelligence.reasoning.legend_style_core import MusicalContextVector
from music_intelligence.reasoning.online_improviser import SoftPlan
from music_intelligence.reasoning.solo_runtime import build_solo_tick
from music_intelligence.reasoning.motif import (
    MotifEvaluationContext,
    MotifGenerationContext,
    MotifMemory,
)
from music_intelligence.reasoning.contextual_prior_gating import (
    improvisation_gating_context,
)
from music_intelligence.reasoning.musical_policy_projection import (
    project_musical_policy,
)
from players.sax import (
    SaxArcContext,
    SaxExpressionContext,
    SaxImmediateContext,
    SaxPhraseContext,
    SaxPhraseMemory,
    SaxPhysicalConstraints,
    apply_sax_arc,
    choose_sax_articulation_arc,
    choose_sax_expression,
    collect_legend_candidate_material,
    choose_sax_runtime_policy,
    generate_immediate_sax_candidates,
)
from players.piano import (
    PianoCompingContext,
    PianoCompingEvaluator,
    PianoCompingState,
    PianoVoicingRequest,
    build_immediate_performance_candidates,
    perform_one_comping_action,
)

from .player_contract import RenderGesture, RenderVoice
from .native_trio_players import Stage1BassNativeDecider
from .shared_intelligence_bridge import derive_shared_solo_moment
from .trio_adapters import NativeImmediateResult


_DRUM_MIDI = {
    DrumVoice.RIDE: 51,
    DrumVoice.CLOSED_HIHAT: 42,
    DrumVoice.OPEN_HIHAT: 46,
    DrumVoice.SNARE: 38,
    DrumVoice.BASS_DRUM: 36,
    DrumVoice.CRASH: 49,
    DrumVoice.HIGH_TOM: 50,
    DrumVoice.MID_TOM: 47,
    DrumVoice.FLOOR_TOM: 43,
    DrumVoice.COWBELL: 56,
    DrumVoice.CLAVE: 75,
}


def _ms_to_beats(ms: float, tempo_bpm: float) -> float:
    return (ms / 1000.0) * tempo_bpm / 60.0


def _latest_other_phrase_maturity(snapshot, player_id: str) -> float:
    values = [
        x.phrase_maturity
        for x in snapshot.intents
        if x.player_id != player_id
    ]
    return max(values, default=0.0)


def _soloist_activity(snapshot) -> float:
    soloist_ids = {
        p.player_id
        for p in snapshot.players
        if p.role.value in {"soloist", "melody", "leader"}
    }
    values = [
        max(i.density, i.energy, i.leadership)
        for i in snapshot.intents
        if i.player_id in soloist_ids
    ]
    return max(values, default=0.0)


@dataclass
class BassNativeDecider:
    """Compatibility facade over the canonical sequential Bass player.

    Realtime must not own a second bass musical policy.  The legacy class name
    remains for callers/tests, while all decisions delegate to the canonical
    Stage1BassNativeDecider / players.bass.BassSequentialRunner path.
    """

    mode: BassMode = BassMode.WALKING
    delegate: Stage1BassNativeDecider = field(default_factory=Stage1BassNativeDecider)

    @property
    def memory(self):
        return self.delegate.runner.memory

    def __call__(self, context: Mapping[str, object]) -> NativeImmediateResult | None:
        forwarded = dict(context)
        forwarded.setdefault("bass_mode", self.mode.value)

        # Walking harmony lives on the quarter-note spine. Swung offbeats are
        # optional ghost/dead-note opportunities, not a second harmonic bass
        # decision. This keeps the causal eighth-note ensemble clock without
        # turning walking bass into eight pitched attacks per bar.
        beat=float(forwarded.get("beat_in_bar",0.0))
        if forwarded["bass_mode"]=="walking":
            frac=beat%1.0
            forwarded.setdefault(
                "bass_ghost_only",
                abs(frac-.5)<=.08,
            )
        return self.delegate(forwarded)


@dataclass
class DrumsNativeDecider:
    memory: DrummerPerformanceMemory = field(default_factory=DrummerPerformanceMemory)
    feel: TimeFeel = TimeFeel.SWING
    bebop_phrase_memory: BebopPhraseMemory = field(default_factory=BebopPhraseMemory)
    ride_memory: RideContinuityMemory = field(default_factory=RideContinuityMemory)
    snare_memory: SnarePhraseMemory = field(default_factory=SnarePhraseMemory)

    def __call__(self, context: Mapping[str, object]) -> NativeImmediateResult | None:
        snapshot = context["ensemble_snapshot"]
        directive = context["interaction_directive"]
        beat = float(snapshot.transport.beat) % snapshot.transport.meter_numerator
        phrase_position = _latest_other_phrase_maturity(snapshot, "drums")
        energy = max(0.0, min(1.0, snapshot.ensemble_energy + directive.energy_delta))

        shared_feel = snapshot.groove.feel.value if snapshot.groove is not None else self.feel.value
        drum_feel = TimeFeel.SWING if shared_feel in {"swing","shuffle"} else TimeFeel.STRAIGHT
        plan = DrummerSoftPlan(
            feel=drum_feel,
            energy=energy,
            comping_density=max(.12, min(.82, .34 + directive.density_delta)),
            interaction_intent=directive.interaction.value,
            ride_velocity=int(round(58 + 34 * energy)),
        )
        dctx = DrummerRuntimeContext(
            position_in_bar_beats=beat,
            tempo_bpm=snapshot.transport.tempo_bpm,
            beats_per_bar=snapshot.transport.meter_numerator,
            phrase_position=phrase_position,
            ensemble_activity=snapshot.ensemble_density,
            soloist_activity=_soloist_activity(snapshot),
            energy_target=energy,
            section_transition=(
                snapshot.transport.form_position >= .96
                or directive.interaction.value == "transition"
            ),
            requested_kick="ensemble_kick" in directive.tags,
            harmonic_transition_confidence=float(context.get("harmonic_transition_confidence", 0.0)),
            harmony=context.get("harmonic_frame"),
            groove=snapshot.groove,
        )
        style_tags={str(x).lower() for x in context.get("style_tags", ())}
        if "bebop" in style_tags:
            sax_intent=snapshot.intent_for("sax")
            soloist=SoloistEnergyProjection(
                activity=(sax_intent.density if sax_intent is not None else .45),
                current_energy=(sax_intent.energy if sax_intent is not None else snapshot.ensemble_energy),
                energy_slope=0.0,
                phrase_terminal_probability=(
                    sax_intent.phrase_maturity if sax_intent is not None else phrase_position
                ),
                climax_probability=max(
                    0.0,
                    min(1.0,(sax_intent.tension if sax_intent is not None else snapshot.ensemble_tension)),
                ),
            )
            projection=BebopRuntimeProjection(
                soloist=soloist,
                phrase_memory=self.bebop_phrase_memory,
                bass=BebopRuntimeProjection.from_ensemble_state(
                    soloist=soloist,
                    phrase_memory=self.bebop_phrase_memory,
                    ensemble_state=snapshot,
                ).bass,
                ride_memory=self.ride_memory,
                snare_memory=self.snare_memory,
            )
            chosen=perform_one_bebop_gesture(plan,dctx,projection,self.memory)

            phase=classify_ride_phase(dctx)
            for action in RideSurfaceAction:
                if action.value in chosen.gesture.tags:
                    self.ride_memory=update_ride_memory(self.ride_memory,action,phase)
                    break
            normalized=(beat%snapshot.transport.meter_numerator)/snapshot.transport.meter_numerator
            for action in CompPhraseAction:
                if action.value in chosen.gesture.tags:
                    self.snare_memory=update_snare_phrase_memory(
                        self.snare_memory,
                        action,
                        phase=normalized,
                        bar_advance=.125,
                    )
                    break
            active=1.0 if chosen.gesture.hits else 0.0
            self.bebop_phrase_memory=BebopPhraseMemory(
                recent_comp_density=max(0.0,min(1.0,.78*self.bebop_phrase_memory.recent_comp_density+.22*active)),
                bars_since_last_statement=(
                    0.0 if active else self.bebop_phrase_memory.bars_since_last_statement+.125
                ),
                recent_response_count=self.bebop_phrase_memory.recent_response_count+(1 if active else 0),
                recent_non_response_count=self.bebop_phrase_memory.recent_non_response_count+(0 if active else 1),
                last_comp_phase=(normalized if active else self.bebop_phrase_memory.last_comp_phase),
            )
        else:
            chosen = perform_one_gesture(plan, dctx, self.memory)
        hits = tuple(
            RenderVoice(
                _DRUM_MIDI[h.voice],
                h.velocity,
                .10,
                _ms_to_beats(h.microtiming_ms, snapshot.transport.tempo_bpm) + getattr(h, "onset_offset_beats", 0.0),
                articulation=(h.articulation,),
                instrument_role="drums",
            )
            for h in chosen.gesture.hits
        )
        gesture = RenderGesture(
            role="drums",
            drum_hits=hits,
            source="player/drums:online_drummer",
            tags=tuple(sorted(chosen.gesture.tags | {chosen.gesture.role.value})),
            annotations={"drum_score": f"{chosen.score:.4f}"},
        )

        density = min(1.0, len(hits) / 4.0)
        return NativeImmediateResult(
            gesture=gesture,
            density=density,
            energy=energy,
            tension=float(context.get("ensemble_tension", snapshot.ensemble_tension)),
            leadership=.12 if chosen.gesture.role.value in {"setup", "accent"} else .03,
            phrase_maturity=0.0,
            tags=frozenset(set(chosen.gesture.tags) | {chosen.gesture.role.value}),
            provenance=(("drummer_bebop_runtime" if "bebop" in style_tags else "drummer_online_policy"),),
        )


@dataclass
class PianoNativeDecider:
    state: PianoCompingState = field(default_factory=PianoCompingState)
    evaluator: PianoCompingEvaluator = field(default_factory=PianoCompingEvaluator)

    def __call__(self, context: Mapping[str, object]) -> NativeImmediateResult | None:
        request = context.get("piano_voicing_request")
        if request is None or not isinstance(request, PianoVoicingRequest):
            return None

        snapshot = context["ensemble_snapshot"]
        directive = context["interaction_directive"]
        phrase = _latest_other_phrase_maturity(snapshot, "piano")
        sax_intent=snapshot.intent_for("sax")
        shared_piano_moment=derive_shared_solo_moment(
            snapshot,
            context.get("harmonic_frame"),
            foreground_player_id="sax",
        ) if context.get("harmonic_frame") is not None else None
        sax_has_motif=bool(
            sax_intent is not None
            and any(str(tag).startswith("motif:") for tag in sax_intent.tags)
        )

        comping_context = PianoCompingContext(
            soloist_activity=_soloist_activity(snapshot),
            phrase_boundary_probability=phrase,
            available_space_beats=max(0.0, snapshot.space_available * 2.0),
            bass_activity=max((
                i.density for i in snapshot.intents if i.player_id == "bass"
            ), default=.5),
            drummer_activity=max((
                i.density for i in snapshot.intents if i.player_id == "drums"
            ), default=.5),
            ensemble_density=snapshot.ensemble_density,
            recent_piano_density=min(1.0, self.state.recent_density.voice_count / 6.0),
            section_energy=snapshot.ensemble_energy,
            motif_continuity_strength=.72 if sax_has_motif else .18,
            pattern_consistency_strength=.58 if sax_has_motif else .25,
            harmonic_turn=(
                shared_piano_moment.harmonic_turn
                if shared_piano_moment is not None
                else PianoCompingContext().harmonic_turn
            ),
            time_feel=(snapshot.groove.feel.value if snapshot.groove is not None else "swing"),
        )
        interaction_state = self.state.interaction_state_from_context(comping_context)
        slate = build_immediate_performance_candidates(
            request,
            comping_context,
            interaction_state,
            context.get("harmonic_affordance"),
            max_candidates=64,
        )
        musical_context = context.get("musical_context")
        if not isinstance(musical_context, MusicalContextVector):
            musical_context = MusicalContextVector(
                phrase_maturity=phrase,
                tension=snapshot.ensemble_tension,
                ensemble_activity=snapshot.ensemble_density,
            )
        plan = SoftPlan(
            horizon_beats=1.0,
            intention=directive.interaction.value,
            density_direction="down" if directive.density_delta < 0 else (
                "up" if directive.density_delta > 0 else "stable"
            ),
        )
        chosen = perform_one_comping_action(
            plan,
            self.evaluator,
            slate.candidates,
            comping_context,
            musical_context,
            self.state,
            harmonic_affordance=context.get("harmonic_affordance"),
            interaction_state=interaction_state,
            harmonic_frame=context.get("harmonic_frame"),
            harmonic_reasoning=context.get("harmonic_reasoning"),
        )

        candidate = chosen.candidate
        if candidate.realization is None:
            return NativeImmediateResult(
                gesture=None,
                density=0.0,
                energy=max(.1, snapshot.ensemble_energy * .35),
                tension=snapshot.ensemble_tension,
                leadership=.02,
                tags=frozenset({"piano_silence", candidate.role.value}),
                provenance=("piano_comping_policy",),
            )

        event = candidate.realization.event
        voices = tuple(
            RenderVoice(
                v.pitch_midi,
                event.velocity,
                event.duration_beats,
                event.onset_offset_beats + v.onset_offset_beats,
                articulation=event.articulation,
                instrument_role="piano",
            )
            for v in event.voices_by_onset
        )
        gesture = RenderGesture(
            role="piano",
            voices=voices,
            source="player/piano:comping_policy",
            tags=tuple(sorted(set(event.tags) | set(candidate.tags) | {candidate.role.value})),
            annotations={"piano_score": f"{chosen.total:.4f}"},
        )
        density = min(1.0, len(voices) / 6.0)
        return NativeImmediateResult(
            gesture=gesture,
            density=density,
            energy=max(.1, min(1.0, snapshot.ensemble_energy)),
            tension=snapshot.ensemble_tension,
            leadership=.08 if candidate.role.value in {"answer", "fill"} else .03,
            phrase_maturity=0.0,
            tags=frozenset(set(event.tags) | set(candidate.tags) | {candidate.role.value}),
            provenance=("piano_comping_policy",),
        )


@dataclass
class SaxNativeDecider:
    """Canonical one-event Sax provider for the shared ensemble runtime.

    The provider delegates musical choice to players.sax and returns exactly one
    immediate renderer gesture (or intentional space). Shared groove is not
    applied here; the runtime adapter boundary owns that projection.
    """

    phrase_memory: SaxPhraseMemory = field(default_factory=SaxPhraseMemory)
    motif_memory: MotifMemory = field(default_factory=MotifMemory)
    physical_constraints: SaxPhysicalConstraints = field(
        default_factory=lambda: SaxPhysicalConstraints(
            lowest_playable_midi=50,
            highest_playable_midi=94,
            comfortable_interval_semitones=12,
            max_notes_since_breath=10,
            max_beats_since_breath=8.0,
        )
    )

    def __call__(self, context: Mapping[str, object]) -> NativeImmediateResult | None:
        snapshot = context["ensemble_snapshot"]
        directive = context["interaction_directive"]
        frame = context.get("harmonic_frame")
        if frame is None:
            return None

        phrase_maturity = float(context.get(
            "phrase_position",
            _latest_other_phrase_maturity(snapshot, "sax"),
        ))
        phrase_maturity = max(0.0, min(1.0, phrase_maturity))

        score_snapshot = context.get("sax_score_snapshot")
        if not isinstance(score_snapshot, ScoreContextSnapshot):
            score_snapshot = ScoreContextSnapshot(
                book_id="runtime",
                song_id=str(context.get("song_id", "runtime")),
                position=ScorePosition(
                    page=1,
                    bar=max(1, int(snapshot.transport.bar) + 1),
                    beat=max(0.0, float(snapshot.transport.beat)),
                ),
                section=snapshot.transport.section or None,
                confidence=0.0,
                provenance=("runtime_unspecified_score_context",),
            )

        policy = choose_sax_runtime_policy(
            score_snapshot,
            previous_score_snapshot=context.get("previous_sax_score_snapshot")
            if isinstance(context.get("previous_sax_score_snapshot"), ScoreContextSnapshot)
            else None,
            legend=context.get("sax_legend_context"),
            legend_candidate_context=context.get("sax_legend_candidate_context"),
            interaction_directive=directive,
            external_allow_improvisation=bool(context.get("sax_allow_improvisation", True)),
        )

        previous_pitch = self.phrase_memory.last_pitch_midi

        showcase_legend_materials=()
        if context.get("legend_showcase") and context.get("sax_legend_context") is not None:
            base_context=context.get("sax_legend_candidate_context")
            materials=[]
            profile_view=context.get("sax_legend_context").profile_view
            for domain in LegendDomain:
                if not profile_view.domain_features.get(domain, ()):
                    continue
                materials.extend(collect_legend_candidate_material(
                    context.get("sax_legend_context"),
                    type(base_context)(
                        domain=domain,
                        harmony_context=base_context.harmony_context,
                        harmonic_function=base_context.harmonic_function,
                        local_key=base_context.local_key,
                        phrase_position=base_context.phrase_position,
                        active_tags=base_context.active_tags,
                        allowed_uses=base_context.allowed_uses,
                        vocabulary_limit=base_context.vocabulary_limit,
                    ),
                ))
            showcase_legend_materials=tuple(materials)

        # Shared Solo Intelligence owns generic phrase/turn/motif development.
        # Sax remains responsible only for instrument-specific realization and
        # physical/expression constraints.
        shared_moment=derive_shared_solo_moment(
            snapshot,
            frame,
            foreground_player_id="sax",
        )
        shared_vocab=context.get("shared_vocabulary_sax")
        shared_vocab_seed=(
            shared_vocab.items[0].vocabulary_id
            if shared_vocab is not None and shared_vocab.items else ""
        )
        motif_generation=MotifGenerationContext(
            tension=max(0.0,min(1.0,snapshot.ensemble_tension)),
            ensemble_activity=max(0.0,min(1.0,snapshot.ensemble_density)),
            phrase_space=max(0.0,min(1.0,snapshot.space_available)),
            future_harmony_available=frame.next_expected is not None,
            interaction_role=directive.interaction.value,
            active_motif_id=(
                next(iter(self.motif_memory.active())).identity.motif_id
                if self.motif_memory.active() else ""
            ),
            vocabulary_seed_id=shared_vocab_seed,
        )
        motif_eval=MotifEvaluationContext(
            harmonic_fit=.72,
            ensemble_fit=max(.25,1.0-snapshot.ensemble_density*.35),
            novelty_need=.52,
            coherence_need=.78,
            recent_similarity=.20 if self.motif_memory.active() else 0.0,
        )
        shared_plan=build_solo_tick(
            harmonic_frame=frame,
            harmonic_turn=shared_moment.harmonic_turn,
            turn=shared_moment.turn,
            complementarity=shared_moment.complementarity,
            current_pitch_class=(previous_pitch%12 if previous_pitch is not None else None),
            target_pitch_classes=frozenset(context.get("sax_target_pitch_classes", ())),
            local_key_pitch_classes=frozenset(context.get("sax_local_key_pitch_classes", ())),
            structural_pitch_classes=(
                frame.expected.pitch_classes
                if frame.expected is not None else frozenset()
            ),
            duration_beats=.5,
            motif_generation_context=motif_generation,
            motif_evaluation_context=motif_eval,
            motif_memory=self.motif_memory,
        )
        policy_projection=project_musical_policy(
            priors=context.get("sax_hierarchical_priors"),
            gating_context=improvisation_gating_context(
                ensemble_complexity=max(0.0,min(1.0,snapshot.ensemble_density)),
                live_context_confidence=.78,
                structural_constraint=.18,
            ),
            motif_decision=shared_plan.motif_decision,
            active_tags=tuple(sorted(directive.tags)),
        )

        immediate = SaxImmediateContext(
            previous_pitch_midi=previous_pitch,
            duration_beats=.5,
            target_pitch_classes=frozenset(context.get("sax_target_pitch_classes", ())),
            local_key_pitch_classes=frozenset(context.get("sax_local_key_pitch_classes", ())),
            allow_improvisation=policy.allow_improvisation,
            written_pitch_midi=context.get("sax_written_pitch_midi"),
            written_duration_beats=context.get("sax_written_duration_beats"),
            notes_since_breath=self.phrase_memory.notes_since_breath,
            beats_since_breath=self.phrase_memory.beats_since_breath,
            physical_constraints=self.physical_constraints,
            score_policy=policy.score,
            interaction=policy.interaction,
            legend_materials=(
                showcase_legend_materials
                if showcase_legend_materials
                else (policy.legend.materials if policy.legend is not None else ())
            ),
            memory_intention=(
                policy.legend.intention if policy.legend is not None else None
            ),
        )
        candidates = generate_immediate_sax_candidates(frame, immediate)
        if not candidates:
            return None

        shared_specs=shared_plan.candidates
        shared_pcs={x.pitch_class for x in shared_specs if x.pitch_class is not None}
        shared_tags=set().union(*(set(x.tags) for x in shared_specs)) if shared_specs else set()
        shared_space=any(x.pitch_class is None for x in shared_specs)

        def _integrated_sax_score(item):
            score=item.score
            event=item.event
            if event.pitch_midi is None:
                if shared_space:
                    score += .18
                score += .24*max(0.0,policy_projection.space_bias)
                if shared_vocab is not None:
                    score += shared_vocab.tag_bias({"ensemble_space","add_space","phrase_end","rest"})
                return score

            if event.pitch_midi%12 in shared_pcs:
                score += .13
            overlap=len(set(event.tags).intersection(shared_tags))
            score += min(.08,.02*overlap)
            if shared_vocab is not None:
                score += shared_vocab.tag_bias(set(event.tags))
            if "directed_target" in event.tags or "future_harmony" in event.tags:
                score += .18*max(0.0,policy_projection.harmonic_retarget_bias)
            if previous_pitch is not None and policy_projection.register_direction:
                delta=event.pitch_midi-previous_pitch
                if delta*policy_projection.register_direction>0:
                    score += .06*abs(policy_projection.register_direction)
            return score

        chosen = max(candidates, key=_integrated_sax_score)
        event = chosen.event
        if event.pitch_midi is None:
            return NativeImmediateResult(
                gesture=None,
                density=0.0,
                energy=max(.1, snapshot.ensemble_energy * .45),
                tension=snapshot.ensemble_tension,
                leadership=max(0.0, min(1.0, .18 + directive.leadership_delta)),
                phrase_maturity=phrase_maturity,
                tags=frozenset(set(event.tags) | {"sax_space"}),
                provenance=("sax_runtime_policy", "sax_immediate_candidate"),
            )

        phrase_context = SaxPhraseContext(
            pitch_midi=event.pitch_midi,
            previous_pitch_midi=previous_pitch,
            duration_beats=event.duration_beats,
            beat_in_bar=float(snapshot.transport.beat) % snapshot.transport.meter_numerator,
            phrase_maturity=phrase_maturity,
            source_family=event.source_family,
            score_phrase_boundary_before=policy.score.phrase_boundary_before,
            score_phrase_boundary_after=policy.score.phrase_boundary_after,
        )
        phrase_decision = self.phrase_memory.decide(phrase_context)

        expression = choose_sax_expression(SaxExpressionContext(
            pitch_midi=event.pitch_midi,
            previous_pitch_midi=previous_pitch,
            duration_beats=event.duration_beats,
            beat_in_bar=phrase_context.beat_in_bar,
            phrase_maturity=phrase_maturity,
            tension=snapshot.ensemble_tension,
            velocity=int(context.get("sax_velocity", 82)),
        ))
        articulations=list(expression.tags)
        if phrase_decision.connect_legato and "legato" not in articulations:
            articulations.append("legato")

        arc = choose_sax_articulation_arc(SaxArcContext(
            pitch_midi=event.pitch_midi,
            previous_pitch_midi=previous_pitch,
            duration_beats=event.duration_beats,
            phrase_maturity=phrase_maturity,
            notes_since_breath=self.phrase_memory.notes_since_breath,
            breath_before=phrase_decision.breath_before,
            phrase_start=phrase_decision.phrase_start,
            phrase_end=phrase_decision.phrase_end,
            tension=snapshot.ensemble_tension,
        ))
        articulation, velocity, attack_scale, release_shape = apply_sax_arc(
            tuple(articulations),
            expression.velocity,
            .72 if phrase_decision.soften_attack else 1.0,
            phrase_decision.release_shape,
            arc,
        )

        self.phrase_memory.commit(phrase_context, phrase_decision)
        if shared_plan.motif_decision is not None:
            self.motif_memory.observe(
                shared_plan.motif_decision.candidate.identity,
                development_success=.5,
            )
        gesture = RenderGesture(
            role="soloist",
            voices=(RenderVoice(
                event.pitch_midi,
                velocity,
                event.duration_beats,
                event.onset_offset_beats,
                articulation=articulation,
                instrument_role="tenor_sax",
                breath_before_beats=.125 if phrase_decision.breath_before else 0.0,
                attack_scale=attack_scale,
                release_shape=release_shape,
            ),),
            source="player/sax:canonical_immediate",
            tags=tuple(sorted(set(event.tags) | set(policy.interaction.tags) | {f"arc:{arc.phase}"})),
            annotations={
                "sax_score": f"{chosen.score:.4f}",
                "arc_phase": arc.phase,
                "phrase_intention": shared_plan.intent.entry_mode.value,
                "shared_solo_method": shared_plan.intent.solo_method.value,
                "shared_entry_mode": shared_plan.intent.entry_mode.value,
                "shared_target_mode": shared_plan.intent.target_mode.value,
                "motif_id": (
                    shared_plan.motif_decision.candidate.identity.motif_id
                    if shared_plan.motif_decision is not None else ""
                ),
                "policy_projection_confidence": f"{policy_projection.confidence:.3f}",
                "legend_id": (
                    context.get("sax_legend_context").profile_view.legend_id
                    if context.get("sax_legend_context") is not None else ""
                ),
                "legend_showcase": "1" if context.get("legend_showcase") else "0",
                "legend_material_count": str(len(showcase_legend_materials)),
                "shared_vocabulary_seed": shared_vocab_seed,
                "shared_vocabulary_count": str(
                    len(shared_vocab.items) if shared_vocab is not None else 0
                ),
            },
        )
        return NativeImmediateResult(
            gesture=gesture,
            density=min(1.0, .32 + .18 * max(0.0, policy.interaction.density_delta)),
            energy=max(.1, min(1.0, snapshot.ensemble_energy + directive.energy_delta)),
            tension=snapshot.ensemble_tension,
            leadership=max(0.0, min(1.0, .58 + directive.leadership_delta)),
            phrase_maturity=phrase_maturity,
            tags=frozenset(set(event.tags) | set(policy.interaction.tags) | {f"arc:{arc.phase}",f"phrase_intention:{shared_plan.intent.entry_mode.value}"}),
            provenance=(
                "sax_runtime_policy",
                "shared_solo_runtime",
                "shared_motif_policy",
                "shared_vocabulary_runtime",
                "sax_immediate_candidate",
                "shared_solo_phrase_intent",
                "sax_phrase_expression",
            ),
        )


def build_native_trio_runtime():
    """Construct the current executable piano/bass/drums runtime loop."""
    from .runtime_loop import EnsembleRuntimeLoop
    from .trio_adapters import PianoRuntimeAdapter, BassRuntimeAdapter, DrumsRuntimeAdapter

    return EnsembleRuntimeLoop((
        PianoRuntimeAdapter(PianoNativeDecider()),
        BassRuntimeAdapter(BassNativeDecider()),
        DrumsRuntimeAdapter(DrumsNativeDecider()),
    ))


def build_native_quartet_runtime():
    """Construct Piano/Bass/Drums/Tenor-Sax from the same causal snapshot."""
    from .runtime_loop import EnsembleRuntimeLoop
    from .trio_adapters import (
        PianoRuntimeAdapter,
        BassRuntimeAdapter,
        DrumsRuntimeAdapter,
        SaxRuntimeAdapter,
    )

    return EnsembleRuntimeLoop((
        PianoRuntimeAdapter(PianoNativeDecider()),
        BassRuntimeAdapter(BassNativeDecider()),
        DrumsRuntimeAdapter(DrumsNativeDecider()),
        SaxRuntimeAdapter(SaxNativeDecider()),
    ))
