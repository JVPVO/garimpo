"""Human-checked tags that let prompts constrain a pool.

Only facts that are unambiguous are encoded here. Anything uncertain is left
out, and a prompt whose filtered pool is too small is dropped at build time
instead of shipping a wrong constraint.
"""
from __future__ import annotations

from .http import normalize

REGION_BY_UF = {
    "acre": "Norte", "amapa": "Norte", "amazonas": "Norte", "para": "Norte",
    "rondonia": "Norte", "roraima": "Norte", "tocantins": "Norte",
    "alagoas": "Nordeste", "bahia": "Nordeste", "ceara": "Nordeste",
    "maranhao": "Nordeste", "paraiba": "Nordeste", "pernambuco": "Nordeste",
    "piaui": "Nordeste", "rio grande do norte": "Nordeste", "sergipe": "Nordeste",
    "espirito santo": "Sudeste", "minas gerais": "Sudeste",
    "rio de janeiro": "Sudeste", "sao paulo": "Sudeste",
    "parana": "Sul", "rio grande do sul": "Sul", "santa catarina": "Sul",
    "distrito federal": "Centro-Oeste", "goias": "Centro-Oeste",
    "mato grosso": "Centro-Oeste", "mato grosso do sul": "Centro-Oeste",
}

LANDLOCKED = {"acre", "amazonas", "distrito federal", "goias", "minas gerais",
              "mato grosso", "mato grosso do sul", "rondonia", "tocantins"}

UF_ALIASES = {
    "ac": "Acre", "al": "Alagoas", "ap": "Amapá", "am": "Amazonas", "ba": "Bahia",
    "ce": "Ceará", "df": "Distrito Federal", "es": "Espírito Santo", "go": "Goiás",
    "ma": "Maranhão", "mt": "Mato Grosso", "ms": "Mato Grosso do Sul",
    "mg": "Minas Gerais", "pa": "Pará", "pb": "Paraíba", "pr": "Paraná",
    "pe": "Pernambuco", "pi": "Piauí", "rj": "Rio de Janeiro",
    "rn": "Rio Grande do Norte", "rs": "Rio Grande do Sul", "ro": "Rondônia",
    "rr": "Roraima", "sc": "Santa Catarina", "sp": "São Paulo", "se": "Sergipe",
    "to": "Tocantins",
}

GLOBAL_ALIASES: dict[tuple[str, str], list[str]] = {
    # v3: forms players really type (probes_g.json)
    ("cidade", "rio de janeiro"): ["Rio"],
    ("cidade", "sao paulo"): ["Sampa"],
    ("cidade", "belo horizonte"): ["BH", "Beagá"],
    ("cidade", "florianopolis"): ["Floripa"],
    ("cidade", "porto alegre"): ["POA"],
    ("pratos_tipicos", "cuscuz nordestino"): ["Cuscuz"],
    ("humorista", "renato aragao"): ["Didi"],
    ("presidente", "luiz inacio lula da silva"): ["Lula"],
    ("politico", "luiz inacio lula da silva"): ["Lula"],
    ("presidente", "fernando henrique cardoso"): ["FHC", "Fernando Henrique"],
    ("politico", "fernando henrique cardoso"): ["FHC", "Fernando Henrique"],
    ("presidente", "juscelino kubitschek"): ["JK", "Juscelino"],
    ("jogador", "edson arantes do nascimento"): ["Pelé"],

    ("pais", "estados unidos"): ["EUA", "USA", "Estados Unidos da América"],
    ("pais", "reino unido"): ["UK", "Grã-Bretanha"],
    ("pais", "emirados arabes unidos"): ["EAU"],
    ("pais", "republica tcheca"): ["Tchéquia"],
    ("pais", "coreia do sul"): ["Coreia"],
    ("capital_mundo", "moscovo"): ["Moscou"],
    ("capital_mundo", "nova iorque"): ["Nova York"],
    ("capital_mundo", "pequim"): ["Beijing"],
    ("capital_mundo", "toquio"): ["Tokyo"],
    ("capital_mundo", "banguecoque"): ["Bangkok"],
    ("capital_mundo", "copenhague"): ["Copenhaga"],
    ("capital_mundo", "kiev"): ["Kyiv"],
    ("heroi", "homem aranha"): ["Spiderman", "Spider-Man"],
    ("heroi", "homem de ferro"): ["Iron Man"],
    ("heroi", "mulher maravilha"): ["Wonder Woman"],
    ("heroi", "capitao america"): ["Captain America"],
    ("heroi", "viuva negra"): ["Black Widow"],
    ("heroi", "doutor estranho"): ["Doctor Strange"],
    ("heroi", "pantera negra"): ["Black Panther"],
    ("heroi", "feiticeira escarlate"): ["Scarlet Witch"],
    ("videogame", "grand theft auto v"): ["GTA V", "GTA 5"],
    ("aves", "pica pau"): ["Picapau", "Pica pau", "Papa-pau"],
    ("aves", "bem te vi"): ["Bemtevi", "Bem ti vi"],
    ("aves", "joao de barro"): ["Joao de barro", "João-de-barro"],
    ("mamiferos", "lobo guara"): ["Lobo", "Lobo guará"],
    ("comida_mundo", "estrogonofe"): ["Strogonoff", "Stroganoff", "Estrogonofe"],
    ("pratos_tipicos", "estrogonofe"): ["Strogonoff", "Stroganoff"],
    ("pratos_tipicos", "quibe"): ["Kibe"],
    ("pratos_tipicos", "cachorro quente"): ["Dogão", "Hot dog"],
    ("comida_mundo", "cachorro quente"): ["Hot dog", "Dogão"],
}

