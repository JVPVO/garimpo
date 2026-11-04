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


def parse_curated_item(item) -> dict | None:
    """A curated item is an object {name, article, aliases, tags} or a compact
    string "Name@Article|alias|alias" (article and aliases optional)."""
    if isinstance(item, str):
        parts = [p.strip() for p in item.split("|")]
        head, aliases = parts[0], [p for p in parts[1:] if p]
        name, _, article = head.partition("@")
        return {"name": name.strip(), "article": article.strip() or None,
                "aliases": aliases, "tags": {}}
    name = (item.get("name") or "").strip()
    if not name:
        return None
    return {"name": name, "article": item.get("article"),
            "aliases": list(item.get("aliases") or []), "tags": dict(item.get("tags") or {})}


def from_curated(items: list, *, source: str, tags: dict | None = None,
                 measure: str | None = None) -> list[dict]:
    """Curated items -> pool entries.

    `tags` assigns attributes by name: {"regiao": {"Nordeste": ["Acarajé", ...]}};
    a name listed under several values gets a list. `measure="wf"` skips the
    pt.wikipedia attention signal (e.g. slang, where an article of the same
    title would be about something else).
    """
    from .http import normalize
    by_name: dict[str, dict] = {}
    for key, values in (tags or {}).items():
        for value, names in values.items():
            for raw in names:
                bucket = by_name.setdefault(normalize(raw.split("|")[0].split("@")[0]), {})
                current = bucket.get(key)
                if current is None:
                    bucket[key] = value
                elif isinstance(current, list):
                    if value not in current:
                        current.append(value)
                elif current != value:
                    bucket[key] = [current, value]
    out = []
    for raw in items:
        item = parse_curated_item(raw)
        if not item or not item["name"]:
            continue
        attrs = {"source": source, **item["tags"]}
        for label in [item["name"], *item["aliases"]]:
            for key, value in by_name.get(normalize(label), {}).items():
                current = attrs.get(key)
                if current is None:
                    attrs[key] = value
                else:
                    merged = current if isinstance(current, list) else [current]
                    for v in value if isinstance(value, list) else [value]:
                        if v not in merged:
                            merged.append(v)
                    attrs[key] = merged if len(merged) > 1 else merged[0]
        article = None if measure == "wf" else (item["article"] or item["name"])
        out.append({
            "name": item["name"],
            "qid": None,
            "article": article,
            "sl": 0,
            "gravity": None,
            "aliases": item["aliases"],
            "curated": True,
            "noarticle": measure == "wf",
            "attrs": attrs,
        })
    return out


def enrich(entries: list[dict]) -> list[dict]:
    """Resolve pt.wikipedia article + QID + sitelink count for every entry.

    A title that does not exist, or lands on a disambiguation page, is cleared
    (article=None) so it is never measured against the wrong page.
    """
    todo = [e for e in entries if e.get("article") and not e.get("resolved")
            and (e.get("curated") or not e.get("qid"))]
    if todo:
        mapping = resolve_titles([e["article"] for e in todo])
        for entry in todo:
            hit = mapping.get(entry["article"]) or {}
            entry["resolved"] = True
            if not hit.get("title") or hit.get("disambig"):
                entry["unresolved"] = entry["article"]
                entry["article"] = None
                continue
            entry["article"] = hit["title"]
            if not entry.get("qid"):
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
