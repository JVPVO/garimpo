"""Build the playable dataset.

    python -m dataset.build

Reads pools (Wikidata + curated JSON), attaches empirical metrics, computes the
rarity percentile inside each prompt, and writes web/data/garimpo.json.
"""
from __future__ import annotations

import json
import re
import sys
from datetime import UTC, datetime
from pathlib import Path

from .features import (
    enrich_curated_qids,
    genders_for,
    genres_for,
    positions_for,
    years_for,
)
from .http import normalize
from .measure import composite, crawl_pageviews, zipf_map
from .question_bank import build as build_prompts
from .sources import load_all
from .tagging import aliases_for, apply_tags

OUT = Path(__file__).resolve().parents[2] / "public" / "data" / "garimpo.json"
REPORT = Path(__file__).resolve().parents[2] / "reports" / "dataset.md"

DISPLAY_STRIP = {
    "rio": ["Rio "],
    "parque": ["Parque Nacional da ", "Parque Nacional do ", "Parque Nacional de ",
               "Parque Nacional "],
    "estadio": ["Estádio "],
}

LEADING_PARTICLES = re.compile(r"^(do|da|de|dos|das)\s+", re.IGNORECASE)


def display_name(pool: str, name: str) -> str:
    out = name
    for prefix in DISPLAY_STRIP.get(pool, []):
        if out.startswith(prefix):
            out = out[len(prefix):]
    if pool in ("parque", "estadio"):
        out = LEADING_PARTICLES.sub("", out)
    return out.strip()


def dedupe(entries: list[dict], pool: str) -> list[dict]:
    seen: dict[str, dict] = {}
    for entry in entries:
        entry["name"] = display_name(pool, entry["name"])
        key = normalize(entry["name"])
        if not key:
            continue
        if key in seen:
            if (entry.get("sl") or 0) > (seen[key].get("sl") or 0):
                seen[key] = entry
            continue
        seen[key] = entry
    return list(seen.values())


def attach_features(pools: dict[str, list[dict]]) -> None:
    for pool in ("novelas", "filmes"):
        for entry in pools.get(pool, []):
            enrich_curated_qids([entry])
    for pool in ("novelas", "filmes"):
        years = years_for(pools.get(pool, []))
        for entry in pools.get(pool, []):
            year = years.get(entry.get("qid") or "")
            if year:
                entry["attrs"]["ano"] = year
    for pool in ("cantores", "atores", "escritores"):
        genders = genders_for(pools.get(pool, []))
        for entry in pools.get(pool, []):
            gender = genders.get(entry.get("qid") or "")
            if gender:
                entry["attrs"]["genero"] = gender
    genres = genres_for(pools.get("cantores", []))
    for entry in pools.get("cantores", []):
        labels = genres.get(entry.get("qid") or "") or []
        if labels:
            entry["attrs"]["genero_wd"] = labels
    positions = positions_for(pools.get("jogador", []))
    for entry in pools.get("jogador", []):
        labels = positions.get(entry.get("qid") or "") or []
        if labels:
            entry["attrs"]["posicao"] = labels


