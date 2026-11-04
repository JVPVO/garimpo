"""Wikidata-backed universes (v2): people, works and places, with Brazilian
Portuguese labels first, pt.wikipedia article, sitelinks and a few facts.

Every query is cached on disk by the HTTP layer, so a rebuild is free.
"""
from __future__ import annotations

from string import Template

from .http import chunks, normalize, sparql
from .universes import _tail

PTWIKI = "<https://pt.wikipedia.org/>"

GENERIC_TMPL = Template("""
SELECT ?item ?itemLabel ?sl ?article ?pop ?year ?gender ?code WHERE {
  {
    SELECT ?item (MAX(?sl_) AS ?sl) (SAMPLE(?article_) AS ?article)
           (MAX(?pop_) AS ?pop) (MIN(?year_) AS ?year) (SAMPLE(?g_) AS ?gender)
           (SAMPLE(?code_) AS ?code)
    WHERE {
      $body
      OPTIONAL { ?item wikibase:sitelinks ?sl_ . }
      OPTIONAL { ?article_ schema:about ?item ; schema:isPartOf $wiki . }
      $extra
    }
    GROUP BY ?item
    ORDER BY $order
    LIMIT $limit
  }
  SERVICE wikibase:label { bd:serviceParam wikibase:language "pt-br,pt,en". }
}
""")

FEMALE = {"http://www.wikidata.org/entity/Q6581072", "http://www.wikidata.org/entity/Q1052281"}
MALE = {"http://www.wikidata.org/entity/Q6581097", "http://www.wikidata.org/entity/Q2449503"}


def query(body: str, *, limit: int = 300, order: str = "DESC(?sl)", gender: bool = False,
          year_prop: str | None = None, pop: bool = False, code_prop: str | None = None,
          source: str = "wikidata") -> list[dict]:
    extra = []
    if gender:
        extra.append("OPTIONAL { ?item wdt:P21 ?g_ . }")
    if year_prop:
        extra.append(f"OPTIONAL {{ ?item wdt:{year_prop} ?d_ . BIND(YEAR(?d_) AS ?year_) }}")
    if pop:
        extra.append("OPTIONAL { ?item wdt:P1082 ?pop_ . }")
    if code_prop:
        extra.append(f"OPTIONAL {{ ?item wdt:{code_prop} ?code_ . }}")
    rows = sparql(GENERIC_TMPL.substitute(body=body, wiki=PTWIKI, extra="\n".join(extra),
                                          order=order, limit=limit))
    out, seen = [], set()
    for row in rows:
        name = (row.get("itemLabel") or "").strip()
        item = (row.get("item") or "").rsplit("/", 1)[-1]
        if not name or (name.startswith("Q") and name[1:].isdigit()) or item in seen:
            continue
        seen.add(item)
        attrs: dict = {"source": source}
        if row.get("gender") in FEMALE:
            attrs["genero"] = "feminino"
        elif row.get("gender") in MALE:
            attrs["genero"] = "masculino"
        if row.get("year"):
            try:
                attrs["ano"] = int(float(row["year"]))
            except ValueError:
                pass
        if row.get("code"):
            attrs["code"] = row["code"]
        out.append({
            "name": name,
            "qid": item or None,
            "article": _tail(row.get("article")),
            "sl": int(float(row.get("sl") or 0)),
            "gravity": float(row["pop"]) if row.get("pop") else None,
            "attrs": attrs,
        })
    return out


ALIAS_TMPL = Template("""
SELECT ?item ?alt WHERE {
  VALUES ?item { $values }
  { ?item skos:altLabel ?alt . FILTER(LANG(?alt) IN ("pt", "pt-br")) }
  UNION
  { ?item rdfs:label ?alt . FILTER(LANG(?alt) IN ("pt", "pt-br")) }
}
""")


def aliases_for_qids(qids: list[str]) -> dict[str, list[str]]:
    """pt / pt-br labels and alt labels per QID (Wikidata), deduplicated."""
    out: dict[str, list[str]] = {}
    unique = [q for q in dict.fromkeys(qids) if q]
    for batch in chunks(unique, 150):
        values = " ".join(f"wd:{q}" for q in batch)
        for row in sparql(ALIAS_TMPL.substitute(values=values)):
            item = (row.get("item") or "").rsplit("/", 1)[-1]
            alt = (row.get("alt") or "").strip()
            if item and alt:
                bucket = out.setdefault(item, [])
                if normalize(alt) not in {normalize(a) for a in bucket}:
                    bucket.append(alt)
    return out


# IBGE municipality code: the first two digits are the state.
IBGE_UF = {
    "11": "RO", "12": "AC", "13": "AM", "14": "RR", "15": "PA", "16": "AP", "17": "TO",
    "21": "MA", "22": "PI", "23": "CE", "24": "RN", "25": "PB", "26": "PE", "27": "AL",
    "28": "SE", "29": "BA", "31": "MG", "32": "ES", "33": "RJ", "35": "SP", "41": "PR",
    "42": "SC", "43": "RS", "50": "MS", "51": "MT", "52": "GO", "53": "DF",
}
REGION_OF_UF = {
    "RO": "Norte", "AC": "Norte", "AM": "Norte", "RR": "Norte", "PA": "Norte", "AP": "Norte",
    "TO": "Norte", "MA": "Nordeste", "PI": "Nordeste", "CE": "Nordeste", "RN": "Nordeste",
    "PB": "Nordeste", "PE": "Nordeste", "AL": "Nordeste", "SE": "Nordeste", "BA": "Nordeste",
    "MG": "Sudeste", "ES": "Sudeste", "RJ": "Sudeste", "SP": "Sudeste", "PR": "Sul",
    "SC": "Sul", "RS": "Sul", "MS": "Centro-Oeste", "MT": "Centro-Oeste", "GO": "Centro-Oeste",
    "DF": "Centro-Oeste",
}


def municipalities(min_pop: int) -> list[dict]:
    """Brazilian municipalities above a population, with UF from the IBGE code."""
    rows = query("?item wdt:P31 wd:Q3184121 ; wdt:P1082 ?p0 . FILTER(?p0 >= %d)" % min_pop,
                 limit=6000, order="DESC(?pop)", pop=True, code_prop="P1585")
    for entry in rows:
        code = str(entry["attrs"].pop("code", "") or "")
        uf = IBGE_UF.get(code[:2])
        if uf:
            entry["attrs"]["uf"] = uf
            entry["attrs"]["regiao"] = REGION_OF_UF[uf]
    return rows
