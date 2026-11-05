"""Concrete answer universes (acervo v2).

Three kinds of source, merged per pool (curated first, so its display names and
aliases win; later sources only add what is new, matched by QID or by name):

  * curated JSON in tools/dataset/curated/ (hand-checked, with aliases/tags);
  * Wikidata SPARQL (people, works, places; pt-br labels and sitelinks);
  * pt.wikipedia categories (authoritative membership lists).

Every entry ends up with a pt.wikipedia article when one exists, so the
attention measurement is available; curated entries without an article are
kept and measured on the remaining signals.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

from .catcrawl import clean_title, crawl, links_of
from .http import normalize, sparql
from .universes import _clean, category_members, enrich, from_curated
from .wdpools import municipalities, query

CURATED = Path(__file__).resolve().parent / "curated"
BINOMIAL = re.compile(r"^[A-Z][a-z]+ [a-z]+$")

BR = "wd:Q155"
PT = "wd:Q45"

DROPPED_POOLS = {
    "pokemon": "fora: universo sem ângulo brasileiro (pedido do dono)",
    "pokemon_extra": "fora: idem",
    "anime": "fora: títulos no Wikidata vêm em japonês/inglês; sem cobertura em português",
    "videogame": "fora: franquia x jogo confunde; acervo do Wikidata não bate com o que se digita",
    "heroi": "fora: sem ângulo lusófono; universo norte-americano",
    "marca_global": "fora: o jogo agora tem 'marca brasileira' grande; global confundia",
    "banda": "fora: substituído por bandas brasileiras",
    "comida_mundo": "fora: substituído por culinária portuguesa e brasileira",
}


def curated(name: str) -> list[dict]:
    path = CURATED / f"{name}.json"
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise RuntimeError(f"curated file {path} is unreadable: {exc}") from exc
    return from_curated(data.get("items", []), source=data.get("source", ""),
                        tags=data.get("tags"), measure=data.get("measure"))


def from_category(cat: str, *, depth: int = 1, exclude: tuple[str, ...] = (),
                  skip: tuple[str, ...] = (), source: str | None = None,
                  attrs: dict | None = None) -> list[dict]:
    found = crawl(cat, depth, exclude)
    out = []
    skip_re = [re.compile(s, re.I) for s in skip]
    for title, where in found.items():
        if any(r.search(title) for r in skip_re):
            continue
        out.append({"name": clean_title(title), "qid": None, "article": title, "sl": 0,
                    "gravity": None, "aliases": [],
                    "attrs": {"source": source or f"https://pt.wikipedia.org/wiki/Categoria:{cat}",
                              "cat": where, **(attrs or {})}})
    return out


def city_key(entry: dict) -> str:
    return normalize(entry["name"]) + "/" + str(entry["attrs"].get("uf") or "")


def merge(*groups: list[dict], keyfn=None) -> list[dict]:
    """Union of entries. Same QID or same normalized name/alias = same answer:
    the first one wins, the later name becomes an alias, attrs are merged."""
    out: list[dict] = []
    by_qid: dict[str, dict] = {}
    by_key: dict[str, dict] = {}
    for group in groups:
        for entry in group:
            entry.setdefault("aliases", [])
            key = keyfn(entry) if keyfn else normalize(entry["name"])
            if not normalize(entry["name"]):
                continue
            hit = (by_qid.get(entry["qid"]) if entry.get("qid") else None) or by_key.get(key)
            if hit is None and entry.get("article"):
                hit = by_key.get("@" + entry["article"])
            if hit is not None:
                if normalize(hit["name"]) != normalize(entry["name"]) and entry["name"] not in hit["aliases"]:
                    hit["aliases"].append(entry["name"])
                for alias in entry["aliases"]:
                    if alias not in hit["aliases"]:
                        hit["aliases"].append(alias)
                for k, v in entry["attrs"].items():
                    current = hit["attrs"].get(k)
                    if current is None:
                        hit["attrs"][k] = v
                    elif k not in ("source", "cat") and current != v:
                        merged = current if isinstance(current, list) else [current]
                        for item in v if isinstance(v, list) else [v]:
                            if item not in merged:
                                merged.append(item)
                        hit["attrs"][k] = merged
                if not hit.get("qid") and entry.get("qid"):
                    hit["qid"] = entry["qid"]
                if not hit.get("article") and entry.get("article"):
                    hit["article"] = entry["article"]
                hit["sl"] = max(hit.get("sl") or 0, entry.get("sl") or 0)
                if entry.get("gravity") and not hit.get("gravity"):
                    hit["gravity"] = entry["gravity"]
                continue
            out.append(entry)
            by_key[key] = entry
            if not keyfn:
                for alias in entry["aliases"]:
                    by_key.setdefault(normalize(alias), entry)
            if entry.get("article"):
                by_key.setdefault("@" + entry["article"], entry)
            if entry.get("qid"):
                by_qid[entry["qid"]] = entry
    return out


LEGACY_GENRE = {"forró": "forro", "axé": "axe", "pagode": "samba", "bossa nova": "mpb",
                "jovem guarda": "pop", "brega": "pop"}


def retag(entries: list[dict], source_file: str, tag: str) -> None:
    """Apply one tag table of another curated file to these entries, by name/alias."""
    data = json.loads((CURATED / f"{source_file}.json").read_text(encoding="utf-8"))
    table: dict[str, list] = {}
    for value, names in (data.get("tags") or {}).get(tag, {}).items():
        for name in names:
            table.setdefault(normalize(name), []).append(value)
    for entry in entries:
        values: list = []
        for label in [entry["name"], *entry.get("aliases", [])]:
            for v in table.get(normalize(label), []):
                if v not in values:
                    values.append(v)
        if values:
            current = entry["attrs"].get(tag)
            merged = ([current] if isinstance(current, str) else list(current or [])) + values
            merged = list(dict.fromkeys(merged))
            entry["attrs"][tag] = merged if len(merged) > 1 else merged[0]


def _people(occupations: str, country: str = BR, limit: int = 400, extra: str = "") -> list[dict]:
    body = f"?item wdt:P106/wdt:P279? ?occ . VALUES ?occ {{ {occupations} }} ?item wdt:P27 {country} . {extra}"
    return query(body, limit=limit, gender=True)


def load_all() -> dict[str, list[dict]]:
    """Return every pool, enriched with article/QID/sitelinks."""
    from .queries import (
        COUNTRY_QUERY,
        ELEMENT_QUERY,
        PRESIDENTS_QUERY,
        STATE_DETAIL_QUERY,
        WORLD_CAPITAL_QUERY,
        WORLD_CITY_QUERY,
    )

    pools: dict[str, list[dict]] = {}

    # ---------------------------------------------------------------- Brasil: lugares
    pools["uf"] = _clean(sparql(STATE_DETAIL_QUERY))
    pools["cidade"] = merge(curated("cidades_extra"), municipalities(20_000), keyfn=city_key)
    pools["cidades_historicas"] = curated("cidades_historicas")
    pools["presidente"] = merge(curated("presidentes"), [e for e in _clean(sparql(PRESIDENTS_QUERY))
                                                        if not e["name"].startswith("Junta")])
    pools["rio"] = merge(curated("rios"), query(
        "?item wdt:P31/wdt:P279* wd:Q4022 ; wdt:P17 wd:Q155 .", limit=320))
    pools["parque"] = merge(curated("parques"), query(
        "?item wdt:P31 wd:Q46169 ; wdt:P17 wd:Q155 .", limit=120))
    pools["estadio"] = merge(curated("estadios"), query(
        "?item wdt:P31/wdt:P279* wd:Q483110 ; wdt:P17 wd:Q155 .", limit=160))
    pools["praias"] = curated("praias")
    pools["pontos_turisticos"] = curated("pontos_turisticos")
    pools["bairro_rio"] = merge(curated("bairros_rio"), query("?item wdt:P31 wd:Q20683285 .", limit=400))
    pools["bairro_sp"] = merge(curated("bairros_sp"), from_category(
        "Bairros da cidade de São Paulo", depth=1, skip=(r"\(desambiguação\)",)))

    # ---------------------------------------------------------------- futebol e esporte
    pools["jogador"] = merge(curated("jogadores"), query(
        "?item wdt:P54 wd:Q83459 .", limit=650))
    pools["jogadora"] = merge(curated("jogadoras"), query("?item wdt:P54 wd:Q757014 .", limit=300))
    pools["time"] = curated("times")
    pools["time_pt"] = curated("times_pt")
    pools["jogador_pt"] = merge(curated("jogadores_pt"), query("?item wdt:P54 wd:Q267245 .", limit=320))
    pools["volei"] = merge(curated("volei"), query(
        "{ ?item wdt:P106 wd:Q15117302 } UNION { ?item wdt:P106 wd:Q17361156 } ?item wdt:P27 wd:Q155 .",
        limit=320, gender=True))
    pools["f1"] = merge(curated("f1"), query(
        "?item wdt:P106 wd:Q10841764 ; wdt:P27 wd:Q155 .", limit=100))
    pools["medalhista"] = merge(curated("medalhistas"), from_category(
        "Medalhistas olímpicos do Brasil", depth=1))

    # ---------------------------------------------------------------- comida e bebida
    pools["frutas_nativas"] = merge(curated("frutas_br"), curated("frutas_nativas"))
    pools["pratos_tipicos"] = curated("pratos_br")
    pools["doces"] = curated("doces_br")
    pools["salgados"] = curated("salgados")
    pools["bebidas"] = curated("bebidas_br")
    pools["cervejas"] = curated("cervejas")
    pools["prato_pt"] = curated("pratos_pt")

    # ---------------------------------------------------------------- TV, música, cinema, letras
    novelas = merge(curated("novelas_br"), curated("novelas"))
    for decade in (1960, 1970, 1980, 1990, 2000, 2010, 2020):
        novelas = merge(novelas, from_category(
            f"Telenovelas da TV Globo da década de {decade}", depth=0,
            attrs={"emissora": "Globo", "decada": decade}))
    for cat, network in (("Telenovelas do SBT", "SBT"), ("Telenovelas da RecordTV", "Record"),
                         ("Telenovelas da Record (rede de televisão)", "Record"), ("Telenovelas da Rede Manchete", "Manchete"),
                         ("Telenovelas da Band", "Band"), ("Telenovelas da Rede Tupi", "Tupi"), ("Telenovelas da TV Tupi", "Tupi"),
                         ("Telenovelas da TV Excelsior", "Excelsior")):
        novelas = merge(novelas, from_category(cat, depth=0, attrs={"emissora": network},
                                               skip=(r"trilha sonora", r"^Elenco", r"\(desenho",
                                                     r"filme", r"^Clube do")))
    slot_pages = {"seis": "Lista de telenovelas das seis da TV Globo",
                  "sete": "Lista de telenovelas das sete da TV Globo",
                  "oito": "Lista de telenovelas das oito da TV Globo",
                  "nove": "Lista de telenovelas das nove da TV Globo"}
    slot_of: dict[str, str] = {}
    for slot, page in slot_pages.items():
        for title in links_of(page):
            slot_of.setdefault(title, slot)
    for entry in novelas:
        slot = slot_of.get(entry.get("article") or "")
        if slot and "faixa" not in entry["attrs"]:
            entry["attrs"]["faixa"] = slot
    pools["novelas"] = novelas
    pools["personagens_novela"] = curated("personagens_novela")
    pools["filmes"] = merge(curated("filmes_br"), curated("filmes"), query(
        "?item wdt:P31/wdt:P279? wd:Q11424 ; wdt:P495 wd:Q155 .", limit=450, year_prop="P577"))
    singers = "wd:Q177220 wd:Q488205 wd:Q2252262"
    pools["cantores"] = merge(curated("cantores_br"), curated("cantores"), _people(singers, limit=700))
    for entry in pools["cantores"]:
        if " & " in entry["name"] or entry["name"].startswith("Trio "):
            entry["attrs"]["dupla"] = True
        raw = entry["attrs"].get("genero")
        values = raw if isinstance(raw, list) else [raw]
        sexes = [v for v in values if v in ("feminino", "masculino")]
        legacy = [v for v in values if v and v not in ("feminino", "masculino")]
        if legacy:
            if sexes:
                entry["attrs"]["genero"] = sexes[0]
            else:
                entry["attrs"].pop("genero", None)
            if "genero_musical" not in entry["attrs"]:
                mapped = list(dict.fromkeys(LEGACY_GENRE.get(v, v) for v in legacy))
                entry["attrs"]["genero_musical"] = mapped if len(mapped) > 1 else mapped[0]
    pools["bandas"] = merge(curated("bandas_br"), query(
        "?item wdt:P31 wd:Q215380 ; wdt:P495 wd:Q155 .", limit=300))
    retag(pools["bandas"], "cantores_br", "genero_musical")
    # Genre questions accept solo artists, duos and groups alike.
    def _copy(entries):
        return [dict(e, aliases=list(e.get("aliases") or []), attrs=dict(e["attrs"])) for e in entries]
    tagged = json.loads((CURATED / "cantores_br.json").read_text(encoding="utf-8"))["tags"]["genero_musical"]
    extra = [{"name": n, "qid": None, "article": n, "sl": 0, "gravity": None, "aliases": [],
              "curated": True, "attrs": {"source": "cantores_br.json (genero_musical)"}}
             for names in tagged.values() for n in names]
    pools["musica"] = merge(_copy(pools["cantores"]), _copy(pools["bandas"]), extra)
    retag(pools["musica"], "cantores_br", "genero_musical")
    pools["cantor_pt"] = merge(curated("cantores_pt"), _people(singers, PT, limit=260))
    pools["escritores"] = merge(curated("escritores_br"), curated("escritores"), _people("wd:Q36180 wd:Q49757 wd:Q6625963", limit=600))
    pools["escritor_pt"] = merge(curated("escritores_pt"), _people("wd:Q36180 wd:Q49757 wd:Q6625963", PT, limit=300))
    pools["atores"] = merge(curated("atores_br"), curated("atores"), _people("wd:Q33999 wd:Q10800557", limit=900))
    pools["apresentador"] = merge(curated("apresentadores"), _people("wd:Q947873", limit=400))
    pools["humorista"] = merge(curated("humoristas"), _people("wd:Q245068 wd:Q12406482", limit=250))
    pools["youtuber"] = merge(curated("youtubers"), _people("wd:Q17125263", limit=260))
    pools["programas_tv"] = curated("programas_tv")
    pools["bbb"] = merge(curated("bbb_v2"), curated("bbb"), curated("bbb_campeoes_v2"))
    pools["bbb_campeoes"] = curated("bbb_campeoes_v2")
    pools["tv_globinho"] = curated("tv_globinho")
    pools["desenhos"] = merge(curated("desenhos"), curated("desenhos_extra"))
    pools["turma_monica"] = merge(curated("turma_monica"), from_category(
        "Personagens da Turma da Mônica", depth=1,
        skip=(r"^Turma d", r"^A Rádio", r"^Chico Bento[,:]", r"Goiabeira", r"^O Burrico",
              r"^Tina:", r"Chico Bento Moço", r"^Lara e")))
    pools["escola_samba"] = merge(
        curated("escolas_samba"),
        from_category("Escolas de samba da cidade do Rio de Janeiro", depth=0, attrs={"cidade": "Rio"}),
        from_category("Escolas de samba da cidade de São Paulo", depth=0, attrs={"cidade": "São Paulo"},
                      skip=(r"^Torcida", r"^Seo ", r"^Seu Chiclé", r"^Geraldo Filme", r"^Sólon",
                            r"^Ernesto Teixeira")))
    pools["cientista"] = curated("cientistas")

    # ---------------------------------------------------------------- cultura popular e língua
    for key in ("aves", "mamiferos", "folclore", "festas", "dancas", "instrumentos"):
        pools[key] = curated(key)
    pools["aves"] = merge(pools["aves"], curated("aves_comuns"), curated("aves_extra"),
                          [e for e in category_members("Aves do Brasil")
                           if not BINOMIAL.match(e["name"])])
    pools["mamiferos"] = merge(pools["mamiferos"], curated("mamiferos_comuns"),
                               [e for e in category_members("Mamíferos do Brasil")
                                if not BINOMIAL.match(e["name"])])
    for key in ("folclore", "festas", "dancas", "instrumentos"):
        pools[key] = merge(pools[key], curated(f"{key}_extra"))
    pools["palavras_tupi"] = merge(curated("palavras_tupi"), curated("palavras_tupi_extra"))
    pools["girias"] = curated("girias_v2")
    pools["palavras_pt"] = curated("palavras_pt")
    pools["marcas"] = curated("marcas_br")

    # ---------------------------------------------------------------- lusofonia e mundo
    pools["cidade_pt"] = merge(curated("cidades_pt"), query("?item wdt:P31 wd:Q13217644 .", limit=400,
                                                            pop=True))
    pools["pais"] = merge(curated("paises_alias"), _clean(sparql(COUNTRY_QUERY)))
    pools["capital_mundo"] = merge(curated("capitais_alias"), _clean(sparql(WORLD_CAPITAL_QUERY)))
    pools["elemento"] = merge(curated("elementos_alias"), _clean(sparql(ELEMENT_QUERY)))
    capitals_copy = [dict(e, aliases=list(e.get("aliases") or []), attrs=dict(e["attrs"]))
                     for e in pools["capital_mundo"]]
    pools["cidade_mundo"] = merge(curated("cidades_mundo"), capitals_copy,
                                  _clean(sparql(WORLD_CITY_QUERY)))
    brazilian = {normalize(e["name"]) for e in pools["cidade"] if (e.get("gravity") or 0) > 400_000}
    brazilian |= {"brasilia", "sao paulo", "rio de janeiro"}
    pools["cidade_mundo"] = [e for e in pools["cidade_mundo"] if normalize(e["name"]) not in brazilian]

    for key in list(pools):
        if not pools[key]:
            del pools[key]
            continue
        pools[key] = enrich(pools[key])
    return pools


if __name__ == "__main__":
    data = load_all()
    for key, items in data.items():
        print(f"{key:20s} {len(items):4d}  e.g. {items[0]['name'] if items else '-'}")
