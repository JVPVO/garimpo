import { useEffect, useState } from "react";
import { PixelSprite } from "../art/PixelSprite.tsx";
import { TOOLS } from "../art/sprites.ts";
import { TIERS } from "../game/score.ts";
import { STRATA } from "../game/strata.ts";
import type { Dataset } from "../game/types.ts";

const RANGES = ["p 0–39", "p 40–64", "p 65–81", "p 82–94", "p 95–100"];

type Validation = {
  source: string;
  n: number;
  spearman: number;
  prompts: string[];
  builtAt: string;
};

type Props = {
  dataset: Dataset;
  shares: number[];
  onHome: () => void;
};

export function Method({ dataset, shares, onHome }: Props) {
  const [validation, setValidation] = useState<Validation | null>(null);

  useEffect(() => {
    let alive = true;
    fetch(`${import.meta.env.BASE_URL}data/validation.json`)
      .then((response) => (response.ok ? response.json() : null))
      .then((data: Validation | null) => {
        if (alive) setValidation(data);
      })
      .catch(() => undefined);
    return () => {
      alive = false;
    };
  }, []);

  return (
    <div className="method">
      <h1>Como medimos</h1>
      <p style={{ maxWidth: "62ch" }}>
        Nenhuma raridade aqui é opinião. Cada resposta carrega três medições públicas, e a posição
        dela dentro da pergunta vira a profundidade que ela cava. O acervo inteiro foi gerado a
        partir das fontes abaixo, e o número de cada resposta aparece no jogo.
      </p>

      <div className="cols">
        <div>
          <h2>1 · Os três sinais</h2>
          <table>
            <thead>
              <tr>
                <th>Sinal</th>
                <th>O que mede</th>
                <th>Peso</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td>pageviews</td>
                <td>média de acessos mensais no verbete da pt.wikipedia nos últimos 12 meses</td>
                <td>50%</td>
              </tr>
              <tr>
                <td>sitelinks</td>
                <td>quantas línguas têm um verbete sobre aquilo (Wikidata)</td>
                <td>25%</td>
              </tr>
              <tr>
                <td>corpus</td>
                <td>frequência da palavra em português no wordfreq (zipf)</td>
                <td>20%</td>
              </tr>
              <tr>
                <td>gravidade</td>
                <td>população, quando a pergunta é sobre um lugar</td>
                <td>5%</td>
              </tr>
            </tbody>
          </table>

          <h2>2 · A conta</h2>
          <p>
            Para cada pergunta, os sinais viram <em>postos percentuais</em> dentro do acervo daquela
            pergunta. A raridade é o complemento da média ponderada:
          </p>
          <pre>{`posto_m(i) = (posição de i em m) / (n - 1)
popularidade(i) = Σ peso_m · posto_m(i) / Σ peso_m
raridade(i) = 1 - popularidade(i)`}</pre>
          <p>
            Um raro de verdade precisa ser raro nos três sinais ao mesmo tempo. Quando falta um
            sinal (uma resposta sem verbete, por exemplo), os pesos restantes são renormalizados —
            nunca se inventa zero.
          </p>
          <p>
            O <b>p</b> que aparece na revelação é esse posto: 0 é a resposta mais óbvia do acervo,
            100 a mais rara. A linha <b>≈ 1 em N</b> é outra medida: uma estimativa de quantos
            jogadores dariam aquela resposta, a partir da distribuição de popularidade dentro do
            acervo. São escalas diferentes e o jogo mostra as duas com nome.
          </p>

          <h2>3 · A descida</h2>
          <pre>{`pontos   = 1 + 9 · raridade^0,32   (1 a 10)
metros   = round(pontos × 10)      (10 a 100 m)
poço     = min(700, soma dos 7)`}</pre>
          <p>
            A curva foi calibrada contra este acervo: 6 000 descidas simuladas com um modelo de
            jogador por posição no acervo. A mediana fica em <b>≈ 346 m</b> e o décimo superior em{" "}
            <b>≈ 426 m</b>; chegar aos 700 m exige seis respostas entre as mais raras de cada
            pergunta, não uma sorte isolada. Uma resposta óbvia sempre rende 10 m, nunca zero.
          </p>
        </div>

        <div>
          <h2>4 · As camadas</h2>
          <p>Cada banda cobre uma janela de raridade e mostra quanto do acervo real caiu nela.</p>
          <div className="legend">
            {STRATA.map((stratum, index) => (
              <div
                key={stratum.id}
                style={{
                  ["--fill" as string]: stratum.fill,
                  ["--hatch" as string]: stratum.hatch,
                }}
              >
                <span>
                  <b>{stratum.label}</b> · {stratum.from}–{stratum.to} m · {stratum.fact}
                </span>
                <span>{Math.round((shares[index] ?? 0) * 100)}%</span>
              </div>
            ))}
          </div>

          <h2>5 · As ferramentas</h2>
          <p>Cada resposta cava com uma máquina que depende só da raridade dela.</p>
          <table>
            <thead>
              <tr>
                <th>Ferramenta</th>
                <th>Raridade</th>
                <th>Posto no acervo</th>
              </tr>
            </thead>
            <tbody>
              {TIERS.map((tier) => (
                <tr key={tier.id}>
                  <td>
                    <span style={{ display: "inline-flex", alignItems: "center", gap: 8 }}>
                      <PixelSprite sprite={TOOLS[tier.tool].frames[0]} scale={1} /> {tier.toolName}
                    </span>
                  </td>
                  <td>{tier.label}</td>
                  <td>{RANGES[tier.id - 1]}</td>
                </tr>
              ))}
            </tbody>
          </table>

          <h2>6 · O acervo</h2>
          <p>
            {dataset.stats.prompts} perguntas, {dataset.stats.answers.toLocaleString("pt-BR")}{" "}
            respostas catalogadas ({dataset.stats.uniqueAnswers.toLocaleString("pt-BR")} únicas),{" "}
            {dataset.stats.withPageviews.toLocaleString("pt-BR")} delas com medição de pageviews.
            Última coleta: {new Date(dataset.builtAt).toLocaleDateString("pt-BR")}.
          </p>
          <p style={{ fontSize: 13 }}>
            Cada pergunta aceita apenas respostas do seu acervo. Uma resposta válida que não está no
            acervo é recusada — e o jogo diz isso na tela em vez de inventar uma raridade.
          </p>

          {validation ? (
            <>
              <h2>7 · Validação</h2>
              <p>
                A régua foi conferida contra um conjunto independente de respostas de multidão:{" "}
                <b>{validation.n}</b> respostas comparadas com o percentil real de jogadores.
                Correlação de Spearman entre a nossa raridade e a da multidão:{" "}
                <b className="mono">{validation.spearman.toFixed(2)}</b>.
              </p>
            </>
          ) : null}

          <h2>{validation ? "8" : "7"} · Fontes</h2>
          <ul className="sources">
            {dataset.method.sources.map((source) => (
              <li key={source.url}>
                <a href={source.url} target="_blank" rel="noreferrer">
                  {source.name}
                </a>
              </li>
            ))}
          </ul>
          <p style={{ fontSize: 12, marginTop: 10 }}>
            Coleta feita com identificação no cabeçalho HTTP, ~5 requisições por segundo e cache
            local. Nada de raspagem de sites de emissoras.
          </p>
        </div>
      </div>

      <div className="back">
        <button type="button" className="btn btn-ghost" onClick={onHome}>
          ← Voltar
        </button>
      </div>
    </div>
  );
}
