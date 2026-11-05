"""Rarity audit of the built dataset: 5 most obvious / 5 rarest per prompt and
the tier distribution per pool.  python3 tools/coverage/audit.py > tools/coverage/rarity_audit.md
"""
import json
import statistics
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
data = json.loads((ROOT / "public/data/garimpo.json").read_text(encoding="utf-8"))
TIERS = [(0.40, "Óbvia"), (0.65, "Comum"), (0.82, "Boa"), (0.95, "Rara"), (1.01, "Raríssima")]


def tier(r):
    for edge, name in TIERS:
        if r < edge:
            return name
    return TIERS[-1][1]


print("# Auditoria de raridade\n")
print("## Distribuição por pool (respostas únicas por pool, pergunta mais ampla)\n")
print("| pool | respostas | " + " | ".join(n for _, n in TIERS) + " |")
print("|---|---|" + "---|" * len(TIERS))
broad = {}
for p in data["prompts"]:
    if p["cat"] not in broad or len(p["answers"]) > len(broad[p["cat"]]["answers"]):
        broad[p["cat"]] = p
for cat, p in sorted(broad.items()):
    counts = defaultdict(int)
    for a in p["answers"]:
        counts[tier(a["rarity"])] += 1
    print(f"| {cat} | {len(p['answers'])} | " + " | ".join(str(counts[n]) for _, n in TIERS) + " |")
print("\n## Por pergunta: 5 mais óbvias / 5 mais raras\n")
for p in data["prompts"]:
    a = p["answers"]
    print(f"- **{p['text']}** ({len(a)}): óbvias: {', '.join(x['n'] for x in a[:5])} — raras: {', '.join(x['n'] for x in a[-5:])}")
sizes = [len(p["answers"]) for p in data["prompts"]]
print(f"\nperguntas={len(sizes)} respostas={sum(sizes)} mediana={statistics.median(sizes)} min={min(sizes)}")
