"""Deterministic diversity-preserving pruning for piano candidates."""
from __future__ import annotations


def _tag_value(tags, prefix):
    for tag in tags:
        if tag.startswith(prefix):
            return tag.split(":", 1)[1]
    return None


def candidate_signature(candidate):
    role = getattr(getattr(candidate, "role", None), "value", None)
    realization = getattr(candidate, "realization", None)
    family = None
    tags = set(getattr(candidate, "tags", ()))
    if realization is not None:
        family = realization.event.source_family
        tags |= set(realization.event.tags)
    return (
        role, family,
        _tag_value(tags, "rhythm:"),
        _tag_value(tags, "register:"),
        _tag_value(tags, "dynamic:"),
        _tag_value(tags, "touch:"),
    )


def _distance(a, b):
    pairs = [(x, y) for x, y in zip(a, b) if x is not None and y is not None]
    if not pairs:
        return 0.0
    return sum(1 for x, y in pairs if x != y) / len(pairs)


def select_diverse_candidates(candidates, max_candidates):
    if max_candidates < 1:
        raise ValueError("max_candidates must be positive")
    if len(candidates) <= max_candidates:
        return tuple(candidates)

    silence = [c for c in candidates if getattr(c, "realization", None) is None]
    sounding = [c for c in candidates if getattr(c, "realization", None) is not None]
    kept_silence = silence[:max_candidates]
    budget = max_candidates - len(kept_silence)
    if budget <= 0:
        return tuple(kept_silence)

    sigs = [candidate_signature(c) for c in sounding]
    chosen = [0]
    remaining = set(range(1, len(sounding)))

    while remaining and len(chosen) < budget:
        chosen_sigs = [sigs[i] for i in chosen]
        families = {s[1] for s in chosen_sigs}
        roles = {s[0] for s in chosen_sigs}
        best = None
        best_key = None
        for idx in sorted(remaining):
            sig = sigs[idx]
            novelty = min(_distance(sig, s) for s in chosen_sigs)
            family_bonus = 1.0 if sig[1] not in families else 0.0
            role_bonus = 0.6 if sig[0] not in roles else 0.0
            key = (family_bonus + role_bonus + novelty, -idx)
            if best_key is None or key > best_key:
                best_key = key
                best = idx
        chosen.append(best)
        remaining.remove(best)

    return tuple(kept_silence + [sounding[i] for i in chosen])