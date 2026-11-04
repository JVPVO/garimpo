"""Pool loaders: authoritative Brazilian answer universes.

Each entry is shaped:
    {name, qid, article, sl, gravity, attrs{...}, source}

`gravity` is an optional authoritative magnitude (population, titles) used only
as a small extra signal; the primary signals are Wikipedia attention and corpus
frequency.

SPARQL templates use string.Template ($name) so the query braces stay literal.
"""
from __future__ import annotations

import json
from string import Template
from urllib.parse import unquote

from .http import sparql
from .wd import qid, resolve_titles, sitelinks_for

PTWIKI = "<https://pt.wikipedia.org/>"
BR = "Q155"

INSTANCES_TMPL = Template("""
SELECT ?item ?itemLabel ?sl ?article ?pop WHERE {
  {
    SELECT ?item (MAX(?sl_) AS ?sl) (SAMPLE(?article_) AS ?article)
                (MAX(?pop_) AS ?pop)
    WHERE {
      ?item wdt:P31 wd:$type .
      $extra
      OPTIONAL { ?item wikibase:sitelinks ?sl_ . }
      OPTIONAL { ?article_ schema:about ?item ; schema:isPartOf $wiki . }
      $gravity
    }
    GROUP BY ?item
    ORDER BY $order
    LIMIT $limit
  }
  SERVICE wikibase:label { bd:serviceParam wikibase:language "pt,en". }
}
""")

PEOPLE_TMPL = Template("""
SELECT ?item ?itemLabel ?sl ?article WHERE {
  {
    SELECT ?item (MAX(?sl_) AS ?sl) (SAMPLE(?article_) AS ?article)
    WHERE {
      ?item wdt:P106 wd:$occ ; wdt:P27 wd:$br .
      $extra
      OPTIONAL { ?item wikibase:sitelinks ?sl_ . }
      OPTIONAL { ?article_ schema:about ?item ; schema:isPartOf $wiki . }
    }
    GROUP BY ?item
    ORDER BY DESC(?sl)
    LIMIT $limit
  }
  SERVICE wikibase:label { bd:serviceParam wikibase:language "pt,en". }
}
""")


def _tail(value: str | None) -> str | None:
    """URN/URL tail, percent-decoded, article-title shaped."""
    if not value:
        return None
    return unquote(value.rsplit("/", 1)[-1]).replace("_", " ")


def _clean(rows: list[dict], key: str = "itemLabel") -> list[dict]:
    out, seen = [], set()
    for row in rows:
        name = (row.get(key) or "").strip()
        if not name or (name.startswith("Q") and name[1:].isdigit()):
            continue
        norm = name.lower()
        if norm in seen:
            continue
        seen.add(norm)
        gravity = row.get("pop") or row.get("gravity")
        attrs = {k[5:]: v for k, v in row.items() if k.startswith("attr_") and v}
        if row.get("contLabel"):
            attrs["continente"] = row["contLabel"]
        out.append({
            "name": name,
            "qid": (row.get("item") or "").rsplit("/", 1)[-1] or None,
            "article": _tail(row.get("article")),
            "sl": int(float(row.get("sl") or 0)),
            "gravity": float(gravity) if gravity else None,
            "attrs": attrs,
        })
    return out


def raw(query: str) -> list[dict]:
    return _clean(sparql(query))


def instances_of(type_label: str, *, extra: str = "", limit: int = 400,
                 order: str = "DESC(?sl)", gravity_prop: str | None = None) -> list[dict]:
    """Instances of a Wikidata class identified by its Portuguese label."""
    gravity = f"OPTIONAL {{ ?item wdt:{gravity_prop} ?pop . }}" if gravity_prop else ""
    query = INSTANCES_TMPL.substitute(
        type=qid(type_label), extra=extra, wiki=PTWIKI, gravity=gravity,
        order=order, limit=limit,
    )
    return _clean(sparql(query))


def people(occupation_label: str, *, limit: int = 150, extra: str = "") -> list[dict]:
    query = PEOPLE_TMPL.substitute(
        occ=qid(occupation_label), br=BR, extra=extra, wiki=PTWIKI, limit=limit,
    )
    return _clean(sparql(query))


def category_members(cat: str) -> list[dict]:
    """pt.wikipedia category members -> entries (metrics added later).

    Follows cmcontinue so big categories (Aves do Brasil, ~740) come complete.
    """
    from .http import wp_api
    out, seen = [], set()
    params: dict = {"cmtitle": f"Categoria:{cat}", "cmlimit": "500", "cmtype": "page"}
    for _ in range(6):
        data = wp_api(list="categorymembers", **params)
        for member in data.get("query", {}).get("categorymembers", []):
            title = member["title"]
            if title.startswith("Categoria:") or title.lower() in seen:
                continue
            seen.add(title.lower())
            out.append({"name": title, "qid": None, "article": title, "sl": 0,
                        "gravity": None, "attrs": {"cat": cat}})
        cont = data.get("continue", {}).get("cmcontinue")
        if not cont:
            break
        params = {**params, "cmcontinue": cont}
    return out


def merge_pools(*groups: list[dict]) -> list[dict]:
    """Concatenate pools, keeping the first entry for a repeated name."""
    from .http import normalize
    out, seen = [], set()
    for group in groups:
        for entry in group:
            key = normalize(entry["name"])
            if not key or key in seen:
                continue
            seen.add(key)
            out.append(entry)
    return out


def from_curated(items: list[dict], *, source: str) -> list[dict]:
    out = []
    for item in items:
        name = (item.get("name") or "").strip()
        if not name:
            continue
        out.append({
            "name": name,
            "qid": None,
            "article": item.get("article") or name,
            "sl": 0,
            "gravity": item.get("gravity"),
            "attrs": {"source": source, **(item.get("tags") or {})},
        })
    return out


def enrich(entries: list[dict]) -> list[dict]:
    """Resolve pt.wikipedia article + QID + sitelink count for every entry."""
    missing_article = [e for e in entries if not e.get("article")]
    if missing_article:
        mapping = resolve_titles([e["name"] for e in missing_article])
        for entry in missing_article:
            hit = mapping.get(entry["name"]) or {}
            entry["article"] = hit.get("title") or entry["name"]
    missing_qid = [e for e in entries if not e.get("qid")]
    if missing_qid:
        mapping = resolve_titles([e["article"] or e["name"] for e in missing_qid])
        for entry in missing_qid:
            hit = mapping.get(entry["article"] or entry["name"]) or {}
            entry["qid"] = hit.get("qid")
    qids = [e["qid"] for e in entries if e.get("qid")]
    counts = sitelinks_for(qids)
    for entry in entries:
        if entry.get("qid"):
            entry["sl"] = max(entry.get("sl") or 0, counts.get(entry["qid"], 0))
    return entries


if __name__ == "__main__":
    print(json.dumps(instances_of("unidade federativa do Brasil", limit=3,
                                  gravity_prop="P1082"), ensure_ascii=False, indent=1))
