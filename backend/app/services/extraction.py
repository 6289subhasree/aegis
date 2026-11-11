"""Rule-based extraction of severity signals from English report text.

Deliberately simple and transparent. Each pattern maps to a factor in [0, 1] so a responder can
see exactly why a report scored the way it did. An ML/NER upgrade (spaCy) can replace this later
without changing the interface.
"""

import re
from dataclasses import dataclass

NUMBER_WORDS = {
    "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7,
    "eight": 8, "nine": 9, "ten": 10, "eleven": 11, "twelve": 12, "fifteen": 15,
    "twenty": 20, "thirty": 30, "fifty": 50, "hundred": 100,
}

# (pattern, life-threat weight)
LIFE_PATTERNS = [
    (r"\b(trapped|stuck|stranded|marooned)\b", 1.0),
    (r"\b(drown\w*|swept away|washed away|being swept)\b", 1.0),
    (r"\b(missing|lost|can'?t find)\b", 0.9),
    (r"\b(roof|rooftop|terrace)\b", 0.9),
    (r"\b(injur\w*|bleeding|unconscious|critical|dying|dead|died)\b", 0.9),
    (r"\b(pregnant|infant|baby|newborn|elderly|disabled|child(ren)?)\b", 0.6),
    (r"\b(rising fast|rapidly rising|water rising|about to collapse|collapsing)\b", 0.8),
]

URGENCY_PATTERNS = [
    (r"\b(now|immediately|urgent\w*|emergency|help|sos|please hurry|right now)\b", 0.7),
    (r"\b(rising|worsening|increasing|getting worse|spreading|fast)\b", 0.8),
    (r"\b(collapsed|collapse|breach\w*|burst|landslide)\b", 0.7),
    (r"\b(no (drinking |clean |safe )?(food|water|medicine))\b", 0.5),
    (r"\b(minor|small|slight|little)\b", -0.3),
]

ISOLATION_PATTERNS = [
    (r"\b(cut off|isolated|no (road|access|network|signal|phone)|road (blocked|closed|submerged))\b", 1.0),
    (r"\b(bridge (collapsed|broke|broken|washed)|collapsed bridge)\b", 1.0),
    (r"\b(can'?t (leave|reach|get out)|unable to (leave|reach))\b", 0.8),
    (r"\b(village|hamlet|island)\b", 0.3),
]

TYPE_PATTERNS = [
    ("rescue", r"\b(trapped|stuck|stranded|rooftop|roof|drown\w*|missing|rescue)\b"),
    ("medical", r"\b(injur\w*|bleeding|unconscious|sick|medical|pregnan\w*|ambulance)\b"),
    ("infrastructure", r"\b(bridge|road|embankment|dam|power line|electric\w*|collaps\w*)\b"),
    ("flood", r"\b(flood\w*|water|inundat\w*|waterlog\w*|rain\w*)\b"),
    ("supplies", r"\b(food|water supply|medicine|shelter|relief)\b"),
]

_NUM = re.compile(r"\b(\d{1,4})\s*(?:\+)?\s*(?:people|persons|villagers|families|family|children|kids|men|women|residents|souls)\b")
_NUM_WORD = re.compile(
    r"\b(" + "|".join(NUMBER_WORDS) + r")\s+(?:people|persons|villagers|families|family|children|kids|men|women|residents)\b"
)


@dataclass(frozen=True)
class Extracted:
    incident_type: str
    people: int
    life: float
    urgency: float
    isolation: float


def _score(patterns: list[tuple[str, float]], text: str, cap: float = 1.0) -> float:
    hits = [w for pat, w in patterns if re.search(pat, text)]
    pos = sorted((h for h in hits if h > 0), reverse=True)
    neg = sum(h for h in hits if h < 0)
    if not pos:
        return 0.0
    # strongest signal dominates; extra corroborating signals add a small bonus
    value = pos[0] + 0.1 * len(pos[1:]) + neg
    return round(max(0.0, min(cap, value)), 3)


def extract_people(text: str) -> int:
    total = 0
    for m in _NUM.finditer(text):
        n = int(m.group(1))
        if "famil" in m.group(0):
            n *= 4  # rough household size assumption
        total = max(total, n)
    for m in _NUM_WORD.finditer(text):
        n = NUMBER_WORDS[m.group(1)]
        if "famil" in m.group(0):
            n *= 4
        total = max(total, n)
    return total


def classify_type(text: str) -> str:
    for name, pat in TYPE_PATTERNS:
        if re.search(pat, text):
            return name
    return "other"


def extract(text: str) -> Extracted:
    t = text.lower()
    return Extracted(
        incident_type=classify_type(t),
        people=extract_people(t),
        life=_score(LIFE_PATTERNS, t),
        urgency=_score(URGENCY_PATTERNS, t),
        isolation=_score(ISOLATION_PATTERNS, t),
    )
