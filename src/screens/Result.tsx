import { useState } from "react";
import { Gem } from "../components/Gem.tsx";
import { TIERS, dig, tierForDepth } from "../game/score.ts";
import { STRATA, stratumForDepth } from "../game/strata.ts";
import type { Answer, Dataset, Dive } from "../game/types.ts";

type Props = {
  dive: Dive;
  dataset: Dataset;
  onHome: () => void;
  onAgain: () => void;
  onLog: () => void;
  onMethod: () => void;
};

type Mark = Dive["rounds"][number] & { at: number };

function poolFor(dataset: Dataset, text: string): Answer[] {
  return dataset.prompts.find((prompt) => prompt.text === text)?.answers ?? [];
}

function withDepths(dive: Dive): Mark[] {
  let cumulative = 0;
  return dive.rounds.map((round) => {
    cumulative += round.meters;
    return { ...round, at: Math.min(700, cumulative) };
  });
}

function ResultPlate({ dive, marks }: { dive: Dive; marks: Mark[] }) {
  const reached = Math.min(700, dive.depth);

  return (
    <div className="result-plate" aria-hidden="true">
      {STRATA.map((stratum) => {
        const top = (stratum.from / 700) * 100;
        const height = ((stratum.to - stratum.from) / 700) * 100;
        return (
          <div
            key={stratum.id}
            className="stratum"
            style={{
              top: `${top}%`,
              height: `${height}%`,
              ["--fill" as string]: stratum.fill,
              ["--hatch" as string]: stratum.hatch,
              opacity: stratum.from >= reached ? 0.45 : 1,
            }}
          />
        );
      })}

      <div className="shaft">
        <div className="shaft-fill" style={{ height: `${(reached / 700) * 100}%` }} />
        {marks.map((mark, index) => (
          <div key={mark.promptId} className="mark" style={{ top: `${(mark.at / 700) * 100}%` }}>
            <i />
            <b>{index + 1}</b>
          </div>
        ))}
      </div>

      <div className="depth-col">
        {[0, 100, 200, 300, 400, 500, 600, 700].map((metres) => (
          <b key={metres} style={{ top: `${(metres / 700) * 100}%` }}>
            {metres === 700 ? "700 m" : metres}
          </b>
        ))}
      </div>

      <div className="strata-names">
        {STRATA.map((stratum) => {
          const middle = ((stratum.from + stratum.to) / 2 / 700) * 100;
          const thin = ((stratum.to - stratum.from) / 700) * 100 < 6;
          if (thin) return null;
          const top = Math.min(94, Math.max(6, middle));
          return (
            <div key={stratum.id} style={{ top: `${top}%` }}>
              <b>{stratum.label}</b>
              {stratum.fact}
            </div>
          );
        })}
      </div>

      <div className="floor" />
    </div>
  );
}

