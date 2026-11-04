"""The prompt bank (acervo v2): ~200 Brazilian / lusophone questions, each bound
to a data pool and a constraint the data can prove (tag, letter, year, size).

Rules:
  * every prompt text is unique;
  * a prompt needs at least 12 answers (a percentile needs room);
  * a letter prompt needs at least 30 answers, or it is dropped.
"""
from __future__ import annotations

from .http import normalize

LETTER_MIN = 30
FLOOR = 12


def letter(chars: str):
    chars = chars.lower()

    def where(entry: dict) -> bool:
        return normalize(entry["name"])[:1] in chars
    return where


def has(key: str, *values):
    wanted = set(values)

    def where(entry: dict) -> bool:
        raw = entry["attrs"].get(key)
        items = raw if isinstance(raw, list) else [raw]
        return any(v in wanted for v in items)
    return where


def gravity_at_least(value: float):
    def where(entry: dict) -> bool:
        return (entry.get("gravity") or 0) >= value
    return where


def year_between(start: int, end: int):
    def where(entry: dict) -> bool:
        values = []
        for k in ("ano", "decada"):
            raw = entry["attrs"].get(k)
            values += raw if isinstance(raw, list) else [raw]
        return any(isinstance(y, int) and start <= y <= end for y in values)
    return where


def both(*preds):
    def where(entry: dict) -> bool:
        return all(p(entry) for p in preds)
    return where


