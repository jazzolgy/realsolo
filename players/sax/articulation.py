from enum import Enum


class SoloArticulation(str, Enum):
    SUSTAIN = "sustain"
    SHORT = "short"
    LEGATO = "legato"
    VIBRATO = "vibrato"
    SUBTONE = "subtone"
    GROWL = "growl"
    SCOOP = "scoop"
    FALL = "fall"
    BREATHY = "breathy"
    ACCENT = "accent"
