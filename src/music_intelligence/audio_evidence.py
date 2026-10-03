"""Canonical Audio Evidence import facade.

Implementation remains in music_intelligence.learning.audio_evidence so there is
one engine. This module is an import-stable public facade for Listener/realtime
consumers and deliberately contains no duplicate detector/posterior logic.
"""
from music_intelligence.learning.audio_evidence import artifacts_from_audio_aggregate

__all__=["artifacts_from_audio_aggregate"]