export function Result({ dive, dataset, onHome, onAgain, onLog, onMethod }: Props) {
  const [copied, setCopied] = useState(false);
  const marks = withDepths(dive);
  const tier = tierForDepth(dive.depth);
  // A gem is what the shaft is cutting through at that depth, not a separate scale.
  const gems = marks.filter((mark) => tierForDepth(mark.at).id >= 3).length;
  const stratum = stratumForDepth(dive.depth);

  const share = async () => {
    const text = [
      `Garimpo · ${dive.label} · ${dive.depth} m`,
      ...dive.rounds.map((round, index) => `${index + 1}. ${round.prompt} — ${round.name ?? (round.guess || "—")} (${round.meters} m)`),
      "sete respostas, uma mina.",
    ].join("\n");
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 2200);
    } catch {
      setCopied(false);
    }
  };

  return (
    <div className="result">
      <ResultPlate dive={dive} marks={marks} />

      <div className="result-body">
        <div>
          <h1 className="result-headline display">
            <small>
              {dive.mode === "daily" ? "diário" : "ilimitado"} · {dive.label}
            </small>
            {dive.depth >= 700 ? "Fundo do poço." : `${dive.depth} metros.`}
          </h1>
          <div className="tier-ticks" aria-label={`${tier.mineral}, ${tier.cut}`}>
            {TIERS.map((item) => (
              <i key={item.id} data-on={item.id <= tier.id} />
            ))}
            <span className="mono" style={{ fontSize: 12, color: "var(--ink-2)", marginLeft: 6 }}>
              {tier.mineral} · {stratum.label.toLowerCase()}
            </span>
          </div>

          <p style={{ color: "var(--ink-2)", marginTop: 18, maxWidth: "46ch" }}>
            {gems > 0
              ? `${gems} ${gems === 1 ? "gema" : "gemas"} no caminho. Você parou no ${stratum.label.toLowerCase()} — ${stratum.fact}.`
              : `Nenhuma gema no caminho. Você parou no ${stratum.label.toLowerCase()} — ${stratum.fact}. As respostas óbvias descem pouco.`}
          </p>

          <div className="result-actions">
            <button type="button" className="btn" onClick={onAgain}>
              Descer de novo
              <span className="btn-meta">mesmas perguntas</span>
            </button>
            <button type="button" className="btn btn-ghost" onClick={onLog}>
              Arquivo
            </button>
            <button type="button" className="btn btn-ghost" onClick={share}>
              {copied ? "Copiado" : "Copiar"}
            </button>
            <button type="button" className="btn btn-ghost" onClick={onMethod}>
              Como medimos
            </button>
            <button type="button" className="btn btn-ghost" onClick={onHome}>
              Início
            </button>
          </div>
        </div>

        <ol className="rounds">
          {marks.map((round, index) => (
            <li key={round.promptId} data-miss={!round.name}>
              <span className="idx">{String(index + 1).padStart(2, "0")}</span>
              <span className="said">
                <span style={{ display: "block", fontSize: 12, color: "var(--iron)" }}>{round.prompt}</span>
                <b>{round.name ?? round.guess ?? "em branco"}</b>
                {round.p !== null ? (
                  <span className="mono" style={{ fontSize: 11, color: "var(--iron)", marginLeft: 8 }}>
                    p {Math.round(round.p * 100)}
                  </span>
                ) : null}
              </span>
              <span className="meters">
                {round.meters} m <Gem tier={tierForDepth(round.at).id} size={14} />
              </span>
            </li>
          ))}
        </ol>
      </div>

      <section className="overview" aria-label="o acervo de cada pergunta">
        <div className="overview-head">
          <h2>o acervo de cada pergunta</h2>
          <p>
            Todas as respostas aceitas de cada pergunta, da que mais desce para a mais óbvia. O que
            você respondeu aparece marcado.
          </p>
        </div>

        <div className="overview-grid">
          {marks.map((mark, index) => {
            const pool = poolFor(dataset, mark.prompt);
            const rarest = [...pool].sort((a, b) => b.rarity - a.rarity).slice(0, 8);
            const obvious = pool.find((answer) => answer.rank === 1);
            const position = mark.rank ? mark.count - mark.rank + 1 : null;
            return (
              <details key={mark.promptId} className="ov" data-miss={!mark.name}>
                <summary>
                  <span className="ov-idx">{String(index + 1).padStart(2, "0")}</span>
                  <span className="ov-prompt">{mark.prompt}</span>
                  <span className="ov-you">{mark.name ?? "fora do acervo"}</span>
                  <span className="ov-meta">
                    {mark.meters} m · {mark.count} respostas
                  </span>
                </summary>
                <div className="ov-body">
                  <p className="ov-line">
                    <span>sua posição</span>
                    <b>
                      {position
                        ? `${position}º mais rara de ${mark.count}`
                        : mark.name
                          ? "sem posição"
                          : "não medida"}
                    </b>
                  </p>
                  <p className="ov-sub">as que mais descem</p>
                  <ul>
                    {rarest.map((answer) => (
                      <li key={answer.n} data-you={answer.n === mark.name}>
                        <span>{answer.n}</span>
                        <span className="mono">{dig(answer.rarity)} m</span>
                      </li>
                    ))}
                  </ul>
                  {obvious ? (
                    <p className="ov-line ov-obvious">
                      <span>a mais óbvia</span>
                      <b>
                        {obvious.n} · {dig(obvious.rarity)} m
                      </b>
                    </p>
                  ) : null}
                </div>
              </details>
            );
          })}
        </div>
      </section>
    </div>
  );
}
