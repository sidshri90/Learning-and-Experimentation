"""Pure helpers for turning raw geocoding results into a sensible suggestion order."""
from typing import Any

_CONTEXT_KEYS = ("admin1", "country", "country_code", "admin2")


def parse_query(query: str) -> tuple[str, list[str]]:
    """'Patna, Bihar, India' -> ('Patna', ['Bihar', 'India'])."""
    parts = [p.strip() for p in query.split(",") if p.strip()]
    return (parts[0], parts[1:]) if parts else ("", [])


def context_matches(result: dict[str, Any], rest: list[str]) -> int:
    """How many of the extra query parts (state, country...) prefix-match this result."""
    fields = [str(result.get(k) or "").casefold() for k in _CONTEXT_KEYS]
    return sum(1 for part in rest if any(f.startswith(part.casefold()) for f in fields if f))


def rank(results: list[dict[str, Any]], head: str, rest: list[str]) -> list[dict[str, Any]]:
    """Order results by context match, then name-prefix match, then population.

    If any result matches every extra part, the others are dropped, so
    'Paris, Texas' does not list Paris, France.
    """
    scored = [(context_matches(r, rest), r) for r in results]
    if rest:
        full = [s for s in scored if s[0] == len(rest)]
        if full:
            scored = full
    head_cf = head.casefold()

    def key(item: tuple[int, dict[str, Any]]):
        matches, r = item
        starts = str(r.get("name") or "").casefold().startswith(head_cf)
        return (-matches, not starts, -(r.get("population") or 0))

    return [r for _, r in sorted(scored, key=key)]
