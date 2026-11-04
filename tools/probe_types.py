import sys

sys.path.insert(0, "tools")
from dataset.http import sparql  # noqa: E402
from dataset.wd import search_qid  # noqa: E402

LABELS = ["país", "país soberano", "capital", "capital nacional", "elemento químico",
          "jogo eletrônico", "anime", "série de anime", "banda musical", "banda",
          "cidade", "Pokémon", "espécie de Pokémon", "super-herói", "clube de futebol"]

for label in LABELS:
    found = search_qid(label)
    if not found:
        print(f"{label:24s} -> ???")
        continue
    rows = sparql(f"""SELECT (COUNT(DISTINCT ?i) AS ?n) WHERE {{ ?i wdt:P31 wd:{found} . }}""")
    count = rows[0]["n"] if rows else "?"
    print(f"{label:24s} -> {found}  instances={count}")
