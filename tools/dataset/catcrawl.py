"""Recursive pt.wikipedia category crawl (depth-limited), used to source and
audit pools. Titles come back as article titles; `clean_title` strips the
disambiguating parenthetical for display.
"""
from __future__ import annotations

import re

from .http import wp_api

PAREN = re.compile(r"\s*\([^)]*\)\s*$")
SKIP = re.compile(r"^(Lista|Listas|Anexo|Predefinição|Portal|Categoria)[ :]", re.I)


def clean_title(title: str) -> str:
    return PAREN.sub("", title).strip()


def _members(cat: str, kind: str) -> list[str]:
    out: list[str] = []
    params: dict = {"cmtitle": f"Categoria:{cat}", "cmlimit": "500", "cmtype": kind}
    for _ in range(10):
        data = wp_api(list="categorymembers", **params)
        out += [m["title"] for m in data.get("query", {}).get("categorymembers", [])]
        cont = data.get("continue", {}).get("cmcontinue")
        if not cont:
            break
        params = {**params, "cmcontinue": cont}
    return out


def crawl(cat: str, depth: int = 1, exclude: tuple[str, ...] = ()) -> dict[str, str]:
    """{article title: category it was found in}."""
    seen_cats: set[str] = set()
    found: dict[str, str] = {}
    frontier = [(cat, 0)]
    while frontier:
        current, level = frontier.pop(0)
        if current in seen_cats:
            continue
        seen_cats.add(current)
        for title in _members(current, "page"):
            if not SKIP.match(title):
                found.setdefault(title, current)
        if level < depth:
            for sub in _members(current, "subcat"):
                name = sub.split(":", 1)[1]
                if any(x.lower() in name.lower() for x in exclude):
                    continue
                frontier.append((name, level + 1))
    return found


def links_of(title: str) -> list[str]:
    """Main-namespace links of one article (e.g. a 'Lista de ...' page)."""
    out: list[str] = []
    params: dict = {"titles": title, "prop": "links", "plnamespace": "0", "pllimit": "500",
                    "redirects": "1"}
    for _ in range(10):
        data = wp_api(**params)
        for page in data.get("query", {}).get("pages", []):
            out += [link["title"] for link in page.get("links", [])]
        cont = data.get("continue", {}).get("plcontinue")
        if not cont:
            break
        params = {**params, "plcontinue": cont}
    return out


if __name__ == "__main__":
    import sys
    depth = int(sys.argv[1])
    for cat in sys.argv[2:]:
        found = crawl(cat, depth)
        print(f"## {cat} ({len(found)})")
        print("; ".join(sorted(found)))
