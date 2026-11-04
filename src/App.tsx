import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { MineAudio } from "./audio/engine.ts";
import { Plate } from "./components/Plate.tsx";
import { findAnswer } from "./game/match.ts";
import { dailySeed, prettyDate, selectPrompts, todayKey } from "./game/rng.ts";
import { dig, tierForDepth } from "./game/score.ts";
import { readStore, saveDive, writeStore, type Store } from "./game/storage.ts";
import { CATEGORY_LABEL, sharesFor } from "./game/strata.ts";
import type { Dataset, Dive, Prompt, Round as RoundResult } from "./game/types.ts";
import { Home } from "./screens/Home.tsx";
import { Log } from "./screens/Log.tsx";
import { Method } from "./screens/Method.tsx";
import { Result } from "./screens/Result.tsx";
import { Reveal } from "./screens/Reveal.tsx";
import { Round } from "./screens/Round.tsx";
import { Seed } from "./screens/Seed.tsx";

type Screen = "home" | "dive" | "result" | "log" | "method" | "seed";

type DiveConfig = {
  mode: "daily" | "unlimited";
  label: string;
  seed: number;
  userSeed?: number;
};

const HASH_SEED = /^#s=(\d{1,4})$/;

function clearHash() {
  if (window.location.hash) {
    window.history.replaceState(null, "", window.location.pathname + window.location.search);
  }
}

