"""The prompt bank: 100+ Brazilian questions, each bound to a data pool.

A prompt is only kept when its filtered pool has enough catalogued answers for a
rarity percentile to mean anything. Constraints are always checked against data
(region, year, population, letter), never against a hunch.
"""
from __future__ import annotations

from .http import normalize


def letter(chars: str):
    chars = chars.lower()
    def where(entry: dict) -> bool:
        return normalize(entry["name"])[:1] in chars
    return where


def attr_is(key: str, value):
    def where(entry: dict) -> bool:
        return entry["attrs"].get(key) == value
    return where


def attr_contains(key: str, value: str):
    def where(entry: dict) -> bool:
        raw = entry["attrs"].get(key) or ""
        items = raw if isinstance(raw, list) else [raw]
        return any(value.lower() in str(i).lower() for i in items)
    return where


def gravity_at_least(value: float):
    def where(entry: dict) -> bool:
        return (entry.get("gravity") or 0) >= value
    return where


def year_between(start: int, end: int):
    def where(entry: dict) -> bool:
        year = entry["attrs"].get("ano")
        return isinstance(year, int) and start <= year <= end
    return where


EXTRA_TEXT = {
    "jogador": "Cite um jogador da Seleção cujo nome começa com {L}",
    "cidade": "Cite uma cidade brasileira que começa com {L}",
    "time": "Cite um time de futebol que começa com {L}",
    "parque": "Cite um parque nacional que começa com {L}",
    "estadio": "Cite um estádio brasileiro que começa com {L}",
    "rio": "Cite um rio brasileiro que começa com {L}",
    "novelas": "Cite uma novela que começa com {L}",
    "cantores": "Cite um cantor brasileiro que começa com {L}",
    "escritores": "Cite um escritor brasileiro que começa com {L}",
    "atores": "Cite um ator brasileiro cujo nome começa com {L}",
    "marcas": "Cite uma marca brasileira que começa com {L}",
    "filmes": "Cite um filme brasileiro que começa com {L}",
    "pratos_tipicos": "Cite um prato brasileiro que começa com {L}",
    "frutas_nativas": "Cite uma fruta brasileira que começa com {L}",
    "doces": "Cite um doce brasileiro que começa com {L}",
    "aves": "Cite uma ave brasileira que começa com {L}",
    "mamiferos": "Cite um mamífero brasileiro que começa com {L}",
}


