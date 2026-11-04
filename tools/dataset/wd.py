"""Wikidata helpers: QID resolution, pool queries, sitelink counts."""
from __future__ import annotations

import json
import logging
from pathlib import Path

from .http import CACHE, cached_json, chunks, read_json, sparql

LABEL_CACHE = CACHE / "entities" / "labels.json"


log = logging.getLogger(__name__)


def _as_int(value, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _load(path: Path) -> dict:
    return read_json(path, {}) or {}


def _save(path: Path, data: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=0), encoding="utf-8")


_label_memo = _load(LABEL_CACHE)


def search_qid(label: str, lang: str = "pt") -> str | None:
    key = f"{lang}:{label}"
    if key in _label_memo:
        return _label_memo[key]
    data = cached_json(
        "https://www.wikidata.org/w/api.php",
        {"action": "wbsearchentities", "search": label, "language": lang,
         "uselang": lang, "format": "json", "limit": 5, "type": "item"},
        namespace="entities",
    )
    qid = None
    hits = data.get("search", [])
    if hits:
        # exact label match wins, else first hit
        for h in hits:
            if h.get("label", "").strip().lower() == label.strip().lower():
                qid = h["id"]
                break
        qid = qid or hits[0]["id"]
    _label_memo[key] = qid
    _save(LABEL_CACHE, _label_memo)
    return qid


def qid(label: str, lang: str = "pt") -> str:
    found = search_qid(label, lang)
    if not found:
        raise RuntimeError(f"no QID for {label!r}")
    return found


def sitelinks_for(qids: list[str]) -> dict[str, int]:
    """{qid: sitelink count} via batched SPARQL."""
    memo_path = CACHE / "entities" / "sitelinks.json"
    memo = _load(memo_path)
    todo = [q for q in dict.fromkeys(qids) if q and q not in memo]
    for batch in chunks(todo, 180):
        values = " ".join(f"wd:{q}" for q in batch)
        rows = sparql(f"""
            SELECT ?item ?sl WHERE {{
              VALUES ?item {{ {values} }}
              OPTIONAL {{ ?item wikibase:sitelinks ?sl }}
            }}""")
        for r in rows:
            memo[r["item"].rsplit("/", 1)[-1]] = _as_int(r.get("sl", 0))
        for q in batch:
            memo.setdefault(q, 0)
        _save(memo_path, memo)
    return {q: memo.get(q, 0) for q in qids}


def resolve_titles(titles: list[str]) -> dict[str, dict]:
    """pt.wikipedia title -> {title, qid, pageid} using pageprops/qid."""
    from .http import wp_api
    out: dict[str, dict] = {}
    for batch in chunks(list(dict.fromkeys(titles)), 45):
        data = wp_api(titles="|".join(batch), redirects="1", prop="pageprops|info")
        pages = data.get("query", {}).get("pages", [])
        redirects = {r["from"]: r["to"] for r in data.get("query", {}).get("redirects", [])}
        by_title = {p["title"]: p for p in pages}
        for original in batch:
            target = redirects.get(original, original)
            page = by_title.get(target) or by_title.get(original)
            if not page or page.get("missing"):
                out[original] = {"title": None, "qid": None, "pageid": None}
                continue
            out[original] = {
                "title": page["title"],
                "qid": (page.get("pageprops") or {}).get("wikibase_item"),
                "pageid": page.get("pageid"),
            }
    return out