def main() -> int:
    pools = load_all()
    for key in list(pools):
        pools[key] = dedupe(pools[key], key)
    apply_tags(pools)
    attach_features(pools)
    prompts = build_prompts(pools)
    print(f"pools={len(pools)} prompts={len(prompts)}")

    articles = sorted({a["article"] for p in prompts for a in p["answers"] if a.get("article")})
    pageviews = crawl_pageviews(articles, workers=4)

    # Verification guard: an answer with no pt.wikipedia article and no Wikidata
    # sitelink was never confirmed to exist, so it does not ship.
    dropped = 0
    for prompt in prompts:
        usable = []
        for answer in prompt["answers"]:
            article = answer.get("article") or ""
            views = pageviews.get(article)
            if (views is None or views == 0) and not (answer.get("sl") or 0):
                dropped += 1
                continue
            usable.append(answer)
        prompt["answers"] = usable
    prompts = [prompt for prompt in prompts if len(prompt["answers"]) >= 12]
    print(f"unverified answers dropped={dropped} prompts after guard={len(prompts)}")

    names = []
    for prompt in prompts:
        for answer in prompt["answers"]:
            names.append(answer["name"])
    zipfs = zipf_map(list(dict.fromkeys(names)))

    total_answers = 0
    unique_answers: set[str] = set()
    for prompt in prompts:
        prepared = []
        for answer in prompt["answers"]:
            prepared.append({
                "n": answer["name"],
                "a": aliases_for(answer, prompt["cat"]),
                "qid": answer.get("qid"),
                "pv": pageviews.get(answer["article"] or ""),
                "sl": answer.get("sl") or 0,
                "wf": zipfs.get(answer["name"], 0.0),
                "g": answer.get("gravity"),
                "src": answer.get("attrs", {}).get("source"),
                "an": answer.get("attrs", {}).get("ano"),
                "cat": answer.get("attrs", {}).get("cat"),
            })
        ranked = composite(prepared)
        ranked.sort(key=lambda a: a["popPercentile"], reverse=True)
        for rank, answer in enumerate(ranked, start=1):
            answer["rank"] = rank
        prompt["answers"] = ranked
        prompt["answerCount"] = len(ranked)
        total_answers += len(ranked)
        unique_answers.update(a["n"] for a in ranked)

    payload = {
        "builtAt": datetime.now(UTC).isoformat(timespec="seconds"),
        "method": {
            "version": 1,
            "weights": {"pageviews_pt": 0.50, "wikidata_sitelinks": 0.25,
                        "wordfreq_zipf_pt": 0.20, "gravity": 0.05},
            "pageviewsWindow": "12 full months, all-access, user agents only",
            "pointsFormula": "k = clamp(round(1 + 9 * rarity^1.15), 1, 10)",
            "rarityDefinition": "1 - weighted mean of within-prompt percentile ranks",
            "shareFormula": "softmax of weighted z-scores within the prompt pool",
            "depthPerPoint": 10,
            "sources": [
                {"name": "Wikidata Query Service", "url": "https://query.wikidata.org/"},
                {"name": "Wikimedia Pageviews API (pt.wikipedia)",
                 "url": "https://wikimedia.org/api/rest_v1/metrics/pageviews/"},
                {"name": "wordfreq 3.x, Portuguese", "url": "https://github.com/rspeer/wordfreq"},
                {"name": "pt.wikipedia API", "url": "https://pt.wikipedia.org/w/api.php"},
            ],
        },
        "stats": {
            "prompts": len(prompts),
            "answers": total_answers,
            "uniqueAnswers": len(unique_answers),
            "withPageviews": sum(1 for p in prompts for a in p["answers"] if a["pv"]),
            "pools": {k: len(v) for k, v in pools.items() if v},
        },
        "prompts": [
            {"id": p["id"], "text": p["text"], "cat": p["cat"], "answers": p["answers"]}
            for p in prompts
        ],
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    size_kb = OUT.stat().st_size / 1024
    print(f"wrote {OUT} ({size_kb:.0f} KB)")

    REPORT.parent.mkdir(parents=True, exist_ok=True)
    lines = ["# Dataset do Garimpo", "",
             f"Gerado em {payload['builtAt']}.", "",
             f"- perguntas: **{len(prompts)}**",
             f"- respostas catalogadas: **{total_answers}**",
             f"- respostas únicas: **{len(unique_answers)}**",
             f"- respostas com pageviews: **{payload['stats']['withPageviews']}**", "",
             "| pergunta | pool | respostas | raridade mediana |", "|---|---|---|---|"]
    for p in payload["prompts"]:
        rarities = sorted(a["rarity"] for a in p["answers"])
        median = rarities[len(rarities) // 2] if rarities else 0
        lines.append(f"| {p['text']} | {p['cat']} | {len(p['answers'])} | {median:.2f} |")
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"wrote {REPORT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
