"""Build the one-page data report rendered in T3 (self-contained HTML)."""
from __future__ import annotations

import json
import random
from collections import Counter
from collections.abc import Sequence
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = json.loads((ROOT / "public" / "data" / "garimpo.json").read_text(encoding="utf-8"))
VALIDATION = json.loads((ROOT / "public" / "data" / "validation.json").read_text(encoding="utf-8"))
OUT = ROOT / "reports" / "acervo.html"

RNG = random.Random(7)
BANDS = [("Solo", 0, 0.23), ("Arenito", 0.23, 0.38), ("Ardósia", 0.38, 0.57),
         ("Quartzito", 0.57, 0.76), ("Xisto", 0.76, 0.88), ("Gnaisse", 0.88, 0.94),
         ("Kimberlito", 0.94, 1.01)]


def fmt(n: int) -> str:
    return f"{n:,}".replace(",", ".")


def pick_rank(n: int, skill: float) -> int:
    if RNG.random() < 0.12:
        return 0
    if skill < 0.55:
        weights = [0.55, 0.25, 0.12, 0.08]
    elif skill < 0.85:
        floor = max(6, n // 3)
        weights = [1 / (r**0.9) for r in range(1, floor + 1)]
    else:
        if RNG.random() < 0.35:
            start = max(4, int(n * 0.66))
            if start <= n:
                return RNG.randint(start, n)
        floor = min(n, max(12, n // 2))
        weights = [0.06, 0.06, 0.06] + [r**0.9 for r in range(4, floor + 1)]
    total = sum(weights)
    roll = RNG.random() * total
    acc = 0.0
    for i, weight in enumerate(weights, start=1):
        acc += weight
        if roll <= acc:
            return i
    return 1


def simulate(prompts: list[dict], runs: int = 6000) -> list[int]:
    totals = []
    for _ in range(runs):
        total = 0
        for prompt in RNG.sample(prompts, 7):
            rank = pick_rank(len(prompt["answers"]), RNG.random())
            if rank == 0:
                continue
            rarity = prompt["answers"][rank - 1]["rarity"]
            total += round((1 + 9 * rarity**0.32) * 10)
        totals.append(min(700, total))
    return sorted(totals)


def percentile(values: list[int], p: float) -> int:
    return values[min(len(values) - 1, int(len(values) * p))]


def esc(text: str) -> str:
    return (text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def bars(categories: Sequence[tuple[str | None, int]], total: int) -> str:
    rows = []
    top = max(count for _, count in categories) or 1
    for name, count in categories:
        width = count / top * 100
        rows.append(
            f'<div class="row"><span class="k">{esc(name or "·")}</span>'
            f'<span class="track"><i style="width:{width:.1f}%"></i></span>'
            f'<span class="v">{count}</span></div>'
        )
    return "\n".join(rows)


def histogram(values: list[int], bins: int, size: int, label: str) -> tuple[str, str]:
    counts = [0] * bins
    for value in values:
        counts[min(bins - 1, value // size)] += 1
    top = max(counts) or 1
    cells = []
    for index, count in enumerate(counts):
        height = count / top * 100
        lo = index * size
        cells.append(
            f'<div class="col" title="{lo}–{lo + size - 1}{label}: {count}">'
            f'<i style="height:{height:.1f}%"></i></div>'
        )
    axis = "".join(
        f'<span>{index * size}</span>' for index in range(0, bins + 1, max(1, bins // 6))
    )
    return "".join(cells), axis


def main() -> None:
    prompts = DATA["prompts"]
    answers = [a for p in prompts for a in p["answers"]]
    stats = DATA["stats"]

    cats = Counter(p["cat"] for p in prompts)
    names = {
        "cidade": "cidades", "novelas": "novelas", "jogador": "seleção",
        "rio": "rios", "frutas_nativas": "frutas", "escritores": "escritores",
        "time": "times", "doces": "doces", "cantores": "cantores",
        "filmes": "filmes", "atores": "atores", "aves": "aves",
        "parque": "parques", "estadio": "estádios", "pratos_tipicos": "pratos",
        "festas": "festas", "marcas": "marcas", "folclore": "folclore",
        "dancas": "danças", "instrumentos": "instrumentos",
        "palavras_tupi": "tupi", "uf": "estados", "presidente": "presidentes",
        "mamiferos": "mamíferos", "girias": "gírias", "bbb": "BBB",
        "bbb_campeoes": "BBB", "tv_globinho": "TV Globinho", "desenhos": "desenhos",
    }
    cat_pairs: list[tuple[str, int]] = sorted(
        ((str(names.get(str(c)) or c), int(n)) for c, n in cats.items()),
        key=lambda item: -item[1],
    )

    pool_sizes = sorted(len(p["answers"]) for p in prompts)
    pool_hist, pool_axis = histogram(pool_sizes, 10, 10, " respostas")

    band_counts = Counter()
    for answer in answers:
        rarity = answer["rarity"]
        band = next((name for name, lo, hi in BANDS if lo <= rarity < hi), BANDS[-1][0])
        band_counts[band] += 1
    band_rows = "".join(
        f'<div class="row"><span class="k">{name}</span>'
        f'<span class="track"><i style="width:{band_counts[name] / len(answers) * 100:.1f}%"></i></span>'
        f'<span class="v">{band_counts[name] / len(answers) * 100:.0f}%</span></div>'
        for name, _, _ in BANDS
    )

    depths = simulate(prompts)
    depth_hist, depth_axis = histogram(depths, 14, 50, " m")
    p10, p50, p90 = percentile(depths, 0.1), percentile(depths, 0.5), percentile(depths, 0.9)

    rows = VALIDATION["rows"]
    width, height, pad = 520, 240, 28
    points = []
    for row in rows:
        x = pad + row["ourRarity"] * (width - pad * 2)
        y = height - pad - (row["crowdScore"] / 100) * (height - pad * 2)
        points.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="4" />')
    grid = "".join(
        f'<line x1="{pad}" y1="{height - pad - v / 100 * (height - pad * 2):.1f}" '
        f'x2="{width - pad}" y2="{height - pad - v / 100 * (height - pad * 2):.1f}" />'
        for v in (0, 25, 50, 75, 100)
    )
    ylabels = "".join(
        f'<text x="{pad - 6}" y="{height - pad - v / 100 * (height - pad * 2) + 4:.1f}" '
        f'text-anchor="end">{v}</text>'
        for v in (0, 25, 50, 75, 100)
    )

    html = f"""<!doctype html>
<html lang="pt-BR">
<head>
<meta charset="utf-8" />
<title>Garimpo · raio-x do acervo</title>
<style>
  :root {{ color-scheme: light dark; }}
  * {{ box-sizing: border-box; }}
  body {{ margin: 0; font-family: ui-sans-serif, system-ui, -apple-system, "Segoe UI", sans-serif;
         color: var(--foreground); background: transparent; }}
  .wrap {{ max-width: 980px; margin: 0 auto; padding: 4px 0 8px; }}
  h1 {{ font-size: 26px; line-height: 1.1; margin: 0 0 4px; letter-spacing: -0.6px; }}
  .sub {{ color: var(--muted-foreground); font-size: 13px; margin: 0 0 20px; }}
  .grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }}
  @media (max-width: 720px) {{ .grid {{ grid-template-columns: 1fr; }} }}
  .card {{ border: 1px solid var(--border); border-radius: var(--radius, 8px); padding: 14px 16px;
           background: var(--card); }}
  .card h2 {{ font-size: 12px; letter-spacing: 1.2px; text-transform: uppercase;
              color: var(--muted-foreground); margin: 0 0 2px; font-weight: 600; }}
  .card p {{ font-size: 12px; color: var(--muted-foreground); margin: 0 0 12px; line-height: 1.45; }}
  .row {{ display: grid; grid-template-columns: 84px 1fr 34px; gap: 8px; align-items: center;
          font-size: 12px; margin-bottom: 6px; }}
  .row .k {{ color: var(--foreground); opacity: .85; white-space: nowrap; overflow: hidden;
             text-overflow: ellipsis; }}
  .row .track {{ height: 9px; background: var(--muted); border-radius: 2px; overflow: hidden; }}
  .row .track i {{ display: block; height: 100%; background: var(--chart-1); }}
  .row .v {{ text-align: right; font-variant-numeric: tabular-nums; color: var(--foreground); }}
  .hist {{ display: flex; align-items: flex-end; gap: 3px; height: 120px; margin-top: 6px; }}
  .hist .col {{ flex: 1; height: 100%; display: flex; align-items: flex-end; }}
  .hist .col i {{ display: block; width: 100%; background: var(--chart-3); border-radius: 1px 1px 0 0; }}
  .axis {{ display: flex; justify-content: space-between; font-size: 10px;
           color: var(--muted-foreground); margin-top: 4px; font-variant-numeric: tabular-nums; }}
  .stats {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 8px; margin-bottom: 16px; }}
  .stats div {{ border: 1px solid var(--border); border-radius: var(--radius, 8px); padding: 9px 11px; }}
  .stats b {{ display: block; font-size: 20px; letter-spacing: -0.5px; font-variant-numeric: tabular-nums; }}
  .stats span {{ font-size: 10px; letter-spacing: .8px; text-transform: uppercase;
                 color: var(--muted-foreground); }}
  svg text {{ font-size: 10px; fill: var(--muted-foreground); }}
  svg line {{ stroke: var(--border); stroke-width: 1; }}
  svg circle {{ fill: var(--chart-2); opacity: .82; }}
  .rho {{ font-variant-numeric: tabular-nums; font-weight: 650; color: var(--foreground); }}
  .note {{ font-size: 11px; color: var(--muted-foreground); margin-top: 10px; line-height: 1.5; }}
  .wide {{ grid-column: 1 / -1; }}
</style>
</head>
<body>
<div class="wrap">
  <h1>Garimpo — raio-x do acervo</h1>
  <p class="sub">Tudo abaixo é medido no arquivo que o jogo carrega: {fmt(stats["prompts"])} perguntas,
     {fmt(stats["answers"])} respostas catalogadas, {fmt(stats["uniqueAnswers"])} únicas.
     Coleta de pageviews: {fmt(stats["withPageviews"])} respostas.</p>

  <div class="stats">
    <div><b>{fmt(stats["prompts"])}</b><span>perguntas</span></div>
    <div><b>{fmt(stats["answers"])}</b><span>respostas</span></div>
    <div><b>{p50} m</b><span>mergulho mediano</span></div>
    <div><b class="rho">ρ {VALIDATION["spearman"]:.2f}</b><span>vs. multidão real</span></div>
  </div>

  <div class="grid">
    <div class="card">
      <h2>Perguntas por acervo</h2>
      <p>Cada barra é um pool de respostas verificadas contra a pt.wikipedia.</p>
      {bars(cat_pairs, len(prompts))}
    </div>

    <div class="card">
      <h2>Tamanho dos acervos</h2>
      <p>Respostas por pergunta. Piso de 10 para um percentil honesto; máximo {pool_sizes[-1]}.</p>
      <div class="hist">{pool_hist}</div>
      <div class="axis"><span>10</span><span>60</span><span>100+</span></div>
      <p class="note">Mediana {pool_sizes[len(pool_sizes) // 2]} respostas por pergunta.</p>
    </div>

    <div class="card">
      <h2>Onde as respostas caem</h2>
      <p>Distribuição real das {fmt(len(answers))} respostas pelas sete camadas da placa.</p>
      {band_rows}
    </div>

    <div class="card">
      <h2>Profundidade simulada</h2>
      <p>6 000 mergulhos de 7 perguntas com um modelo de jogador por posição no acervo.</p>
      <div class="hist">{depth_hist}</div>
      <div class="axis">{depth_axis}</div>
      <p class="note">p10 {p10} m · mediana {p50} m · p90 {p90} m · 700 m exige seis respostas
         entre as mais raras de cada acervo.</p>
    </div>

    <div class="card wide">
      <h2>Validação: nossa raridade × raridade da multidão</h2>
      <p>Pergunta “{esc(VALIDATION["prompt"])}”, {VALIDATION["n"]} respostas, percentil real de
         jogadores do Krillion (eixo y) contra a raridade medida aqui (eixo x).</p>
      <svg viewBox="0 0 {width} {height}" width="100%" height="{height}" role="img"
           aria-label="dispersão raridade medida contra score da multidão">
        {grid}
        {ylabels}
        <text x="{pad}" y="{height - 6}">0 · óbvia</text>
        <text x="{width - pad}" y="{height - 6}" text-anchor="end">1 · rara</text>
        {''.join(points)}
      </svg>
      <p class="note">Correlação de Spearman <span class="rho">ρ = {VALIDATION["spearman"]:.3f}</span>
         (n = {VALIDATION["n"]}), medida em {VALIDATION["date"]}. A multidão do Krillion é
         anglófona; num acervo brasileiro os sinais tendem a separar melhor.</p>
    </div>
  </div>
</div>
</body>
</html>
"""
    OUT.write_text(html, encoding="utf-8")
    print(f"wrote {OUT} ({len(html) / 1024:.0f} KB)")
    print(f"p50={p50} p10={p10} p90={p90} bands={dict(band_counts)}")


if __name__ == "__main__":
    main()
