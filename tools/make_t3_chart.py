"""Generate the compact one-page chart rendered inside T3."""
from __future__ import annotations

import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from make_chart import DATA, VALIDATION, percentile, simulate  # noqa: E402

OUT = Path(__file__).resolve().parents[1] / "reports" / "acervo-t3.html"

LABEL = {
    "cidade": "cidades", "novelas": "novelas", "jogador": "seleção", "rio": "rios",
    "frutas_nativas": "frutas", "escritores": "escritores", "time": "times",
    "doces": "doces", "cantores": "cantores", "filmes": "filmes", "atores": "atores",
    "aves": "aves", "parque": "parques", "estadio": "estádios",
    "pratos_tipicos": "pratos", "festas": "festas", "marcas": "marcas",
    "folclore": "folclore", "dancas": "danças", "instrumentos": "instrumentos",
    "palavras_tupi": "tupi", "uf": "estados", "presidente": "presidentes",
    "mamiferos": "mamíferos", "girias": "gírias", "bbb": "BBB",
    "bbb_campeoes": "BBB", "tv_globinho": "TV Globinho", "desenhos": "desenhos",
    "pais": "países", "capital_mundo": "capitais", "elemento": "elementos",
    "cidade_mundo": "cidades do mundo", "videogame": "videogames",
    "anime": "animes", "banda": "bandas", "pokemon": "Pokémon",
    "heroi": "heróis", "comida_mundo": "comida do mundo",
    "marca_global": "marcas globais",
}


