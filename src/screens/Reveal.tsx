import { useEffect, useRef } from "react";
import { PixelSprite } from "../art/PixelSprite.tsx";
import { MINERALS, TOOLS } from "../art/sprites.ts";
import { Counter } from "../components/Counter.tsx";
import { TIERS, styleScale, tierForRarity } from "../game/score.ts";
import { stratumForDepth } from "../game/strata.ts";
import type { Answer, Prompt, Round as RoundResult } from "../game/types.ts";

type Props = {
  prompt: Prompt;
  round: RoundResult;
  depthBefore: number;
  depthAfter: number;
  onNext: () => void;
  isLast: boolean;
};

/** Reads the measured rarity defensively: the field is what the build writes. */
function rarityOf(answer: Answer | null | undefined): number {
  if (!answer || !("rarity" in answer)) return 0;
  return Number(answer.rarity);
}

function formatViews(views: number | null): string {
  if (views === null) return "sem artigo";
  if (views <= 0) return "0/mês";
  if (views >= 1_000_000)
    return `${(views / 1_000_000).toLocaleString("pt-BR", { maximumFractionDigits: 1 })} M/mês`;
  if (views >= 1000)
    return `${(views / 1000).toLocaleString("pt-BR", { maximumFractionDigits: 1 })} mil/mês`;
  return `${views.toLocaleString("pt-BR")}/mês`;
}

function normalizer(prompt: Prompt, pick: (answer: Answer) => number) {
  const values = prompt.answers.map(pick);
  const min = Math.min(...values);
  const max = Math.max(...values);
  return (answer: Answer) => {
    if (max === min) return 0.5;
    return Math.min(1, Math.max(0.04, (pick(answer) - min) / (max - min)));
  };
}

export function Reveal({ prompt, round, depthBefore, depthAfter, onNext, isLast }: Props) {
  const matched = round.matched;
  const matchedRarity = rarityOf(matched);
  const tier = tierForRarity(matchedRarity);
  const nextButton = useRef<HTMLButtonElement | null>(null);
  useEffect(() => {
    nextButton.current?.focus({ preventScroll: true });
  }, []);
  const layer = stratumForDepth(Math.min(699, depthAfter));
  const popularityBars = normalizer(prompt, (answer) => Math.log10(1 + (answer.pv ?? 0)));
  const sitelinkBars = normalizer(prompt, (answer) => Math.log10(1 + answer.sl));
  const corpusBars = normalizer(prompt, (answer) => answer.wf);

  const signals = matched
    ? [
        { name: "atenção", value: formatViews(matched.pv), width: popularityBars(matched) },
        {
          name: "sitelinks",
          value: `${matched.sl} ${matched.sl === 1 ? "wiki" : "wikis"}`,
          width: sitelinkBars(matched),
        },
        { name: "corpus", value: `${matched.wf.toFixed(1)} zipf`, width: corpusBars(matched) },
      ]
    : [];

  return (
    <div className="round reveal panel">
      {matched ? (
        <div className="sheet">
          <p className="who">{round.timedOut ? "o tempo acabou" : "você"}</p>
          <p className="answer">{round.guess || "—"}</p>
          <p className="canonical">
            {matched.n !== round.guess ? `no acervo: ${matched.n}` : "no acervo"}
          </p>

          <hr />

          <div className="tier">
            <PixelSprite sprite={TOOLS[tier.tool].frames[0]} scale={2} title={tier.toolName} />
            <div>
              <h2>{tier.label}</h2>
              <p className="tier-layer">
                <PixelSprite sprite={MINERALS[layer.id].sprite} scale={1} /> cavou com{" "}
                {tier.toolName.toLowerCase()} · camada de{" "}
                {layer.label.charAt(0).toLowerCase() + layer.label.slice(1)}
              </p>
            </div>
            <div
              className="pval"
              title="p é o posto de raridade no acervo; a linha de baixo estima quantos jogadores dariam essa resposta."
            >
              <b>p {Math.round(matchedRarity * 100)}</b>
              <em>posto no acervo</em>
              <span>≈ {styleScale(matched.oneIn)}</span>
            </div>
          </div>

          <div className="signals" aria-label="sinais medidos">
            {signals.map((signal) => (
              <div className="signal" key={signal.name}>
                <em>{signal.name}</em>
                <span className="bar">
                  <i style={{ width: `${Math.round(signal.width * 100)}%` }} />
                </span>
                <span>{signal.value}</span>
              </div>
            ))}
          </div>

          <div className="tier-caps" aria-hidden="true">
            {TIERS.map((item) => (
              <i key={item.id} data-on={item.id <= tier.id} />
            ))}
          </div>
        </div>
      ) : (
        <div className="sheet">
          <p className="who">{round.timedOut ? "o tempo acabou" : "você"}</p>
          <p className="answer">{round.guess || "—"}</p>
          <p className="canonical">
            {round.timedOut ? "sem resposta" : "não está no acervo desta pergunta"}
          </p>
          <hr />
          <p className="compare" style={{ marginTop: 0 }}>
            {round.timedOut ? (
              <>
                O tempo acabou antes da sua resposta. Sem uma resposta do acervo, não há raridade
                para medir.
              </>
            ) : (
              <>
                O acervo cobre <b>{prompt.answers.length}</b> respostas possíveis. A sua ficou fora
                dele, então não dá para medir a raridade — e o jogo não inventa um número.
              </>
            )}
          </p>
        </div>
      )}

      <div className="reveal-foot">
        <div>
          <p className="label" style={{ color: "var(--iron)" }}>
            profundidade
          </p>
          <p
            className="display reveal-depth"
            style={{ fontSize: "var(--fs-h1)", color: "var(--lamp)" }}
          >
            {depthAfter !== depthBefore ? (
              <>
                <Counter value={depthBefore} />
                <span
                  className="mono"
                  style={{ fontSize: 24, color: "var(--ink-2)", margin: "0 6px" }}
                >
                  →
                </span>
              </>
            ) : null}
            <Counter key={depthAfter} value={depthAfter} />
            <span style={{ fontSize: 24 }}> m</span>
          </p>
        </div>
        <button
          ref={nextButton}
          type="button"
          className="btn"
          onClick={onNext}
          style={{ width: 240 }}
        >
          {isLast ? "Ver o poço" : "Próxima"}
          <span className="btn-meta">{isLast ? "resultado" : "enter"}</span>
        </button>
      </div>
    </div>
  );
}