STATE_CAPITALS = {
    "rio branco", "maceio", "macapa", "manaus", "salvador", "fortaleza", "brasilia",
    "vitoria", "goiania", "sao luis", "cuiaba", "campo grande", "belo horizonte", "belem",
    "joao pessoa", "curitiba", "recife", "teresina", "rio de janeiro", "natal",
    "porto alegre", "porto velho", "boa vista", "florianopolis", "sao paulo", "aracaju",
    "palmas",
}

POSITION_WORDS = (
    ("goleiro", ("goleiro", "guarda-redes", "goalkeeper")),
    ("lateral", ("lateral", "ala", "full-back", "wing-back", "fullback")),
    ("zagueiro", ("zagueiro", "defesa central", "defensor", "centre-back", "center-back",
                  "defender", "libero", "líbero", "beque")),
    ("meia", ("meio-campista", "meio campo", "médio", "medio", "meia", "volante",
              "midfielder", "playmaker", "meio-campo")),
    ("atacante", ("atacante", "avançado", "ponta", "centroavante", "forward", "striker",
                  "winger", "ponta-de-lança", "extremo")),
)


def positions_from_labels(labels: list[str]) -> list[str]:
    out: list[str] = []
    for label in labels:
        low = label.lower()
        for position, words in POSITION_WORDS:
            if any(w in low for w in words) and position not in out:
                out.append(position)
    return out


def apply_tags(pools: dict[str, list[dict]]) -> None:
    for entry in pools.get("uf", []):
        key = normalize(entry["name"])
        entry["attrs"]["regiao"] = REGION_BY_UF.get(key)
        entry["attrs"]["litoral"] = key not in LANDLOCKED

    seen: dict[str, int] = {}
    for entry in pools.get("cidade", []):
        seen[normalize(entry["name"])] = seen.get(normalize(entry["name"]), 0) + 1
    for entry in pools.get("cidade", []):
        if seen[normalize(entry["name"])] > 1 and entry["attrs"].get("uf"):
            entry.setdefault("aliases", []).append(entry["name"])
            entry["name"] = f"{entry['name']} ({entry['attrs']['uf']})"
    from .wdpools import REGION_OF_UF
    for entry in pools.get("cidade", []):
        uf = entry["attrs"].get("uf")
        if isinstance(uf, str) and not entry["attrs"].get("regiao"):
            entry["attrs"]["regiao"] = REGION_OF_UF.get(uf)
        big = (entry.get("gravity") or 0) > 150_000 or entry["attrs"].get("uf") == "DF"
        if normalize(entry["name"].split(" (")[0]) in STATE_CAPITALS and big:
            entry["attrs"]["capital"] = True


def aliases_for(entry: dict, pool: str) -> list[str]:
    """Candidate aliases: curated, Wikidata pt/pt-br labels, siglas, prefixes.
    Collisions inside a prompt are removed later, in build."""
    out: list[str] = list(entry.get("aliases") or [])
    out += list(entry.get("wd_aliases") or [])
    name = entry["name"]
    if pool == "uf":
        for abbrev, full in UF_ALIASES.items():
            if normalize(full) == normalize(name):
                out.append(abbrev.upper())
    if pool == "time":
        for prefix in ("Clube de Regatas ", "Clube Atlético ", "Sport Club ",
                       "Sociedade Esportiva ", "Associação Atlética ",
                       "Esporte Clube ", "Clube "):
            if name.startswith(prefix):
                out.append(name[len(prefix):])
    for alias in GLOBAL_ALIASES.get((pool, normalize(name)), []):
        out.append(alias)
    return out
