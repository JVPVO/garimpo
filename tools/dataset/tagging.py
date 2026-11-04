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

BRASILEIRAO_CHAMPIONS = {    "flamengo", "palmeiras", "corinthians", "sao paulo", "santos", "cruzeiro",
    "vasco", "fluminense", "botafogo", "gremio", "internacional",
    "atletico mineiro", "bahia", "coritiba", "athletico", "sport", "guarani",
    "juventude",
}

GLOBAL_ALIASES: dict[tuple[str, str], list[str]] = {
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

SONG_GENRE = {
    "mpb": {"caetano veloso", "gilberto gil", "gal costa", "maria bethania",
            "chico buarque", "milton nascimento", "elis regina", "tom jobim",
            "vinicius de moraes", "joao gilberto", "djavan", "ivan lins",
            "marisa monte", "nando reis", "ana carolina", "cassia eller",
            "belchior", "ze ramalho", "alceu valenca", "lenine", "nazareno? "},
    "sertanejo": {"chitaozinho & xororo", "leandro & leonardo", "zere di camargo & luciano",
                  "zeze di camargo & luciano", "jorge & mateus", "michel telo",
                  "gusttavo lima", "luan santana", "marilia mendonca",
                  "maiara & maraisa", "henrique & juliano", "wesley safadao"},
    "rock": {"raul seixas", "rita lee", "cazuza", "renato russo", "legiao urbana",
             "titas", "paralamas do sucesso", "engenheiros do hawaii", "skank",
             "jota quest", "los hermanos", "mutantes", "secos & molhados"},
    "funk": {"emicida", "criolo", "marcelo d2", "racionais mc's", "seu jorge"},
    "samba": {"martinho da vila", "beth carvalho", "fundo de quintal", "zeca pagodinho",
              "clara nunes", "cartola", "paulinho da viola", "alcione"},
    "axe": {"ivete sangalo", "claudia leitte", "daniela mercury", "carlinhos brown",
            "chiclete com banana", "banda eva"},
    "forro": {"luiz gonzaga", "dominguinhos", "elba ramalho", "fagner", "alceu valenca",
              "genival lacerda"},
}

DISH_REGION = {
    "acaraje": "Bahia", "vatapa": "Bahia", "caruru": "Bahia", "mocoto": "Bahia",
    "moqueca": "Bahia", "bobo de camarao": "Bahia", "abara": "Bahia",
    "xinxim de galinha": "Bahia", "sarapatel": "Bahia",
    "pao de queijo": "Minas Gerais", "frango com quiabo": "Minas Gerais",
    "tutu a mineira": "Minas Gerais", "feijao tropeiro": "Minas Gerais",
    "angu": "Minas Gerais", "queijo minas": "Minas Gerais",
    "baiao de dois": "Nordeste", "carne de sol": "Nordeste", "cuscuz": "Nordeste",
    "tapioca": "Nordeste", "buchada de bode": "Nordeste", "arrumadinho": "Nordeste",
    "galinhada": "Nordeste", "paçoca": "Nordeste",
    "barreado": "Sul", "churrasco": "Sul", "galeto": "Sul", "cuca": "Sul",
    "xis": "Sul", "marreco recheado": "Sul", "arroz carreteiro": "Sul",
    "tacaca": "Norte", "manicoba": "Norte", "pato no tucupi": "Norte",
    "pirarucu": "Norte", "tucupi": "Norte", "jambu": "Norte",
    "virado a paulista": "Sudeste", "pastel": "Sudeste", "coxinha": "Sudeste",
    "feijoada": "Sudeste", "pizza": "Sudeste", "empada": "Sudeste",
}

FRUIT_BIOME = {
    "acai": "Amazônia", "cupuacu": "Amazônia", "guarana": "Amazônia",
    "bacuri": "Amazônia", "buriti": "Amazônia", "pupunha": "Amazônia",
    "tucuma": "Amazônia", "camu camu": "Amazônia", "graviola": "Amazônia",
    "abiu": "Amazônia", "biriba": "Amazônia", "tapereba": "Amazônia",
    "bacaba": "Amazônia", "mari": "Amazônia", "cubiu": "Amazônia",
    "pequi": "Cerrado", "cagaita": "Cerrado", "baru": "Cerrado",
    "murici": "Cerrado", "gabiroba": "Cerrado", "araticum": "Cerrado",
    "mangaba": "Cerrado", "pitomba": "Cerrado", "umbu": "Caatinga",
    "caja": "Caatinga", "licuri": "Caatinga", "jabuticaba": "Mata Atlântica",
    "cambuci": "Mata Atlântica", "jucara": "Mata Atlântica",
    "grumixama": "Mata Atlântica", "uvaia": "Mata Atlântica",
    "cabeludinha": "Mata Atlântica", "pitanga": "Mata Atlântica",
    "araca": "Mata Atlântica", "inga": "Mata Atlântica", "butia": "Pampa",
}

ANIMAL_BIOME = {
    "capivara": "Pantanal", "tuiuiu": "Pantanal", "jacare do pantanal": "Pantanal",
    "arara azul": "Pantanal", "tamandua bandeira": "Cerrado",
    "lobo guarau": "Cerrado", "lobo guara": "Cerrado", "seriema": "Cerrado",
    "ema": "Cerrado", "tatu canastra": "Cerrado", "veado campeiro": "Cerrado",
    "mico leao dourado": "Mata Atlântica", "muriqui": "Mata Atlântica",
    "sagui": "Mata Atlântica", "bugio": "Mata Atlântica",
    "boto cor de rosa": "Amazônia", "peixe boi": "Amazônia",
    "ariranha": "Amazônia", "onca pintada": "Amazônia",
    "gaviao real": "Amazônia", "uirapuru": "Amazônia",
    "onca parda": "Caatinga", "tatu peba": "Caatinga",
}


def _match(table: dict[str, str], name: str) -> str | None:
    key = normalize(name)
    if key in table:
        return table[key]
    for candidate, value in table.items():
        if candidate in key:
            return value
    return None


def apply_tags(pools: dict[str, list[dict]]) -> None:
    for entry in pools.get("uf", []):
        key = normalize(entry["name"])
        entry["attrs"]["regiao"] = REGION_BY_UF.get(key)
        entry["attrs"]["litoral"] = key not in LANDLOCKED

    for entry in pools.get("time", []):
        key = normalize(entry["name"])
        entry["attrs"]["campeao_brasileiro"] = any(c in key for c in BRASILEIRAO_CHAMPIONS)

    for entry in pools.get("cantores", []):
        key = normalize(entry["name"])
        for genre, names in SONG_GENRE.items():
            if any(n in key or key in n for n in names):
                entry["attrs"]["genero_musical"] = genre
                break

    for entry in pools.get("pratos_tipicos", []):
        region = _match(DISH_REGION, entry["name"])
        if region:
            entry["attrs"].setdefault("regiao", region)

    for entry in pools.get("frutas_nativas", []):
        biome = _match(FRUIT_BIOME, entry["name"])
        if biome:
            entry["attrs"].setdefault("bioma", biome)

    for pool in ("aves", "mamiferos"):
        for entry in pools.get(pool, []):
            biome = _match(ANIMAL_BIOME, entry["name"])
            if biome:
                entry["attrs"].setdefault("bioma", biome)


def aliases_for(entry: dict, pool: str) -> list[str]:
    out: list[str] = []
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