def main() -> None:
    prompts = DATA["prompts"]
    stats = DATA["stats"]
    depths = simulate(prompts)
    p10, p50, p90 = percentile(depths, 0.1), percentile(depths, 0.5), percentile(depths, 0.9)

    counts = Counter(LABEL.get(p["cat"], p["cat"]) for p in prompts)
    top = counts.most_common(10)
    rest = len(prompts) - sum(n for _, n in top)
    rows = top + [(f"outros {len(counts) - len(top)}", rest)]
    peak = max(n for _, n in rows)
    bars = "\n".join(
        f'<div class="row"><span class="k">{name}</span>'
        f'<span class="t"><i style="width:{n / peak * 100:.1f}%"></i></span>'
        f'<span class="v">{n}</span></div>'
        for name, n in rows
    )

    bins = [0] * 14
    for depth in depths:
        bins[min(13, depth // 50)] += 1
    peak = max(bins) or 1
    bars_svg = []
    for index, count in enumerate(bins):
        height = count / peak * 108
        bars_svg.append(
            f'<rect x="{32 + index * 30}" y="{140 - height:.1f}" width="26" '
            f'height="{height:.1f}" rx="1" />'
        )

    dots = []
    for row in VALIDATION["rows"]:
        cx = 40 + row["ourRarity"] * 410
        cy = 160 - (row["crowdScore"] / 100) * 150
        dots.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="4" />')

    html = TEMPLATE.format(
        prompts=stats["prompts"],
        answers=f"{stats['answers']:,}".replace(",", "."),
        p50=p50, p10=p10, p90=p90,
        rho=f"{VALIDATION['spearman']:.2f}".replace(".", ","),
        bars=bars,
        histogram="".join(bars_svg),
        dots="".join(dots),
        n=VALIDATION["n"],
        total_cats=len(counts),
    )
    OUT.write_text(html, encoding="utf-8")
    print(f"wrote {OUT} ({len(html) / 1024:.1f} KB) p50={p50} p90={p90}")


TEMPLATE = """<!doctype html>
<html lang="pt-BR">
<head>
<meta charset="utf-8" />
<title>Garimpo — raio-x do acervo</title>
<style>
  :root {{ color-scheme: light dark; }}
  * {{ box-sizing: border-box; }}
  body {{ margin: 0; background: transparent; color: var(--foreground);
         font-family: ui-sans-serif, system-ui, -apple-system, "Segoe UI", sans-serif; }}
  .wrap {{ max-width: 960px; margin: 0 auto; }}
  h1 {{ font-size: 22px; margin: 0 0 4px; letter-spacing: -0.4px; }}
  .sub {{ margin: 0 0 16px; font-size: 12px; color: var(--muted-foreground); }}
  .stats {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 8px; margin-bottom: 14px; }}
  .stats div {{ border: 1px solid var(--border); border-radius: 8px; padding: 8px 10px; }}
  .stats b {{ display: block; font-size: 19px; font-variant-numeric: tabular-nums; letter-spacing: -0.4px; }}
  .stats span {{ font-size: 10px; letter-spacing: .7px; text-transform: uppercase; color: var(--muted-foreground); }}
  .grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 14px; }}
  @media (max-width: 700px) {{ .grid {{ grid-template-columns: 1fr; }} .stats {{ grid-template-columns: 1fr 1fr; }} }}
  .card {{ border: 1px solid var(--border); border-radius: 8px; padding: 12px 14px; background: var(--card); }}
  .card h2 {{ font-size: 11px; letter-spacing: 1.1px; text-transform: uppercase; margin: 0 0 2px;
             color: var(--muted-foreground); font-weight: 600; }}
  .card p {{ font-size: 12px; line-height: 1.45; color: var(--muted-foreground); margin: 0 0 10px; }}
  .card p b {{ color: var(--foreground); }}
  .wide {{ grid-column: 1 / -1; }}
  svg {{ display: block; width: 100%; height: auto; }}
  svg text {{ font-size: 10px; fill: var(--muted-foreground); font-variant-numeric: tabular-nums; }}
  svg .grid {{ stroke: var(--border); stroke-width: 1; }}
  svg .bar {{ fill: var(--chart-1); }}
  svg .dot {{ fill: var(--chart-2); opacity: .8; }}
  .rows {{ display: grid; gap: 6px; }}
  .row {{ display: grid; grid-template-columns: 82px 1fr 26px; gap: 8px; align-items: center; font-size: 12px; }}
  .row .k {{ color: var(--foreground); opacity: .85; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }}
  .row .t {{ height: 8px; background: var(--muted); border-radius: 2px; overflow: hidden; }}
  .row .t i {{ display: block; height: 100%; background: var(--chart-3); }}
  .row .v {{ text-align: right; font-variant-numeric: tabular-nums; }}
  .foot {{ font-size: 11px; color: var(--muted-foreground); margin-top: 10px; line-height: 1.5; }}
</style>
</head>
<body>
<div class="wrap">
  <h1>Garimpo — raio-x do acervo</h1>
  <p class="sub">Medido no arquivo que o jogo carrega, não em estimativa. Coleta de 04 nov 2026.</p>

  <div class="stats">
    <div><b>{prompts}</b><span>perguntas</span></div>
    <div><b>{answers}</b><span>respostas catalogadas</span></div>
    <div><b>{p50} m</b><span>mergulho mediano</span></div>
    <div><b>ρ {rho}</b><span>vs. multidão real</span></div>
  </div>

  <div class="grid">
    <div class="card">
      <h2>Onde cada mergulho para</h2>
      <p>6 000 descidas simuladas de 7 perguntas. Mediana <b>{p50} m</b>, p10 <b>{p10} m</b>,
         p90 <b>{p90} m</b>. Os 700 m exigem seis ou sete respostas entre as mais raras de cada acervo.</p>
      <svg viewBox="0 0 460 168" role="img" aria-label="histograma de profundidade por faixa de 50 metros">
        <line class="grid" x1="30" y1="140" x2="450" y2="140" />
        <g class="bar">{histogram}</g>
        <line class="grid" x1="90" y1="0" x2="90" y2="140" stroke-dasharray="3 3" />
        <line class="grid" x1="207" y1="0" x2="207" y2="140" stroke-dasharray="3 3" />
        <line class="grid" x1="325" y1="0" x2="325" y2="140" stroke-dasharray="3 3" />
        <text x="92" y="10">p10 {p10} m</text>
        <text x="209" y="10">mediana {p50} m</text>
        <text x="327" y="10">p90 {p90} m</text>
        <text x="32" y="158">0</text>
        <text x="182" y="158">250</text>
        <text x="332" y="158">500</text>
        <text x="428" y="158">700</text>
      </svg>
      <p class="foot">Cada barra cobre 50 m. A montanha fica entre 300 e 400 m: é onde a maioria
         dos mergulhos encosta. Acima de 600 m, a barra some — chegar lá é exceção.</p>
    </div>

    <div class="card">
      <h2>De onde vêm as perguntas</h2>
      <p>Perguntas por pool de respostas. Cidades, novelas e seleção puxam a fila; cada pool
         foi verificado contra a pt.wikipedia antes de entrar.</p>
      <div class="rows">
        {bars}
      </div>
      <p class="foot">{total_cats} pools no total: do folclore ao BBB, da TV Globinho a palavras
         de origem tupi.</p>
    </div>

    <div class="card wide">
      <h2>Nossa raridade × raridade da multidão</h2>
      <p>{n} respostas à pergunta “Name any Pokémon”, comparadas com o percentil real de jogadores
         do Krillion (eixo y) contra a raridade medida aqui (eixo x). Spearman <b>ρ = {rho}</b>:
         a régua ordena de forma parecida com a multidão, sem nunca ter visto um jogador.</p>
      <svg viewBox="0 0 460 190" role="img" aria-label="dispersão entre raridade medida e score da multidão">
        <line class="grid" x1="40" y1="160" x2="450" y2="160" />
        <line class="grid" x1="40" y1="120" x2="450" y2="120" />
        <line class="grid" x1="40" y1="80" x2="450" y2="80" />
        <line class="grid" x1="40" y1="40" x2="450" y2="40" />
        <line class="grid" x1="40" y1="10" x2="450" y2="10" />
        <text x="34" y="164" text-anchor="end">0</text>
        <text x="34" y="124" text-anchor="end">25</text>
        <text x="34" y="84" text-anchor="end">50</text>
        <text x="34" y="44" text-anchor="end">75</text>
        <text x="34" y="14" text-anchor="end">100</text>
        <g class="dot">{dots}</g>
        <text x="40" y="182">0 · óbvia</text>
        <text x="450" y="182" text-anchor="end">1 · rara</text>
      </svg>
      <p class="foot">A multidão do Krillion é anglófona e responde em faixas grosseiras (10/30/60/85).
         Num acervo brasileiro os sinais tendem a separar melhor — isso ainda não está provado.</p>
    </div>
  </div>
</div>
</body>
</html>
"""


if __name__ == "__main__":
    main()
