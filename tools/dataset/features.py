"""Extra per-answer facts used to build constrained prompts.

Fetched once from Wikidata by QID batch, cached by the HTTP layer.
"""
from __future__ import annotations

from string import Template

from .http import sparql
from .universes import _clean
from .wd import resolve_titles

DATES_TMPL = Template("""
SELECT ?item ?year WHERE {
  VALUES ?item { $values }
  { ?item wdt:P577 ?d . } UNION { ?item wdt:P580 ?d . } UNION { ?item wdt:P1191 ?d . }
  BIND(YEAR(?d) AS ?year)
}
""")

GENDER_TMPL = Template("""
SELECT ?item ?genderLabel WHERE {
  VALUES ?item { $values }
  ?item wdt:P21 ?gender .
  SERVICE wikibase:label { bd:serviceParam wikibase:language "pt,en". }
}
""")

GENRE_TMPL = Template("""
SELECT ?item ?genreLabel WHERE {
  VALUES ?item { $values }
  ?item wdt:P136 ?genre .
  SERVICE wikibase:label { bd:serviceParam wikibase:language "pt,en". }
}
""")

POSITION_TMPL = Template("""
SELECT ?item ?posLabel WHERE {
  VALUES ?item { $values }
  ?item wdt:P413 ?pos .
  SERVICE wikibase:label { bd:serviceParam wikibase:language "pt,en". }
}
""")


def _batched(template: Template, qids: list[str], size: int = 150) -> list[dict]:
    rows: list[dict] = []
    unique = [q for q in dict.fromkeys(qids) if q]
    for i in range(0, len(unique), size):
        values = " ".join(f"wd:{q}" for q in unique[i:i + size])
        rows.extend(sparql(template.substitute(values=values)))
    return rows


def _by_item(rows: list[dict], value_key: str) -> dict[str, list[str]]:
    out: dict[str, list[str]] = {}
    for row in rows:
        item = (row.get("item") or "").rsplit("/", 1)[-1]
        value = row.get(value_key)
        if item and value:
            out.setdefault(item, [])
            if value not in out[item]:
                out[item].append(value)
    return out


def years_for(entries: list[dict]) -> dict[str, int]:
    rows = _batched(DATES_TMPL, [e["qid"] for e in entries if e.get("qid")])
    out: dict[str, int] = {}
    for row in rows:
        item = (row.get("item") or "").rsplit("/", 1)[-1]
        try:
            year = int(row.get("year", ""))
        except ValueError:
            continue
        if item:
            out[item] = min(year, out.get(item, year))
    return out


def genders_for(entries: list[dict]) -> dict[str, str]:
    rows = _batched(GENDER_TMPL, [e["qid"] for e in entries if e.get("qid")])
    out: dict[str, str] = {}
    for item, labels in _by_item(rows, "genderLabel").items():
        joined = " ".join(labels).lower()
        if "feminino" in joined or "female" in joined or "mulher" in joined:
            out[item] = "feminino"
        elif "masculino" in joined or "male" in joined or "homem" in joined:
            out[item] = "masculino"
    return out


def genres_for(entries: list[dict]) -> dict[str, list[str]]:
    rows = _batched(GENRE_TMPL, [e["qid"] for e in entries if e.get("qid")])
    return _by_item(rows, "genreLabel")


def positions_for(entries: list[dict]) -> dict[str, list[str]]:
    rows = _batched(POSITION_TMPL, [e["qid"] for e in entries if e.get("qid")])
    return _by_item(rows, "posLabel")


def enrich_curated_qids(entries: list[dict]) -> None:
    """Curated entries carry a title; resolve QID once so features can be fetched."""
    missing = [e for e in entries if not e.get("qid")]
    if not missing:
        return
    mapping = resolve_titles([e["article"] or e["name"] for e in missing])
    for entry in missing:
        hit = mapping.get(entry["article"] or entry["name"]) or {}
        entry["qid"] = hit.get("qid")


if __name__ == "__main__":
    sample = _clean(sparql("""SELECT ?item ?itemLabel WHERE {
      ?item wdt:P31 wd:Q23745 . SERVICE wikibase:label { bd:serviceParam wikibase:language "pt". }
    } LIMIT 3"""))
    print(sample)
    print(years_for(sample))
