"""Deterministic citation check, run next to the LLM judge so a wrong citation is cheap to spot."""

import re

# Matches "[Lanternfall, Section 2]" and also "[Lanternfall, Section 2; Lanternfall, Section 3]".
_CITATION = re.compile(r"([A-Z][A-Za-z' ]+?),\s*(?:Section|§)\s*(\d+)")


def parse_citations(answer: str) -> set[tuple[str, str]]:
    return {(g.strip(), n) for g, n in _CITATION.findall(answer)}


def citation_ok(answer: str, game: str, section: str) -> bool:
    """True when the answer cites (game, section); for sections of "" nothing may be cited."""
    cited = parse_citations(answer)
    if not section:
        return not cited
    return (game, section) in cited
