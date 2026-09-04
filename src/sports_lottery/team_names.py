"""Explicit aliases only: unknown names remain unchanged, never fuzzy-merged."""
import unicodedata

ALIASES = {
    "尤尔加登": "Djurgardens IF", "佐加顿斯": "Djurgardens IF",
    "西布罗姆": "West Brom", "西布罗姆维奇": "West Brom",
    "女王巡游": "QPR", "女王公园巡游者": "QPR",
}


def normalize_team(name: str) -> str:
    cleaned = " ".join(unicodedata.normalize("NFKC", name).split())
    return ALIASES.get(cleaned, cleaned)