export default function App() {
  const [dataset, setDataset] = useState<Dataset | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [store, setStore] = useState<Store>(() => readStore());
  const [screen, setScreen] = useState<Screen>("home");
  const [config, setConfig] = useState<DiveConfig | null>(null);
  const [prompts, setPrompts] = useState<Prompt[]>([]);
  const [index, setIndex] = useState(0);
  const [rounds, setRounds] = useState<RoundResult[]>([]);
  const [revealed, setRevealed] = useState(false);
  const [result, setResult] = useState<Dive | null>(null);
  const audio = useRef(new MineAudio()).current;

  useEffect(() => {
    let alive = true;
    import("./game/load.ts")
      .then((module) => module.loadDataset())
      .then((data) => {
        if (alive) setDataset(data);
      })
      .catch((cause: Error) => {
        if (alive) setError(cause.message);
      });
    return () => {
      alive = false;
    };
  }, []);

  useEffect(() => {
    audio.setEnabled(store.sound);
  }, [audio, store.sound]);

  const depth = useMemo(() => Math.min(700, rounds.reduce((total, round) => total + round.meters, 0)), [rounds]);
  const depthBefore = useMemo(
    () => Math.min(700, rounds.slice(0, -1).reduce((total, round) => total + round.meters, 0)),
    [rounds],
  );
  const shares = useMemo(() => {
    if (!dataset) return [];
    const rarities: number[] = [];
    for (const prompt of dataset.prompts) {
      for (const answer of prompt.answers) rarities.push(answer.rarity);
    }
    return sharesFor(rarities);
  }, [dataset]);

  const begin = useCallback(
    (next: DiveConfig) => {
      if (!dataset) return;
      const selected = selectPrompts(dataset.prompts, next.seed, 7);
      setConfig(next);
      setPrompts(selected);
      setIndex(0);
      setRounds([]);
      setRevealed(false);
      setResult(null);
      setScreen("dive");
      if (next.mode === "daily") clearHash();
      else window.location.hash = `#s=${next.userSeed ?? next.seed}`;
      window.scrollTo({ top: 0 });
    },
    [dataset],
  );

  const startDaily = useCallback(() => {
    const today = todayKey();
    begin({ mode: "daily", label: prettyDate(today), seed: dailySeed(today) });
  }, [begin]);

  const startUnlimited = useCallback(
    (seed: number) => {
      begin({
        mode: "unlimited",
        label: `semente ${seed}`,
        seed: dailySeed(`s:${seed}`),
        userSeed: seed,
      });
    },
    [begin],
  );

  useEffect(() => {
    if (!dataset) return;
    const match = HASH_SEED.exec(window.location.hash);
    if (match) startUnlimited(Number(match[1]));
  }, [dataset, startUnlimited]);

  const onAnswer = useCallback(
    (value: string, timedOut: boolean) => {
      const prompt = prompts[index];
      if (!prompt) return;
      const match = findAnswer(value, prompt.answers);
      const meters = match ? dig(match.answer.rarity) : 0;
      const round: RoundResult = {
        prompt,
        guess: value,
        matched: match?.answer ?? null,
        meters,
        ms: 0,
        timedOut,
      };
      const nextRounds = [...rounds, round];
      setRounds(nextRounds);
      setRevealed(true);

      if (match) {
        audio.strike(match.answer.points);
        const tier = tierForDepth(
          Math.min(700, nextRounds.reduce((total, item) => total + item.meters, 0)),
        );
        audio.crumble(meters);
        if (tier.id >= 2) window.setTimeout(() => audio.gem(tier.id), 180);
      } else {
        audio.strike(1);
      }
    },
    [audio, index, prompts, rounds],
  );

  const finish = useCallback(
    (finalRounds: RoundResult[]) => {
      if (!config) return;
      const total = Math.min(700, finalRounds.reduce((sum, round) => sum + round.meters, 0));
      const dive: Dive = {
        id: `${config.mode}:${config.label}:${config.seed}`,
        mode: config.mode,
        label: config.label,
        date: todayKey(),
        seed: config.seed,
        depth: total,
        tier: tierForDepth(total).id,
        finishedAt: new Date().toISOString(),
        rounds: finalRounds.map((round) => ({
          promptId: round.prompt.id,
          prompt: round.prompt.text,
          guess: round.guess,
          name: round.matched?.n ?? null,
          p: round.matched ? round.matched.rarity : null,
          meters: round.meters,
          rank: round.matched?.rank ?? null,
          count: round.prompt.answers.length,
        })),
      };
      setStore(saveDive(dive));
      setResult(dive);
      setScreen("result");
      audio.bottom(total >= 700);
      window.scrollTo({ top: 0 });
    },
    [audio, config],
  );

  const next = useCallback(() => {
    if (index + 1 >= prompts.length) {
      finish(rounds);
      return;
    }
    setIndex(index + 1);
    setRevealed(false);
    window.scrollTo({ top: 0 });
  }, [finish, index, prompts.length, rounds]);

  useEffect(() => {
    if (screen !== "dive" || !revealed) return;
    const onKey = (event: KeyboardEvent) => {
      if (event.key === "Enter") {
        event.preventDefault();
        next();
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [next, revealed, screen]);

  const toggleSound = () => {
    const nextStore = { ...store, sound: !store.sound };
    setStore(nextStore);
    writeStore(nextStore);
  };

  const goHome = () => {
    setScreen("home");
    setRounds([]);
    setRevealed(false);
    clearHash();
  };

  const openDive = (dive: Dive) => {
    setResult(dive);
    setScreen("result");
  };

  if (error) {
    return (
      <div className="boot">
        <p className="label" style={{ color: "var(--lamp)" }}>
          sem sinal
        </p>
        <p style={{ color: "var(--ink-2)", maxWidth: 360 }}>
          O acervo não carregou ({error}). O jogo precisa do arquivo de dados em{" "}
          <code>public/data/garimpo.json</code>.
        </p>
        <button type="button" className="btn btn-ghost" onClick={() => window.location.reload()}>
          Tentar de novo
        </button>
      </div>
    );
  }

  if (!dataset) {
    return (
      <div className="boot">
        <p className="label" style={{ color: "var(--lamp)" }}>
          garimpo
        </p>
        <div className="bar">
          <i />
        </div>
        <p style={{ color: "var(--iron)", fontSize: 13 }}>abrindo o acervo</p>
      </div>
    );
  }

  const activePrompt = prompts[index];
  const currentRound = rounds[rounds.length - 1];

  return (
    <div className="app" data-screen={screen}>
      <aside className="rail" aria-hidden="true">
        {screen !== "result" && screen !== "method" && screen !== "log" ? (
          <div className="rail-inner">
            <Plate
              depth={screen === "dive" ? depth : 0}
              channel={screen === "dive"}
              shares={shares}
              labels
            />
          </div>
        ) : null}
      </aside>

      <header className="topbar">
        <button
          type="button"
          className="brand"
          onClick={goHome}
          style={{ background: "none", border: 0, padding: 0, cursor: "pointer", color: "var(--paper)" }}
        >
          Garimpo
        </button>
        <span className="quiet">
          {screen === "dive" && activePrompt
            ? `${config?.mode === "daily" ? config.label : config?.label} · pergunta ${index + 1}/7`
            : dataset.stats.prompts + " perguntas · 700 m"}
        </span>
        <span className="spacer" />
        <button
          type="button"
          className="icon-btn"
          onClick={toggleSound}
          aria-label={store.sound ? "desligar som" : "ligar som"}
          title={store.sound ? "desligar som" : "ligar som"}
        >
          {store.sound ? "◉" : "◌"}
        </button>
      </header>

      {screen === "home" && (
        <main className="stage">
          <Home
            dataset={dataset}
            store={store}
            onDaily={startDaily}
            onSeed={() => setScreen("seed")}
            onLog={() => setScreen("log")}
            onMethod={() => setScreen("method")}
          />
        </main>
      )}

      {screen === "seed" && (
        <main className="stage">
          <Seed onStart={startUnlimited} onHome={() => setScreen("home")} />
        </main>
      )}

      {screen === "dive" && activePrompt && (
        <>
          <main className="stage">
            {revealed && currentRound ? (
              <Reveal
                prompt={activePrompt}
                round={currentRound}
                depthBefore={depthBefore}
                depthAfter={depth}
                onNext={next}
                isLast={index + 1 >= prompts.length}
              />
            ) : (
              <Round
                key={activePrompt.id}
                prompt={activePrompt}
                index={index}
                total={prompts.length}
                depth={depth}
                done={rounds.map((_, i) => i)}
                audio={audio}
                onAnswer={onAnswer}
              />
            )}
          </main>

          <aside className="ledger">
            <h2>caderno</h2>
            <ol>
              {prompts.map((prompt, i) => {
                const round = rounds[i];
                return (
                  <li key={prompt.id} data-empty={!round}>
                    <span className="n">{i + 1}</span>
                    <span>{round?.matched ? "◈" : "◇"}</span>
                    <span style={{ overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                      {round ? (round.matched?.n ?? "fora do acervo") : CATEGORY_LABEL[prompt.cat] ?? prompt.cat}
                    </span>
                    <span className="m">{round ? `${round.meters} m` : "—"}</span>
                  </li>
                );
              })}
            </ol>
            <div className="total">
              <b>{depth} m</b>
              <span>profundidade</span>
            </div>
          </aside>
        </>
      )}

      {screen === "result" && result && (
        <main className="stage">
          <Result
            dive={result}
            dataset={dataset}
            onHome={goHome}
            onAgain={() =>
              begin({
                mode: result.mode,
                label: result.label,
                seed: result.seed,
                userSeed: result.mode === "unlimited"
                  ? Number(result.label.replace(/\D/g, "")) || undefined
                  : undefined,
              })
            }
            onLog={() => setScreen("log")}
            onMethod={() => setScreen("method")}
          />
        </main>
      )}

      {screen === "log" && (
        <main className="stage">
          <Log store={store} onOpen={openDive} onHome={goHome} />
        </main>
      )}

      {screen === "method" && (
        <main className="stage">
          <Method dataset={dataset} shares={shares} onHome={goHome} />
        </main>
      )}
    </div>
  );
}