def build(pools: dict[str, list[dict]]) -> list[dict]:
    out: list[dict] = []

    def add(pid: str, text: str, pool: str, where=None, minimum: int = 12):
        items = pools.get(pool, [])
        selected = [a for a in items if where is None or where(a)]
        # Hard floor: under a dozen answers a percentile is too coarse to be fair.
        if len(selected) < max(minimum, 12):
            return
        out.append({"id": pid, "text": text, "cat": pool, "answers": selected})

    # ---- estados
    add("uf-todos", "Cite um estado do Brasil", "uf", minimum=20)
    add("uf-nordeste", "Cite um estado do Nordeste", "uf", attr_is("regiao", "Nordeste"), 6)
    add("uf-sul", "Cite um estado do Sul", "uf", attr_is("regiao", "Sul"), 3)
    add("uf-norte", "Cite um estado do Norte", "uf", attr_is("regiao", "Norte"), 5)
    add("uf-sudeste", "Cite um estado do Sudeste", "uf", attr_is("regiao", "Sudeste"), 4)
    add("uf-centro-oeste", "Cite um estado do Centro-Oeste", "uf",
        attr_is("regiao", "Centro-Oeste"), 4)
    add("uf-sem-litoral", "Cite um estado brasileiro sem litoral", "uf",
        attr_is("litoral", False), 6)
    add("uf-populoso", "Cite um estado com mais de 10 milhões de habitantes", "uf",
        gravity_at_least(10_000_000), 6)
    add("uf-p", "Cite um estado que começa com a letra P", "uf", letter("p"), 4)
    add("uf-s", "Cite um estado que começa com a letra S", "uf", letter("s"), 3)
    add("uf-r", "Cite um estado que começa com a letra R", "uf", letter("r"), 4)
    add("uf-m", "Cite um estado que começa com a letra M", "uf", letter("m"), 4)
    add("uf-a", "Cite um estado que começa com a letra A", "uf", letter("a"), 3)

    # ---- cidades
    add("cidade-todas", "Cite uma cidade brasileira", "cidade", minimum=60)
    add("cidade-milhao", "Cite uma cidade com mais de 1 milhão de habitantes", "cidade",
        gravity_at_least(1_000_000), 10)
    add("cidade-500mil", "Cite uma cidade com mais de 500 mil habitantes", "cidade",
        gravity_at_least(500_000), 20)
    for char in "bcsprmat":
        add(f"cidade-{char}", f"Cite uma cidade brasileira que começa com {char.upper()}",
            "cidade", letter(char), 8)

    # ---- presidentes
    add("presidente-todos", "Cite um presidente do Brasil", "presidente", minimum=20)
    add("presidente-pos1985", "Cite um presidente que governou depois de 1985",
        "presidente", lambda a: (a["attrs"].get("ano") or 0) >= 1985, 8)
    add("presidente-militar", "Cite um presidente da ditadura militar", "presidente",
        lambda a: 1964 <= (a["attrs"].get("ano") or 0) <= 1985, 4)
    add("presidente-j", "Cite um presidente cujo nome começa com J", "presidente",
        letter("j"), 5)

    # ---- jogadores
    add("jogador-todos", "Cite um jogador da Seleção Brasileira", "jogador", minimum=60)
    add("jogador-atacante", "Cite um atacante da Seleção Brasileira", "jogador",
        attr_contains("posicao", "atacante"), 10)
    add("jogador-goleiro", "Cite um goleiro da Seleção Brasileira", "jogador",
        attr_contains("posicao", "goleiro"), 8)
    add("jogador-meia", "Cite um meia da Seleção Brasileira", "jogador",
        attr_contains("posicao", "meia"), 8)
    add("jogador-zagueiro", "Cite um zagueiro da Seleção Brasileira", "jogador",
        attr_contains("posicao", "zagueiro"), 8)
    add("jogador-r", "Cite um jogador da Seleção cujo nome começa com R", "jogador",
        letter("r"), 8)
    add("jogador-m", "Cite um jogador da Seleção cujo nome começa com M", "jogador",
        letter("m"), 6)

    # ---- times
    add("time-todos", "Cite um time de futebol brasileiro", "time", minimum=40)
    add("time-campeao", "Cite um time que já foi campeão brasileiro", "time",
        lambda a: bool(a["attrs"].get("campeao_brasileiro")), 10)
    add("time-f", "Cite um time de futebol que começa com F", "time", letter("f"), 4)
    add("time-c", "Cite um time de futebol que começa com C", "time", letter("c"), 5)
    add("time-s", "Cite um time de futebol que começa com S", "time", letter("s"), 6)

    # ---- rios
    add("rio-todos", "Cite um rio brasileiro", "rio", minimum=40)
    add("rio-s", "Cite um rio brasileiro que começa com S", "rio", letter("s"), 6)
    add("rio-p", "Cite um rio brasileiro que começa com P", "rio", letter("p"), 6)
    add("rio-i", "Cite um rio brasileiro que começa com I", "rio", letter("i"), 5)
    add("rio-a", "Cite um rio brasileiro que começa com A", "rio", letter("a"), 4)

    # ---- parques
    add("parque-todos", "Cite um parque nacional brasileiro", "parque", minimum=25)
    add("parque-s", "Cite um parque nacional que começa com S", "parque", letter("s"), 5)
    add("parque-c", "Cite um parque nacional que começa com C", "parque", letter("c"), 4)
    add("parque-i", "Cite um parque nacional que começa com I", "parque", letter("i"), 4)

    # ---- estádios
    add("estadio-todos", "Cite um estádio de futebol no Brasil", "estadio", minimum=25)
    add("estadio-m", "Cite um estádio brasileiro que começa com M", "estadio",
        letter("m"), 4)

    # ---- frutas
    add("fruta-todas", "Cite uma fruta nativa do Brasil", "frutas_nativas", minimum=30)
    add("fruta-a", "Cite uma fruta brasileira que começa com A", "frutas_nativas",
        letter("a"), 8)
    add("fruta-c", "Cite uma fruta brasileira que começa com C", "frutas_nativas",
        letter("c"), 6)
    add("fruta-m", "Cite uma fruta brasileira que começa com M", "frutas_nativas",
        letter("m"), 5)
    add("fruta-amazonia", "Cite uma fruta da Amazônia", "frutas_nativas",
        attr_is("bioma", "Amazônia"), 8)
    add("fruta-cerrado", "Cite uma fruta do Cerrado", "frutas_nativas",
        attr_is("bioma", "Cerrado"), 6)
    add("fruta-mata", "Cite uma fruta da Mata Atlântica", "frutas_nativas",
        attr_is("bioma", "Mata Atlântica"), 6)

    # ---- pratos
    add("prato-todos", "Cite um prato típico brasileiro", "pratos_tipicos", minimum=40)
    add("prato-bahia", "Cite um prato típico da Bahia", "pratos_tipicos",
        attr_is("regiao", "Bahia"), 6)
    add("prato-minas", "Cite um prato típico de Minas Gerais", "pratos_tipicos",
        attr_is("regiao", "Minas Gerais"), 6)
    add("prato-nordeste", "Cite um prato típico do Nordeste", "pratos_tipicos",
        attr_is("regiao", "Nordeste"), 6)
    add("prato-sul", "Cite um prato típico do Sul", "pratos_tipicos",
        attr_is("regiao", "Sul"), 5)
    add("prato-norte", "Cite um prato típico do Norte", "pratos_tipicos",
        attr_is("regiao", "Norte"), 5)
    add("prato-f", "Cite um prato brasileiro que começa com F", "pratos_tipicos",
        letter("f"), 4)
    add("prato-m", "Cite um prato brasileiro que começa com M", "pratos_tipicos",
        letter("m"), 4)

    # ---- doces
    add("doce-todos", "Cite um doce brasileiro", "doces", minimum=25)
    add("doce-b", "Cite um doce brasileiro que começa com B", "doces", letter("b"), 4)
    add("doce-c", "Cite um doce brasileiro que começa com C", "doces", letter("c"), 6)
    add("doce-p", "Cite um doce brasileiro que começa com P", "doces", letter("p"), 4)

    # ---- novelas
    add("novela-todas", "Cite uma novela da Globo", "novelas", minimum=50)
    add("novela-90", "Cite uma novela dos anos 1990", "novelas",
        year_between(1990, 1999), 8)
    add("novela-2000", "Cite uma novela dos anos 2000", "novelas",
        year_between(2000, 2009), 8)
    add("novela-2010", "Cite uma novela dos anos 2010", "novelas",
        year_between(2010, 2019), 8)
    add("novela-2020", "Cite uma novela de 2020 para cá", "novelas",
        year_between(2020, 2030), 5)
    add("novela-a", "Cite uma novela que começa com A", "novelas", letter("a"), 6)
    add("novela-t", "Cite uma novela que começa com T", "novelas", letter("t"), 4)

    # ---- filmes
    add("filme-todos", "Cite um filme brasileiro", "filmes", minimum=40)
    add("filme-2000", "Cite um filme brasileiro dos anos 2000", "filmes",
        year_between(2000, 2009), 6)
    add("filme-2010", "Cite um filme brasileiro dos anos 2010", "filmes",
        year_between(2010, 2019), 6)
    add("filme-c", "Cite um filme brasileiro que começa com C", "filmes", letter("c"), 6)
    add("filme-t", "Cite um filme brasileiro que começa com T", "filmes", letter("t"), 4)

    # ---- cantores
    add("cantor-todos", "Cite um cantor brasileiro", "cantores", minimum=50)
    add("cantora", "Cite uma cantora brasileira", "cantores",
        attr_is("genero", "feminino"), 15)
    add("cantor-mpb", "Cite um cantor de MPB", "cantores",
        attr_is("genero_musical", "mpb"), 8)
    add("cantor-sertanejo", "Cite um cantor de sertanejo", "cantores",
        attr_is("genero_musical", "sertanejo"), 6)
    add("cantor-rock", "Cite um cantor ou cantora de rock brasileiro", "cantores",
        attr_is("genero_musical", "rock"), 6)
    add("cantor-c", "Cite um cantor brasileiro que começa com C", "cantores",
        letter("c"), 6)
    add("cantor-j", "Cite um cantor brasileiro que começa com J", "cantores",
        letter("j"), 5)

    # ---- escritores
    add("escritor-todos", "Cite um escritor brasileiro", "escritores", minimum=40)
    add("escritora", "Cite uma escritora brasileira", "escritores",
        attr_is("genero", "feminino"), 8)
    add("escritor-m", "Cite um escritor brasileiro que começa com M", "escritores",
        letter("m"), 6)
    add("escritor-j", "Cite um escritor brasileiro que começa com J", "escritores",
        letter("j"), 4)

    # ---- atores
    add("ator-todos", "Cite um ator ou atriz brasileira", "atores", minimum=40)
    add("atriz", "Cite uma atriz brasileira", "atores",
        attr_is("genero", "feminino"), 20)
    add("ator-f", "Cite um ator brasileiro cujo nome começa com F", "atores",
        letter("f"), 5)
    add("ator-m", "Cite um ator brasileiro cujo nome começa com M", "atores",
        letter("m"), 5)

    # ---- marcas
    add("marca-todas", "Cite uma marca brasileira", "marcas", minimum=30)
    add("marca-n", "Cite uma marca brasileira que começa com N", "marcas", letter("n"), 4)
    add("marca-c", "Cite uma marca brasileira que começa com C", "marcas", letter("c"), 6)

    # ---- aves
    add("ave-todas", "Cite uma ave brasileira", "aves", minimum=30)
    add("ave-a", "Cite uma ave brasileira que começa com A", "aves", letter("a"), 6)
    add("ave-t", "Cite uma ave brasileira que começa com T", "aves", letter("t"), 5)
    add("ave-p", "Cite uma ave brasileira que começa com P", "aves", letter("p"), 5)

    # ---- mamíferos
    add("mamifero-todos", "Cite um mamífero brasileiro", "mamiferos", minimum=25)
    add("mamifero-c", "Cite um mamífero brasileiro que começa com C", "mamiferos",
        letter("c"), 5)
    add("mamifero-m", "Cite um mamífero brasileiro que começa com M", "mamiferos",
        letter("m"), 4)

    # ---- folclore
    add("folclore-todos", "Cite uma criatura do folclore brasileiro", "folclore",
        minimum=25)
    add("folclore-c", "Cite uma criatura do folclore que começa com C", "folclore",
        letter("c"), 4)
    add("folclore-b", "Cite uma criatura do folclore que começa com B", "folclore",
        letter("b"), 4)

    # ---- festas
    add("festa-todas", "Cite uma festa popular brasileira", "festas", minimum=25)
    add("festa-f", "Cite uma festa popular brasileira que começa com F", "festas",
        letter("f"), 4)
    add("festa-c", "Cite uma festa popular brasileira que começa com C", "festas",
        letter("c"), 5)

    # ---- danças
    add("danca-todas", "Cite uma dança brasileira", "dancas", minimum=20)
    add("danca-c", "Cite uma dança brasileira que começa com C", "dancas", letter("c"), 4)
    add("danca-f", "Cite uma dança brasileira que começa com F", "dancas", letter("f"), 3)

    # ---- instrumentos
    add("instrumento-todos", "Cite um instrumento musical brasileiro", "instrumentos",
        minimum=15)
    add("instrumento-p", "Cite um instrumento de percussão brasileiro", "instrumentos",
        attr_is("tipo", "percussão"), 8)

    # ---- palavras de origem indígena
    add("tupi-todas", "Cite uma palavra de origem indígena que usamos no português",
        "palavras_tupi", minimum=30)
    add("tupi-m", "Cite uma palavra de origem indígena que começa com M",
        "palavras_tupi", letter("m"), 5)
    add("tupi-p", "Cite uma palavra de origem indígena que começa com P",
        "palavras_tupi", letter("p"), 5)
    add("tupi-j", "Cite uma palavra de origem indígena que começa com J",
        "palavras_tupi", letter("j"), 4)

    # ---- gírias
    add("giria-todas", "Cite uma gíria brasileira", "girias", minimum=20)

    # ---- BBB
    add("bbb-todos", "Cite um participante do Big Brother Brasil", "bbb", minimum=40)
    add("bbb-campeao", "Cite um campeão do Big Brother Brasil", "bbb_campeoes", minimum=12)
    add("bbb-b", "Cite um participante do BBB cujo nome começa com B", "bbb", letter("b"), 5)
    add("bbb-j", "Cite um participante do BBB cujo nome começa com J", "bbb", letter("j"), 5)

    # ---- TV Globinho e desenhos
    add("globinho-todos", "Cite um desenho que passou na TV Globinho", "tv_globinho",
        minimum=20)
    add("globinho-d", "Cite um desenho da TV Globinho que começa com D", "tv_globinho",
        letter("d"), 4)
    add("desenho-todos", "Cite um desenho animado que marcou a sua infância",
        "desenhos", minimum=30)
    add("desenho-a", "Cite um desenho animado que começa com A", "desenhos", letter("a"), 6)
    add("desenho-b", "Cite um desenho animado que começa com B", "desenhos", letter("b"), 6)
    add("desenho-d", "Cite um desenho animado que começa com D", "desenhos", letter("d"), 5)

    # ---- bebidas
    add("bebida-todas", "Cite uma bebida brasileira", "bebidas", minimum=12)
    add("bebida-c", "Cite uma bebida brasileira que começa com C", "bebidas",
        letter("c"), 4)

    # ---- novelas por faixa (tag da lista da Globo)
    add("novela-nove", "Cite uma novela das nove", "novelas", attr_is("faixa", "nove"), 8)
    add("novela-oito", "Cite uma novela das oito", "novelas", attr_is("faixa", "oito"), 8)
    add("novela-seis", "Cite uma novela das seis", "novelas", attr_is("faixa", "seis"), 6)

    # ---- letras, por pool: a constraint the data can actually prove
    extra_letters = {
        "jogador": ("a", "d", "f", "g", "l", "s", "t", "v"),
        "cidade": ("j", "g", "v", "n", "l", "e", "f"),
        "time": ("a", "g", "p", "v", "b", "i"),
        "parque": ("a", "b", "j", "p", "t", "e"),
        "estadio": ("a", "j", "c", "s", "m", "p"),
        "rio": ("j", "m", "t", "u", "i", "a", "g", "c"),
        "novelas": ("o", "c", "p", "s", "v", "e", "l"),
        "cantores": ("g", "l", "r", "t", "a", "b", "d", "m"),
        "escritores": ("c", "r", "a", "p", "g", "l", "s", "v"),
        "atores": ("c", "j", "l", "t", "a", "g", "m", "r", "s"),
        "marcas": ("b", "p", "a", "c", "d", "g", "i", "l", "m", "r", "s", "t", "v"),
        "filmes": ("a", "o", "p", "s", "c", "d", "e", "m", "r", "t"),
        "pratos_tipicos": ("b", "c", "p", "t", "a", "e", "g", "m", "s"),
        "frutas_nativas": ("j", "p", "g", "u", "b", "c", "m", "s", "t"),
        "doces": ("m", "t", "a", "b", "c", "p", "q", "s"),
        "aves": ("c", "g", "j", "s", "a", "b", "p", "t"),
        "mamiferos": ("a", "l", "c", "g", "j", "p", "s", "t"),
    }
    for pool, letters in extra_letters.items():
        for char in letters:
            add(f"{pool}-l{char}",
                EXTRA_TEXT[pool].format(L=char.upper()),
                pool, letter(char), 4)

    # ---- internacionais
    add("pais-todos", "Cite um país do mundo", "pais", minimum=120)
    add("pais-europa", "Cite um país da Europa", "pais", attr_contains("continente", "Europa"), 20)
    add("pais-africa", "Cite um país da África", "pais", attr_contains("continente", "África"), 20)
    add("pais-asia", "Cite um país da Ásia", "pais", attr_contains("continente", "Ásia"), 20)
    add("pais-america-sul", "Cite um país da América do Sul", "pais",
        attr_contains("continente", "América do Sul"), 8)
    add("pais-america-norte", "Cite um país da América do Norte", "pais",
        attr_contains("continente", "América do Norte"), 8)
    add("pais-a", "Cite um país que começa com A", "pais", letter("a"), 6)
    add("pais-b", "Cite um país que começa com B", "pais", letter("b"), 6)
    add("pais-m", "Cite um país que começa com M", "pais", letter("m"), 6)

    add("capital-todas", "Cite uma capital do mundo", "capital_mundo", minimum=80)
    add("capital-europa", "Cite uma capital da Europa", "capital_mundo",
        attr_contains("continente", "Europa"), 15)
    add("capital-asia", "Cite uma capital da Ásia", "capital_mundo",
        attr_contains("continente", "Ásia"), 15)
    add("capital-africa", "Cite uma capital da África", "capital_mundo",
        attr_contains("continente", "África"), 15)
    add("capital-america", "Cite uma capital da América", "capital_mundo",
        attr_contains("continente", "América"), 12)
    add("capital-a", "Cite uma capital que começa com A", "capital_mundo", letter("a"), 5)
    add("capital-b", "Cite uma capital que começa com B", "capital_mundo", letter("b"), 5)
    add("capital-c", "Cite uma capital que começa com C", "capital_mundo", letter("c"), 5)
    add("capital-m", "Cite uma capital que começa com M", "capital_mundo", letter("m"), 5)

    add("pokemon-todos", "Cite um Pokémon", "pokemon", minimum=60)
    add("pokemon-p", "Cite um Pokémon que começa com P", "pokemon", letter("p"), 6)
    add("pokemon-c", "Cite um Pokémon que começa com C", "pokemon", letter("c"), 4)
    add("pokemon-m", "Cite um Pokémon que começa com M", "pokemon", letter("m"), 6)
    add("pokemon-g", "Cite um Pokémon que começa com G", "pokemon", letter("g"), 4)

    add("elemento-todos", "Cite um elemento químico", "elemento", minimum=60)
    add("elemento-c", "Cite um elemento químico que começa com C", "elemento", letter("c"), 5)
    add("elemento-h", "Cite um elemento químico que começa com H", "elemento", letter("h"), 3)
    add("elemento-o", "Cite um elemento químico que começa com O", "elemento", letter("o"), 3)
    add("elemento-s", "Cite um elemento químico que começa com S", "elemento", letter("s"), 6)

    add("videogame-todos", "Cite um videogame", "videogame", minimum=60)
    add("videogame-a", "Cite um videogame que começa com A", "videogame", letter("a"), 4)
    add("videogame-c", "Cite um videogame que começa com C", "videogame", letter("c"), 4)
    add("videogame-g", "Cite um videogame que começa com G", "videogame", letter("g"), 4)
    add("videogame-m", "Cite um videogame que começa com M", "videogame", letter("m"), 4)

    add("anime-todos", "Cite um anime", "anime", minimum=50)
    add("anime-d", "Cite um anime que começa com D", "anime", letter("d"), 4)
    add("anime-n", "Cite um anime que começa com N", "anime", letter("n"), 4)
    add("anime-s", "Cite um anime que começa com S", "anime", letter("s"), 5)

    add("banda-todos", "Cite uma banda internacional", "banda", minimum=50)
    add("banda-a", "Cite uma banda que começa com A", "banda", letter("a"), 4)
    add("banda-b", "Cite uma banda que começa com B", "banda", letter("b"), 4)
    add("banda-c", "Cite uma banda que começa com C", "banda", letter("c"), 3)
    add("banda-m", "Cite uma banda que começa com M", "banda", letter("m"), 4)

    add("cidade-mundo-todas", "Cite uma cidade do mundo", "cidade_mundo", minimum=100)
    add("cidade-mundo-b", "Cite uma cidade do mundo que começa com B", "cidade_mundo",
        letter("b"), 6)
    add("cidade-mundo-c", "Cite uma cidade do mundo que começa com C", "cidade_mundo",
        letter("c"), 6)
    add("cidade-mundo-l", "Cite uma cidade do mundo que começa com L", "cidade_mundo",
        letter("l"), 6)
    add("cidade-mundo-m", "Cite uma cidade do mundo que começa com M", "cidade_mundo",
        letter("m"), 6)
    add("cidade-mundo-p", "Cite uma cidade do mundo que começa com P", "cidade_mundo",
        letter("p"), 6)

    add("heroi-todos", "Cite um super-herói", "heroi", minimum=40)
    add("heroi-b", "Cite um super-herói que começa com B", "heroi", letter("b"), 4)
    add("heroi-c", "Cite um super-herói que começa com C", "heroi", letter("c"), 3)
    add("heroi-h", "Cite um super-herói que começa com H", "heroi", letter("h"), 4)
    add("heroi-m", "Cite um super-herói que começa com M", "heroi", letter("m"), 3)

    add("comida-mundo-todos", "Cite um prato internacional", "comida_mundo", minimum=30)
    add("comida-mundo-c", "Cite um prato internacional que começa com C", "comida_mundo",
        letter("c"), 3)
    add("comida-mundo-p", "Cite um prato internacional que começa com P", "comida_mundo",
        letter("p"), 4)
    add("comida-mundo-s", "Cite um prato internacional que começa com S", "comida_mundo",
        letter("s"), 3)

    add("marca-global-todas", "Cite uma marca global", "marca_global", minimum=30)
    add("marca-global-a", "Cite uma marca global que começa com A", "marca_global",
        letter("a"), 3)
    add("marca-global-c", "Cite uma marca global que começa com C", "marca_global",
        letter("c"), 3)
    add("marca-global-g", "Cite uma marca global que começa com G", "marca_global",
        letter("g"), 3)
    add("marca-global-m", "Cite uma marca global que começa com M", "marca_global",
        letter("m"), 4)

    # ---- top up with further constraints the data can prove
    texts = {p["text"] for p in out}
    for pool, template in EXTRA_TEXT.items():
        added = 0
        for char in "abcdefghijklmnopqrstuvwxyz":
            if added >= 4:
                break
            text = template.format(L=char.upper())
            if text in texts:
                continue
            items = [a for a in pools.get(pool, []) if letter(char)(a)]
            if len(items) < 12:
                continue
            out.append({"id": f"{pool}-g{char}", "text": text, "cat": pool,
                        "answers": items})
            texts.add(text)
            added += 1

    return out
