"""Concrete answer universes.

Administrative / encyclopedic universes come from Wikidata SPARQL (authoritative,
with sitelink counts). Cultural universes come from curated JSON files built by
the content agents, each verified against pt.wikipedia.

Every entry ends up with at least a pt.wikipedia article, so the pageviews
measurement is available for all of them.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from string import Template

from .http import sparql
from .universes import (
    _clean,
    category_members,
    enrich,
    from_curated,
    instances_of,
    merge_pools,
    people,
)

CURATED = Path(__file__).resolve().parent / "curated"
BINOMIAL = re.compile(r"^[A-Z][a-z]+ [a-z]+$")

CITIES_TMPL = Template("""
SELECT ?item ?itemLabel ?sl ?article ?pop ?stateLabel WHERE {
  {
    SELECT ?item (MAX(?pop_) AS ?pop) (MAX(?sl_) AS ?sl)
    WHERE {
      ?item wdt:P31 wd:$type .
      ?item wdt:P1082 ?pop_ .
      OPTIONAL { ?item wikibase:sitelinks ?sl_ . }
    }
    GROUP BY ?item
    ORDER BY DESC(?pop)
    LIMIT $limit
  }
  OPTIONAL { ?article schema:about ?item ; schema:isPartOf <https://pt.wikipedia.org/> }
  OPTIONAL { ?item wdt:P131 ?state }
  SERVICE wikibase:label { bd:serviceParam wikibase:language "pt,en". }
}
""")

BY_COUNTRY_TMPL = Template("""
SELECT ?item ?itemLabel ?sl ?article WHERE {
  {
    SELECT ?item (MAX(?sl_) AS ?sl) (SAMPLE(?article_) AS ?article)
    WHERE {
      ?item wdt:P31/wdt:P279* wd:$type .
      ?item wdt:P17 wd:Q155 .
      OPTIONAL { ?item wikibase:sitelinks ?sl_ . }
      OPTIONAL { ?article_ schema:about ?item ; schema:isPartOf <https://pt.wikipedia.org/> . }
    }
    GROUP BY ?item
    ORDER BY DESC(?sl)
    LIMIT $limit
  }
  SERVICE wikibase:label { bd:serviceParam wikibase:language "pt,en". }
}
""")


def _cities(limit: int = 320) -> list[dict]:
    from .wd import qid
    query = CITIES_TMPL.substitute(type=qid("município do Brasil"), limit=limit)
    entries = _clean(sparql(query))
    for entry in entries:
        entry["attrs"]["uf"] = entry.pop("state", None) or entry["attrs"].get("uf")
    return entries


def _by_country(type_label: str, limit: int) -> list[dict]:
    from .wd import qid
    query = BY_COUNTRY_TMPL.substitute(type=qid(type_label), limit=limit)
    return _clean(sparql(query))


def _curated_file(name: str) -> list[dict]:
    path = CURATED / f"{name}.json"
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise RuntimeError(f"curated file {path} is unreadable: {exc}") from exc
    return from_curated(data.get("items", []), source=data.get("source", ""))


def load_all() -> dict[str, list[dict]]:
    """Return every pool, enriched with article/QID/sitelinks, deduped by name."""
    from .queries import (
        COUNTRY_QUERY,
        ELEMENT_QUERY,
        PRESIDENTS_QUERY,
        STATE_DETAIL_QUERY,
        WORLD_CAPITAL_QUERY,
        WORLD_CITY_QUERY,
    )

    pools: dict[str, list[dict]] = {}
    pools["uf"] = _clean(sparql(STATE_DETAIL_QUERY))
    pools["cidade"] = _cities()
    pools["presidente"] = _clean(sparql(PRESIDENTS_QUERY))
    pools["jogador"] = people("futebolista", limit=220,
                              extra="?item wdt:P54 ?team . ?team wdt:P31 wd:Q6979593 .")
    pools["time"] = _by_country("clube de futebol", 90)
    pools["rio"] = _by_country("rio", 110)
    pools["parque"] = _by_country("parque nacional", 70)
    pools["estadio"] = _by_country("estádio de futebol", 70)

    # international universes
    pools["pais"] = _clean(sparql(COUNTRY_QUERY))
    pools["capital_mundo"] = _clean(sparql(WORLD_CAPITAL_QUERY))
    pools["elemento"] = _clean(sparql(ELEMENT_QUERY))
    pools["cidade_mundo"] = _clean(sparql(WORLD_CITY_QUERY))
    pools["videogame"] = instances_of("jogo eletrônico", limit=320)
    pools["anime"] = instances_of("série de anime", limit=260)
    pools["banda"] = instances_of("banda musical", limit=260)

    for key in ("frutas_nativas", "pratos_tipicos", "doces", "novelas", "filmes",
                "cantores", "escritores", "atores", "marcas", "aves", "mamiferos",
                "folclore", "festas", "dancas", "instrumentos", "palavras_tupi",
                "girias", "bebidas", "bandas", "praias", "pontos_turisticos",
                "bbb", "bbb_campeoes", "tv_globinho", "desenhos",
                "pokemon", "heroi", "comida_mundo", "marca_global"):
        items = _curated_file(key)
        if items:
            pools[key] = items

    # Bigger universes for the broad prompts: popular names people actually say,
    # plus every vernacular member of the pt.wikipedia category (no binomials).
    if "aves" in pools:
        birds = [entry for entry in category_members("Aves do Brasil")
                 if not BINOMIAL.match(entry["name"])]
        pools["aves"] = merge_pools(pools["aves"], _curated_file("aves_comuns"), birds)
    if "mamiferos" in pools:
        mammals = [entry for entry in category_members("Mamíferos do Brasil")
                   if not BINOMIAL.match(entry["name"])]
        pools["mamiferos"] = merge_pools(pools["mamiferos"],
                                         _curated_file("mamiferos_comuns"), mammals)
    pools["comida_mundo"] = merge_pools(_curated_file("comida_mundo"),
                                        _curated_file("comida_mundo_extra"))
    pools["pratos_tipicos"] = merge_pools(_curated_file("pratos_tipicos"),
                                          _curated_file("pratos_extra"))
    pools["pokemon"] = merge_pools(_curated_file("pokemon"), _curated_file("pokemon_extra"))
    all_keys = ("uf", "cidade", "presidente", "jogador", "time", "rio", "parque",
                "estadio", "frutas_nativas", "pratos_tipicos", "doces", "novelas",
                "filmes", "cantores", "escritores", "atores", "marcas", "aves",
                "mamiferos", "folclore", "festas", "dancas", "instrumentos",
                "palavras_tupi", "girias", "bebidas", "bandas", "praias",
                "pontos_turisticos", "bbb", "bbb_campeoes", "tv_globinho", "desenhos",
                "pais", "capital_mundo", "elemento", "cidade_mundo", "videogame",
                "anime", "banda", "pokemon", "heroi", "comida_mundo", "marca_global")
    for key in all_keys:
        if key in pools and pools[key]:
            pools[key] = enrich(pools[key])
    return pools


if __name__ == "__main__":
    data = load_all()
    for key, items in data.items():
        print(f"{key:20s} {len(items):4d}  e.g. {items[0]['name'] if items else '-'}")
