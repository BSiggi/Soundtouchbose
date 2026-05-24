"""Small text normalization utilities."""

from __future__ import annotations


def repair_mojibake(value: str) -> str:
    text = str(value or "")
    # Common UTF-8-as-Latin-1 artifacts seen in SoundTouch names (e.g. "BÃRO" for "BÜRO").
    markers = ("Ã", "Â", "Ð", "Ñ", "Ã¤", "Ã¶", "Ã¼", "ÃŸ")
    if not any(marker in text for marker in markers):
        return text
    try:
        repaired = text.encode("latin-1").decode("utf-8")
    except UnicodeError:
        return text
    return repaired or text