def build(pools: dict[str, list[dict]]) -> list[dict]:
    out: list[dict] = []
    texts: set[str] = set()
    dropped: list[tuple[str, int]] = []

    def add(pid: str, text: str, pool: str, where=None, *, is_letter: bool = False,
            cat: str | None = None):
        items = pools.get(pool, [])
        selected = [a for a in items if where is None or where(a)]
        need = LETTER_MIN if is_letter else FLOOR
        if len(selected) < need or text in texts:
            dropped.append((pid, len(selected)))
            return
        texts.add(text)
        out.append({"id": pid, "text": text, "cat": cat or pool, "answers": selected})

    def letters(pool: str, template: str, chars: str, prefix: str):
        for char in chars:
            add(f"{prefix}-l{char}", template.format(L=char.upper()), pool, letter(char),
                is_letter=True)

    # ---- estados e cidades
    add("uf-todos", "Cite um estado do Brasil", "uf")
    add("uf-litoral", "Cite um estado brasileiro com litoral", "uf", has("litoral", True))
    add("capital-br", "Cite uma capital de estado brasileiro", "cidade", has("capital", True))
    add("cidade-todas", "Cite uma cidade brasileira", "cidade")
    add("cidade-500mil", "Cite uma cidade brasileira com mais de 500 mil habitantes", "cidade",
        gravity_at_least(500_000))
    for uf, text in (("SP", "Cite uma cidade do estado de São Paulo"),
                     ("MG", "Cite uma cidade de Minas Gerais"),
                     ("RJ", "Cite uma cidade do estado do Rio de Janeiro"),
                     ("RS", "Cite uma cidade do Rio Grande do Sul"),
                     ("PR", "Cite uma cidade do Paraná"),
                     ("SC", "Cite uma cidade de Santa Catarina"),
                     ("BA", "Cite uma cidade da Bahia")):
        add(f"cidade-{uf.lower()}", text, "cidade", has("uf", uf))
    add("cidade-nordeste", "Cite uma cidade do Nordeste", "cidade", has("regiao", "Nordeste"))
    add("cidade-norte", "Cite uma cidade da Região Norte", "cidade", has("regiao", "Norte"))
    add("cidade-co", "Cite uma cidade do Centro-Oeste", "cidade", has("regiao", "Centro-Oeste"))
    letters("cidade", "Cite uma cidade brasileira que começa com {L}", "abcmpsrjt", "cidade")
    add("cidade-historica", "Cite uma cidade histórica brasileira", "cidades_historicas")

    # ---- política, ciência
    add("presidente-todos", "Cite um presidente do Brasil", "presidente")
    add("cientista", "Cite um cientista ou inventor brasileiro", "cientista")

    # ---- futebol
    add("jogador-todos", "Cite um jogador da Seleção Brasileira", "jogador")
    add("jogador-atacante", "Cite um atacante da Seleção Brasileira", "jogador", has("posicao", "atacante"))
    add("jogador-goleiro", "Cite um goleiro da Seleção Brasileira", "jogador", has("posicao", "goleiro"))
    add("jogador-zagueiro", "Cite um zagueiro da Seleção Brasileira", "jogador", has("posicao", "zagueiro"))
    add("jogador-meia", "Cite um meio-campista da Seleção Brasileira", "jogador", has("posicao", "meia"))
    add("jogador-lateral", "Cite um lateral da Seleção Brasileira", "jogador", has("posicao", "lateral"))
    letters("jogador", "Cite um jogador da Seleção cujo nome começa com {L}", "rmagdf", "jogador")
    add("jogadora-todas", "Cite uma jogadora da Seleção Brasileira feminina", "jogadora")
    add("time-todos", "Cite um time de futebol brasileiro", "time")
    add("time-campeao", "Cite um time que já foi campeão brasileiro", "time", has("campeao", "sim"))
    add("time-sp", "Cite um time de futebol paulista", "time", has("uf", "SP"))
    add("time-rj", "Cite um time de futebol carioca ou fluminense", "time", has("uf", "RJ"))
    add("time-mg", "Cite um time de futebol mineiro", "time", has("uf", "MG"))
    add("time-sul", "Cite um time de futebol do Sul do Brasil", "time", has("uf", "RS", "PR", "SC"))
    add("time-nordeste", "Cite um time de futebol do Nordeste", "time",
        has("uf", "BA", "PE", "CE", "RN", "PB", "AL", "SE", "MA", "PI"))
    letters("time", "Cite um time de futebol brasileiro que começa com {L}", "acs", "time")
    add("time-pt", "Cite um clube de futebol de Portugal", "time_pt")
    add("jogador-pt", "Cite um jogador da seleção de Portugal", "jogador_pt")
    add("estadio-todos", "Cite um estádio de futebol no Brasil", "estadio")
    add("volei-todos", "Cite um jogador ou jogadora de vôlei do Brasil", "volei")
    add("f1-br", "Cite um piloto brasileiro de Fórmula 1", "f1")
    add("medalhista", "Cite um medalhista olímpico brasileiro", "medalhista")

    # ---- natureza
    add("rio-todos", "Cite um rio brasileiro", "rio")
    letters("rio", "Cite um rio brasileiro que começa com {L}", "pas", "rio")
    add("parque-todos", "Cite um parque nacional brasileiro", "parque")
    add("fruta-todas", "Cite uma fruta nativa do Brasil", "frutas_nativas")
    add("fruta-amazonia", "Cite uma fruta da Amazônia", "frutas_nativas", has("bioma", "Amazônia"))
    add("fruta-cerrado", "Cite uma fruta do Cerrado", "frutas_nativas", has("bioma", "Cerrado"))
    add("fruta-mata", "Cite uma fruta da Mata Atlântica", "frutas_nativas", has("bioma", "Mata Atlântica"))
    add("fruta-caatinga", "Cite uma fruta da Caatinga", "frutas_nativas", has("bioma", "Caatinga"))
    letters("frutas_nativas", "Cite uma fruta nativa do Brasil que começa com {L}", "cpabmg", "fruta")
    add("ave-todas", "Cite uma ave brasileira", "aves")
    letters("aves", "Cite uma ave brasileira que começa com {L}", "abcgjpst", "ave")
    add("mamifero-todos", "Cite um mamífero da fauna brasileira", "mamiferos")
    letters("mamiferos", "Cite um mamífero da fauna brasileira que começa com {L}", "cmp", "mamifero")

    # ---- comida e bebida
    add("prato-todos", "Cite um prato típico brasileiro", "pratos_tipicos")
    for region, pid, text in (("Nordeste", "prato-nordeste", "Cite um prato típico do Nordeste"),
                              ("Bahia", "prato-bahia", "Cite um prato típico da Bahia"),
                              ("Minas Gerais", "prato-minas", "Cite um prato típico de Minas Gerais"),
                              ("Sul", "prato-sul", "Cite um prato típico do Sul"),
                              ("Norte", "prato-norte", "Cite um prato típico do Norte"),
                              ("Sudeste", "prato-sudeste", "Cite um prato típico do Sudeste"),
                              ("Centro-Oeste", "prato-co", "Cite um prato típico do Centro-Oeste")):
        add(pid, text, "pratos_tipicos", has("regiao", region))
    letters("pratos_tipicos", "Cite um prato brasileiro que começa com {L}", "cbpmf", "prato")
    add("doce-todos", "Cite um doce brasileiro", "doces")
    letters("doces", "Cite um doce brasileiro que começa com {L}", "bcpm", "doce")
    add("salgado-festa", "Cite um salgadinho de festa", "salgados", has("tipo", "festa"))
    add("petisco-boteco", "Cite um petisco de boteco", "salgados", has("tipo", "boteco"))
    add("bebida-todas", "Cite uma bebida brasileira", "bebidas")
    add("refrigerante-br", "Cite um refrigerante de marca brasileira", "bebidas",
        has("tipo", "refrigerante"))
    add("cerveja-br", "Cite uma marca de cerveja brasileira", "cervejas")
    add("prato-pt", "Cite um prato ou doce típico de Portugal", "prato_pt")

    # ---- novelas, cinema, TV
    add("novela-globo", "Cite uma novela da Globo", "novelas", has("emissora", "Globo"))
    add("novela-todas", "Cite uma novela brasileira", "novelas")
    for start, pid, text in ((1970, "novela-70", "Cite uma novela dos anos 1970"),
                             (1980, "novela-80", "Cite uma novela dos anos 1980"),
                             (1990, "novela-90", "Cite uma novela dos anos 1990"),
                             (2000, "novela-2000", "Cite uma novela dos anos 2000"),
                             (2010, "novela-2010", "Cite uma novela dos anos 2010"),
                             (2020, "novela-2020", "Cite uma novela de 2020 para cá")):
        add(pid, text, "novelas", year_between(start, start + 9))
    add("novela-seis", "Cite uma novela das seis da Globo", "novelas", has("faixa", "seis"))
    add("novela-sete", "Cite uma novela das sete da Globo", "novelas", has("faixa", "sete"))
    add("novela-nove", "Cite uma novela das oito ou das nove da Globo", "novelas",
        has("faixa", "oito", "nove"))
    add("novela-sbt", "Cite uma novela produzida pelo SBT", "novelas",
        both(has("emissora", "SBT"), lambda e: not e["attrs"].get("estrangeira")))
    add("novela-record", "Cite uma novela da Record", "novelas", has("emissora", "Record"))
    letters("novelas", "Cite uma novela brasileira que começa com {L}", "aot", "novela")
    add("personagem-novela", "Cite um personagem marcante de novela", "personagens_novela")
    add("filme-todos", "Cite um filme brasileiro", "filmes")
    add("filme-90", "Cite um filme brasileiro dos anos 1990", "filmes", year_between(1990, 1999))
    add("filme-2000", "Cite um filme brasileiro dos anos 2000", "filmes", year_between(2000, 2009))
    add("filme-2010", "Cite um filme brasileiro dos anos 2010", "filmes", year_between(2010, 2019))
    letters("filmes", "Cite um filme brasileiro que começa com {L}", "oac", "filme")
    add("programa-tv", "Cite um programa da TV brasileira", "programas_tv")
    add("apresentador", "Cite um apresentador ou apresentadora de TV brasileiro", "apresentador")
    add("humorista", "Cite um humorista brasileiro", "humorista")
    add("youtuber", "Cite um youtuber ou influenciador brasileiro", "youtuber")
    add("bbb-todos", "Cite um participante do Big Brother Brasil", "bbb")
    add("bbb-campeao", "Cite um campeão do Big Brother Brasil", "bbb_campeoes")
    add("globinho-todos", "Cite um desenho que passou na TV Globinho", "tv_globinho")
    add("desenho-todos", "Cite um desenho animado que marcou a sua infância", "desenhos")
    letters("desenhos", "Cite um desenho animado que começa com {L}", "abp", "desenho")
    add("turma-monica", "Cite um personagem da Turma da Mônica", "turma_monica")

    # ---- música
    add("cantor-todos", "Cite um cantor ou cantora brasileira", "cantores")
    add("cantora", "Cite uma cantora brasileira", "cantores", has("genero", "feminino"))
    add("cantor-masc", "Cite um cantor brasileiro (homem)", "cantores", has("genero", "masculino"))
    for genre, pid, text in (("mpb", "cantor-mpb", "Cite um cantor ou cantora de MPB"),
                             ("sertanejo", "cantor-sertanejo", "Cite um cantor, cantora ou dupla sertaneja"),
                             ("funk", "cantor-funk", "Cite um MC ou cantor de funk"),
                             ("forro", "cantor-forro", "Cite um artista de forró"),
                             ("samba", "cantor-samba", "Cite um artista de samba ou pagode"),
                             ("axe", "cantor-axe", "Cite um artista de axé"),
                             ("rap", "cantor-rap", "Cite um rapper ou grupo de rap brasileiro"),
                             ("gospel", "cantor-gospel", "Cite um cantor ou cantora gospel brasileira"),
                             ("rock", "cantor-rock", "Cite um nome do rock brasileiro")):
        add(pid, text, "cantores", has("genero_musical", genre))
    add("dupla-sertaneja", "Cite uma dupla sertaneja", "cantores",
        both(has("dupla", True), has("genero_musical", "sertanejo")))
    letters("cantores", "Cite um cantor ou cantora brasileira que começa com {L}", "abcdgjlmrt", "cantor")
    add("banda-br", "Cite uma banda ou grupo musical brasileiro", "bandas")
    add("banda-rock", "Cite uma banda de rock brasileira", "bandas", has("genero_musical", "rock"))
    add("cantor-pt", "Cite um cantor, cantora ou banda de Portugal", "cantor_pt")

    # ---- letras
    add("escritor-todos", "Cite um escritor ou escritora brasileira", "escritores")
    add("escritora", "Cite uma escritora brasileira", "escritores", has("genero", "feminino"))
    letters("escritores", "Cite um escritor brasileiro cujo nome começa com {L}", "cmjaglr", "escritor")
    add("escritor-pt", "Cite um escritor ou poeta português", "escritor_pt")

    # ---- atores
    add("ator-todos", "Cite um ator ou atriz brasileira", "atores")
    add("atriz", "Cite uma atriz brasileira", "atores", has("genero", "feminino"))
    add("ator-masc", "Cite um ator brasileiro (homem)", "atores", has("genero", "masculino"))
    letters("atores", "Cite um ator ou atriz brasileira cujo nome começa com {L}", "mcfrjlast", "ator")

    # ---- marcas
    add("marca-todas", "Cite uma marca brasileira", "marcas")
    add("banco-br", "Cite um banco brasileiro", "marcas", has("setor", "banco"))
    add("marca-moda", "Cite uma marca brasileira de roupa ou calçado", "marcas", has("setor", "moda"))
    letters("marcas", "Cite uma marca brasileira que começa com {L}", "bcpsmatd", "marca")

    # ---- cultura popular
    add("folclore-todos", "Cite uma criatura ou lenda do folclore brasileiro", "folclore")
    add("festa-todas", "Cite uma festa popular brasileira", "festas")
    add("danca-todas", "Cite uma dança ou ritmo brasileiro", "dancas")
    add("instrumento-todos", "Cite um instrumento musical brasileiro", "instrumentos")
    add("instrumento-perc", "Cite um instrumento de percussão brasileiro", "instrumentos",
        has("tipo", "percussão"))
    add("escola-samba", "Cite uma escola de samba", "escola_samba")
    add("tupi-todas", "Cite uma palavra de origem indígena que usamos no português", "palavras_tupi")
    letters("palavras_tupi", "Cite uma palavra de origem tupi que começa com {L}", "pcmaij", "tupi")
    add("giria-todas", "Cite uma gíria brasileira", "girias")
    add("giria-nordeste", "Cite uma gíria ou expressão nordestina", "girias", has("regiao", "Nordeste"))
    add("giria-sul", "Cite uma gíria ou expressão gaúcha", "girias", has("regiao", "Sul"))
    add("giria-rio", "Cite uma gíria carioca", "girias", has("regiao", "Rio"))
    add("giria-minas", "Cite uma expressão mineira", "girias", has("regiao", "Minas"))
    add("palavra-pt", "Cite uma palavra que em Portugal é diferente do Brasil (ex.: autocarro)",
        "palavras_pt")

    # ---- lugares
    add("praia-todas", "Cite uma praia brasileira", "praias")
    add("ponto-turistico", "Cite um ponto turístico do Brasil", "pontos_turisticos")
    add("bairro-rio", "Cite um bairro da cidade do Rio de Janeiro", "bairro_rio")
    add("bairro-sp", "Cite um bairro da cidade de São Paulo", "bairro_sp")
    add("cidade-pt", "Cite uma cidade de Portugal", "cidade_pt")

    # ---- mundo
    add("pais-todos", "Cite um país do mundo", "pais")
    add("pais-lusofono", "Cite um país onde se fala português", "pais", has("lusofono", True))
    for cont, pid, text in (("Europa", "pais-europa", "Cite um país da Europa"),
                            ("África", "pais-africa", "Cite um país da África"),
                            ("Ásia", "pais-asia", "Cite um país da Ásia"),
                            ("América do Sul", "pais-america-sul", "Cite um país da América do Sul")):
        add(pid, text, "pais", lambda e, c=cont: c in str(e["attrs"].get("continente") or ""))
    letters("pais", "Cite um país que começa com {L}", "abcegimst", "pais")
    add("capital-todas", "Cite uma capital de país", "capital_mundo")
    for cont, pid, text in (("Europa", "capital-europa", "Cite uma capital da Europa"),
                            ("África", "capital-africa", "Cite uma capital da África"),
                            ("Ásia", "capital-asia", "Cite uma capital da Ásia"),
                            ("América", "capital-america", "Cite uma capital das Américas")):
        add(pid, text, "capital_mundo", lambda e, c=cont: c in str(e["attrs"].get("continente") or ""))
    add("cidade-mundo-todas", "Cite uma cidade do mundo (fora do Brasil)", "cidade_mundo")
    letters("cidade_mundo", "Cite uma cidade do mundo que começa com {L}", "bclmps", "cidade-mundo")
    add("elemento-todos", "Cite um elemento químico", "elemento")

    build.dropped = dropped  # type: ignore[attr-defined]
    return out
