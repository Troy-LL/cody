"""Parse 'Hey Cody, where's my ____' style voice commands."""

from __future__ import annotations

import re

# "Cody" / common STT misspells: codey, kody, coty
WAKE_RE = re.compile(
    r"\bhey\s*(?:cody|codey|kody|coty)\b[,.]?\s*(.*)$",
    re.IGNORECASE | re.DOTALL,
)
CODY_NAME_RE = re.compile(r"\b(?:cody|codey|kody|coty)\b", re.IGNORECASE)
WHERE_RE = re.compile(
    r"where'?s?\s+(?:(?:is|are)\s+)?(?:(?:my|the)\s+)?(.+)$",
    re.IGNORECASE,
)
FIND_RE = re.compile(
    r"^(?:find|show|locate|point\s+(?:to|at)|get)\s+(?:my\s+|the\s+)?(.+)$",
    re.IGNORECASE,
)
STOPWORDS = frozenset(
    {
        "a",
        "an",
        "the",
        "my",
        "please",
        "file",
        "files",
        "for",
        "me",
        "to",
        "at",
        "on",
        "in",
    }
)


def extract_search_phrase(transcript: str) -> str:
    """Pull '____' from where's/find phrasing (no wake word required)."""
    text = " ".join(str(transcript or "").strip().split())
    if not text:
        return ""
    for cre in (WHERE_RE, FIND_RE):
        m = cre.search(text)
        if m:
            return _clean_phrase(m.group(1))
    return _clean_phrase(text)


def parse_hey_cody(transcript: str) -> str | None:
    """Return search phrase if utterance is a Cody command, else None."""
    text = " ".join(str(transcript or "").strip().split())
    if not text:
        return None

    wake = WAKE_RE.search(text)
    rest = (wake.group(1) or "").strip() if wake else ""

    # Require wake word for hands-free; allow bare "where's my X" after wake in same utterance
    if wake:
        if not rest:
            return ""  # wake only — waiting for follow-up
        for cre in (WHERE_RE, FIND_RE):
            m = cre.search(rest)
            if m:
                return _clean_phrase(m.group(1))
        return _clean_phrase(rest)

    # Also accept full-utterance where-questions that mention cody/codey
    if CODY_NAME_RE.search(text):
        m = WHERE_RE.search(text)
        if m:
            return _clean_phrase(m.group(1))

    return None


def _clean_phrase(phrase: str) -> str:
    p = phrase.strip(" .,!?\"'")
    p = re.sub(r"\s+", " ", p)
    return p


def query_terms(phrase: str) -> list[str]:
    """Tokens used to match OCR labels."""
    raw = re.findall(r"[A-Za-z0-9][A-Za-z0-9_\-.]{1,}", phrase.casefold())
    return [t for t in raw if t not in STOPWORDS and len(t) >= 2]
