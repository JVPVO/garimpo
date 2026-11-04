"""Validate the rarity stack against real crowd data.

Krillion (krillion.io) exposes a public per-answer scoring endpoint used by its
own client. A small, paced sample of answers to one of today's prompts lets us
compare our empirical rarity with the crowd percentile of real players.

Politeness: ~1 request/second, identified client, one prompt, < 50 answers.
"""
from __future__ import annotations

import json
import math
import sys
import time
import uuid
from datetime import UTC, datetime
from pathlib import Path

import requests

sys.path.insert(0, "tools")
from dataset.measure import composite, crawl_pageviews, zipf_map  # noqa: E402
from dataset.wd import resolve_titles, sitelinks_for  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "public" / "data" / "validation.json"
REPORT = ROOT / "reports" / "validation.md"

ANSWERS = [
    "Pikachu", "Charizard", "Bulbasaur", "Squirtle", "Mewtwo", "Mew", "Eevee",
    "Gengar", "Snorlax", "Dragonite", "Lucario", "Greninja", "Gardevoir",
    "Gyarados", "Machamp", "Alakazam", "Arcanine", "Lapras", "Onix", "Psyduck",
    "Jigglypuff", "Magikarp", "Ditto", "Vaporeon", "Umbreon", "Blastoise",
    "Venusaur", "Raichu", "Cubone", "Scyther", "Aerodactyl", "Articuno",
    "Zapdos", "Lugia", "Rayquaza", "Tyranitar", "Heracross", "Skarmory",
    "Houndoom", "Donphan", "Qwilfish", "Dunsparce", "Luvdisc", "Finneon", "Spinda",
]

UA = "GarimpoValidation/1.0 (research; contact: local)"


def ranks(values: list[float]) -> list[float]:
    order = sorted(range(len(values)), key=lambda i: values[i])
    out = [0.0] * len(values)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and values[order[j + 1]] == values[order[i]]:
            j += 1
        avg = (i + j) / 2
        for k in range(i, j + 1):
            out[order[k]] = avg
        i = j + 1
    return out


def spearman(xs: list[float], ys: list[float]) -> float:
    rx, ry = ranks(xs), ranks(ys)
    n = len(xs)
    mx, my = sum(rx) / n, sum(ry) / n
    num = sum((a - mx) * (b - my) for a, b in zip(rx, ry, strict=True))
    dx = math.sqrt(sum((a - mx) ** 2 for a in rx))
    dy = math.sqrt(sum((b - my) ** 2 for b in ry))
    return num / (dx * dy) if dx and dy else 0.0


def main() -> int:
    session = requests.Session()
    session.headers.update({"User-Agent": UA, "accept": "application/json"})

    today = session.get("https://krillion.io/api/today", timeout=20).json()
    date = today["date"]
    prompt = next((p for p in today["prompts"] if "pok" in p["text"].lower()), None)
    if not prompt:
        print("no Pokémon prompt today; skipping validation")
        return 0
    print(f"prompt {prompt['id']}: {prompt['text']} ({date})")

    mapping = resolve_titles(ANSWERS)
    titles = [(name, (mapping.get(name) or {}).get("title")) for name in ANSWERS]
    titles = [(name, title) for name, title in titles if title]
    qids = [(mapping.get(name) or {}).get("qid") for name, _ in titles]
    sitelinks = sitelinks_for([q for q in qids if q])
    pageviews = crawl_pageviews([title for _, title in titles], workers=2)
    zipfs = zipf_map([name for name, _ in titles])

    prepared = []
    for name, title in titles:
        qid = (mapping.get(name) or {}).get("qid")
        prepared.append({
            "n": name,
            "a": [],
            "pv": pageviews.get(title),
            "sl": sitelinks.get(qid or "", 0),
            "wf": zipfs.get(name, 0.0),
            "g": None,
        })
    scored = composite(prepared)

    rows = []
    for entry in scored:
        body = {
            "date": date,
            "promptId": prompt["id"],
            "answer": entry["n"],
            "previewCorrection": True,
            "playerId": str(uuid.uuid4()),
        }
        try:
            response = session.post("https://krillion.io/api/submit", json=body, timeout=20)
            if response.status_code == 429:
                time.sleep(20)
                continue
            if response.status_code != 200:
                continue
            data = response.json()
        except requests.RequestException:
            continue
        finally:
            time.sleep(1.1)
        if not data.get("accepted"):
            continue
        rows.append({"answer": data.get("answer", entry["n"]),
                     "ourRarity": entry["rarity"],
                     "crowdScore": data.get("score"),
                     "tier": data.get("tier")})
        print(f"  {entry['n']:14s} ours={entry['rarity']:.2f}  crowd={data.get('score')}")

    if len(rows) < 12:
        print(f"too few comparable answers ({len(rows)}); not writing validation")
        return 1

    rho = spearman([r["ourRarity"] for r in rows], [float(r["crowdScore"]) for r in rows])
    payload = {
        "source": "krillion.io · /api/submit (crowd percentile of real players)",
        "prompt": prompt["text"],
        "date": date,
        "n": len(rows),
        "spearman": round(rho, 3),
        "builtAt": datetime.now(UTC).isoformat(timespec="seconds"),
        "rows": rows,
    }
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8")

    lines = [
        "# Validação contra multidão real",
        "",
        f"Fonte: {payload['source']}",
        f"Pergunta: {payload['prompt']} ({date})",
        f"Amostra: {len(rows)} respostas · Spearman ρ = {rho:.3f}",
        "",
        "| resposta | raridade medida | score da multidão |",
        "|---|---|---|",
    ]
    for row in sorted(rows, key=lambda r: -r["ourRarity"]):
        lines.append(f"| {row['answer']} | {row['ourRarity']:.2f} | {row['crowdScore']} |")
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"rho={rho:.3f} n={len(rows)} -> {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
