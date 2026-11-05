"""Cached, polite HTTP for the dataset build.

Every network response lands in .cache/ so re-runs are free and the build is
reproducible without hammering upstream services.
"""
from __future__ import annotations

import hashlib
import json
import os
import time
from pathlib import Path
from typing import Any

import requests

ROOT = Path(__file__).resolve().parents[2]
CACHE = ROOT / ".cache" / "dataset"
CACHE.mkdir(parents=True, exist_ok=True)

UA = "GarimpoDatasetBot/1.0 (educational trivia game; https://github.com/arthurafaria/garimpo)"

_session = requests.Session()
_session.headers.update({"User-Agent": UA})


_last_net = [0.0]


def _polite(min_interval: float = 0.3) -> None:
    """Serialise network calls: at most ~3 requests per second to Wikimedia."""
    wait = min_interval - (time.time() - _last_net[0])
    if wait > 0:
        time.sleep(wait)
    _last_net[0] = time.time()


def _key(url: str, params: dict | None) -> str:
    raw = url + json.dumps(params or {}, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(raw.encode()).hexdigest()[:32]


def read_json(path: Path, default: Any = None) -> Any:
    """Read JSON from disk, returning `default` when missing or unreadable."""
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return default


def cached_json(url: str, params: dict | None = None, *, namespace: str = "http",
                ttl: float | None = None, retries: int = 3, timeout: int = 60):
    """GET -> json, cached on disk by URL+params."""
    ns = CACHE / namespace
    ns.mkdir(parents=True, exist_ok=True)
    path = ns / f"{_key(url, params)}.json"
    if path.exists() and (ttl is None or (time.time() - path.stat().st_mtime) < ttl):
        cached = read_json(path)
        if cached is not None:
            return cached
    last: Exception | None = None
    for attempt in range(max(retries, 6)):
        try:
            _polite()
            r = _session.get(url, params=params, timeout=timeout,
                             headers={"Accept": "application/json"})
            if r.status_code in (429, 503):
                wait = r.headers.get("Retry-After")
                time.sleep(float(wait) if wait and wait.isdigit() else 5 * (attempt + 1))
                last = RuntimeError(f"HTTP {r.status_code}")
                continue
            r.raise_for_status()
            data = r.json()
            path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
            if attempt == 0:
                time.sleep(0.12)
            return data
        except Exception as exc:  # noqa: BLE001
            last = exc
            time.sleep(1.5 * (attempt + 1))
    if path.exists():
        return read_json(path)
    raise RuntimeError(f"fetch failed: {url} {params} :: {last}")


def cached_text(url: str, params: dict | None = None, *, namespace: str = "text",
                retries: int = 3) -> str:
    ns = CACHE / namespace
    ns.mkdir(parents=True, exist_ok=True)
    path = ns / f"{_key(url, params)}.txt"
    if path.exists():
        return path.read_text(encoding="utf-8")
    for attempt in range(retries):
        try:
            r = _session.get(url, params=params, timeout=60)
            r.raise_for_status()
            path.write_text(r.text, encoding="utf-8")
            return r.text
        except Exception:  # noqa: BLE001
            time.sleep(1.5 * (attempt + 1))
    raise RuntimeError(f"fetch failed: {url}")


def sparql(query: str) -> list[dict]:
    """Run a SPARQL query against query.wikidata.org, returning simplified rows."""
    data = cached_json(
        "https://query.wikidata.org/sparql",
        {"query": query, "format": "json"},
        namespace="sparql",
        timeout=120,
    )
    out = []
    payload = data or {}
    for row in (payload.get("results") or {}).get("bindings", []):
        out.append({k: v["value"] for k, v in row.items()})
    return out


def wp_api(**params) -> dict:
    base: dict[str, Any] = {"action": "query", "format": "json", "formatversion": "2"}
    base.update(params)
    result = cached_json("https://pt.wikipedia.org/w/api.php", base, namespace="wpapi")
    return result if isinstance(result, dict) else {}


def chunks(seq, n):
    for i in range(0, len(seq), n):
        yield seq[i:i + n]


def normalize(s: str) -> str:
    """Comparison key: lowercase, no accents, single spaces, no punctuation."""
    import unicodedata
    s = unicodedata.normalize("NFD", s)
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    s = s.lower()
    keep = []
    for c in s:
        if c.isalnum() or c in " -'":
            keep.append(c)
        elif c in "/&+":
            keep.append(" ")
    s = "".join(keep)
    s = s.replace("-", " ").replace("'", "")
    return " ".join(s.split())


def ensure_dirs():
    for sub in ("sparql", "wpapi", "text", "http", "pageviews", "entities"):
        (CACHE / sub).mkdir(parents=True, exist_ok=True)
    return CACHE


if __name__ == "__main__":
    os.makedirs(CACHE, exist_ok=True)
    print(CACHE)
