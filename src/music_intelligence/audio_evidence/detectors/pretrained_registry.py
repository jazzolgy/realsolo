"""Registry of pretrained model options for Audio Evidence Engine.

The registry records capabilities and deployment-review requirements. It is not
an automatic legal determination and intentionally keeps research/development
availability separate from production eligibility.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PretrainedModelProfile:
    model_id: str
    task: str
    classes_or_stems: tuple[str, ...]
    note_level: bool
    framework: str
    default_role: str
    deployment_review_required: bool
    notes: str


PRETRAINED_MODEL_PROFILES: tuple[PretrainedModelProfile, ...] = (
    PretrainedModelProfile(
        model_id="demucs:htdemucs_6s",
        task="source_separation",
        classes_or_stems=(
            "drums",
            "bass",
            "other",
            "vocals",
            "guitar",
            "piano",
        ),
        note_level=False,
        framework="demucs/torch",
        default_role="research_separator",
        deployment_review_required=True,
        notes=(
            "Best current pretrained fit for explicit bass/piano stems, but "
            "piano separation is experimental and model-weight licensing must "
            "be reviewed separately from the MIT code license."
        ),
    ),
    PretrainedModelProfile(
        model_id="torchaudio:HDEMUCS_HIGH_MUSDB_PLUS",
        task="source_separation",
        classes_or_stems=("drums", "bass", "other", "vocals"),
        note_level=False,
        framework="torchaudio/torch",
        default_role="research_separator_fallback",
        deployment_review_required=True,
        notes=(
            "Pretrained four-stem Hybrid Demucs fallback. Piano is contained "
            "inside other and is not isolated."
        ),
    ),
    PretrainedModelProfile(
        model_id="yamnet:audioset",
        task="audio_event_tagging",
        classes_or_stems=(
            "piano",
            "double_bass",
            "bass_guitar",
            "drum_kit",
            "snare_drum",
            "bass_drum",
            "cymbal",
            "hi_hat",
        ),
        note_level=False,
        framework="tensorflow",
        default_role="weak_instrument_prior",
        deployment_review_required=True,
        notes=(
            "Coarse AudioSet frame classifier. Use only as weak onset-local "
            "instrument evidence, never direct note ownership."
        ),
    ),
)


def pretrained_profiles_for_task(task: str) -> tuple[PretrainedModelProfile, ...]:
    return tuple(
        profile
        for profile in PRETRAINED_MODEL_PROFILES
        if profile.task == task
    )


def pretrained_profile(model_id: str) -> PretrainedModelProfile:
    for profile in PRETRAINED_MODEL_PROFILES:
        if profile.model_id == model_id:
            return profile
    raise KeyError(model_id)
