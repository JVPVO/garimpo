import { Collar } from "../components/Collar.tsx";
import type { Dataset } from "../game/types.ts";
import { prettyDate, todayKey } from "../game/rng.ts";
import type { Store } from "../game/storage.ts";

type Props = {
  dataset: Dataset;
  store: Store;
  onDaily: () => void;
  onSeed: () => void;
  onLog: () => void;
  onMethod: () => void;
};

const SIGNALS = [
  { name: "pageviews", weight: 50, note: "atenção no verbete, 12 meses" },
  { name: "sitelinks", weight: 25, note: "quantas línguas têm verbete" },
  { name: "corpus", weight: 20, note: "frequência no texto em português" },
  { name: "gravidade", weight: 5, note: "população, quando é lugar" },
];

export function Home({ dataset, store, onDaily, onSeed, onLog, onMethod }: Props) {
  const today = todayKey();
  const done = store.dailyDone[today];
  const record = store.dives.reduce((best, dive) => Math.max(best, dive.depth), 0);
  const streak = store.streak.count;

  return (
    <div className="home">
      <div className="home-grid">
        <div className="home-main">
          <Collar />
          <h1 className="display">
            Sete respostas.
            <br />
            Uma mina.
          </h1>
          <p className="lede">
            Cada resposta desce o poço. Quanto mais rara, mais fundo — e a raridade é{" "}
            <strong>medida em dados</strong>, não em opinião.
          </p>

          <div className="actions">
            <button type="button" className="btn" onClick={onDaily}>
              {done ? "Descer de novo" : "Descer"}
              <span className="btn-meta">
                {done ? `hoje: ${done.depth} m` : "7 perguntas · 25 s cada"}
              </span>
            </button>
          </div>

          <div className="links">
            <span className="mono" style={{ color: "var(--iron)" }}>
              diário · {prettyDate(today)}
            </span>
            <button type="button" onClick={onSeed}>
              ilimitado
            </button>
            <button type="button" onClick={onLog}>
              arquivo ({store.dives.length})
            </button>
            <button type="button" onClick={onMethod}>
              como medimos
            </button>
          </div>

          <div className="meta-line">
            <span>pt.wikipedia · wikidata · wordfreq</span>
            <span>régua de 0 a 700 m</span>
          </div>
        </div>

        <aside className="home-card" aria-label="a régua usada no jogo">
          <p className="label" style={{ color: "var(--iron)" }}>
            a régua
          </p>
          <p className="home-card-lede">
            Quatro medidas públicas viram um posto percentual dentro do acervo de cada pergunta.
          </p>

          <ul className="home-signals">
            {SIGNALS.map((signal) => (
              <li key={signal.name}>
                <span className="n">{signal.name}</span>
                <span className="track">
                  <i style={{ width: `${signal.weight * 2}%` }} />
                </span>
                <span className="w">{signal.weight}%</span>
                <span className="note">{signal.note}</span>
              </li>
            ))}
          </ul>

          <div className="home-card-foot">
            <div>
              <b>{dataset.stats.prompts}</b>
              <span>perguntas</span>
            </div>
            <div>
              <b>{dataset.stats.uniqueAnswers.toLocaleString("pt-BR")}</b>
              <span>respostas</span>
            </div>
            <div>
              <b>{record ? `${record} m` : "—"}</b>
              <span>{streak > 1 ? `${streak} em sequência` : "seu recorde"}</span>
            </div>
          </div>

          <button type="button" className="home-card-link" onClick={onMethod}>
            ver a conta inteira →
          </button>
        </aside>
      </div>
    </div>
  );
}
