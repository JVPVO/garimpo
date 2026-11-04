import { useEffect, useRef, useState } from "react";
import type { MineAudio } from "../audio/engine.ts";
import { findAnswer, findSuggestion, key as matchKey } from "../game/match.ts";
import { stratumForDepth } from "../game/strata.ts";
import type { Prompt } from "../game/types.ts";

const SECONDS = 25;

type Props = {
  prompt: Prompt;
  index: number;
  total: number;
  depth: number;
  done: number[];
  audio: MineAudio;
  onAnswer: (value: string, timedOut: boolean) => void;
};

export function Round({ prompt, index, total, depth, done, audio, onAnswer }: Props) {
  const [value, setValue] = useState("");
  const [suggestion, setSuggestion] = useState<{ raw: string; name: string } | null>(null);
  const [rejected, setRejected] = useState<{ text: string; count: number } | null>(null);
  const [seconds, setSeconds] = useState(SECONDS);
  const [urgent, setUrgent] = useState(false);
  const bar = useRef<HTMLElement | null>(null);
  const input = useRef<HTMLInputElement | null>(null);
  const answered = useRef(false);
  const latest = useRef("");

  useEffect(() => {
    answered.current = false;
    latest.current = "";
    setSuggestion(null);
    setRejected(null);
    input.current?.focus();
  }, [prompt.id]);

  useEffect(() => {
    const finish = () => {
      if (answered.current) return;
      answered.current = true;
      onAnswer(latest.current.trim(), true);
    };

    const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    const start = performance.now();
    let frame = 0;
    let lastSecond = SECONDS;
    const step = (now: number) => {
      const elapsed = (now - start) / 1000;
      const left = Math.max(0, SECONDS - elapsed);
      if (bar.current) {
        bar.current.style.transform = `scaleX(${left / SECONDS})`;
      }
      const second = Math.ceil(left);
      if (second !== lastSecond) {
        lastSecond = second;
        setSeconds(second);
        if (second <= 6 && second > 0) audio.tick();
      }
      setUrgent(left <= 7);
      if (left <= 0) {
        finish();
        return;
      }
      if (!reduce) frame = requestAnimationFrame(step);
    };
    frame = requestAnimationFrame(step);
    if (reduce) {
      const interval = window.setInterval(() => {
        const left = Math.max(0, SECONDS - (performance.now() - start) / 1000);
        if (bar.current) barRef(bar.current, left);
        if (left <= 0) finish();
      }, 500);
      return () => window.clearInterval(interval);
    }
    return () => cancelAnimationFrame(frame);
  }, [prompt.id, onAnswer, audio]);

  const commit = (text: string) => {
    answered.current = true;
    onAnswer(text, false);
  };

  /**
   * First press on a fuzzy/alias answer corrects the field and asks for a second
   * press; an exact answer goes straight through.
   */
  const suggest = (name: string, raw: string) => {
    setSuggestion({ raw, name });
    setValue(name);
    latest.current = name;
    audio.tick();
    input.current?.focus();
    input.current?.select();
  };

  const submit = () => {
    if (answered.current) return;
    const typed = value.trim();
    if (!typed) return;

    // Uma correção pendente: o segundo envio confirma.
    if (suggestion) {
      commit(typed);
      return;
    }

    const match = findAnswer(typed, prompt.answers);
    if (match) {
      if (matchKey(typed) !== matchKey(match.answer.n)) {
        suggest(match.answer.n, typed);
        return;
      }
      commit(typed);
      return;
    }

    const hint = findSuggestion(typed, prompt.answers);
    if (hint) {
      suggest(hint.answer.n, typed);
      return;
    }

    // Fora do acervo não encerra a pergunta: avisa e deixa tentar de novo.
    setRejected({ text: typed, count: (rejected?.count ?? 0) + 1 });
    setValue("");
    latest.current = "";
    audio.strike(1);
    input.current?.focus();
  };

  const change = (next: string) => {
    setValue(next);
    latest.current = next;
    if (suggestion) setSuggestion(null);
    if (rejected) setRejected(null);
  };

  const stratum = stratumForDepth(depth);
  const band = `${stratum.label} · ${depth} m`;

  return (
    <div className="round panel panel-round">
      <div className="wick" data-urgent={urgent}>
        <i ref={bar} style={{ transform: `scaleX(${seconds / SECONDS})` }} />
      </div>

      <div className="round-head">
        <span className="label" style={{ color: "var(--iron)" }}>
          pergunta {index + 1}/{total}
        </span>
        <span
          className="mono"
          style={{
            fontSize: 15,
            color: urgent ? "var(--paper)" : "var(--ink-2)",
            fontWeight: urgent ? 600 : 400,
          }}
        >
          {`0:${String(seconds).padStart(2, "0")}`}
        </span>
      </div>

      <div className="ledger-inline" aria-hidden="true">
        {Array.from({ length: total }, (_, i) => (
          <i key={i} data-done={done.includes(i)} />
        ))}
      </div>

      <p className="stratum-tag">{band}</p>
      <h1 className="prompt">{prompt.text}</h1>

      <label className="field-label" htmlFor="answer" hidden>
        Sua resposta
      </label>
      <input
        id="answer"
        ref={input}
        className="field"
        type="text"
        value={value}
        onChange={(event) => change(event.target.value)}
        onKeyDown={(event) => {
          if (event.key === "Enter") {
            event.preventDefault();
            event.stopPropagation();
            submit();
          }
        }}
        placeholder="sua resposta"
        autoComplete="off"
        autoCorrect="off"
        autoCapitalize="off"
        spellCheck={false}
        enterKeyHint="go"
        aria-describedby="field-hint"
      />

      {suggestion ? (
        <div className="correction" id="field-hint" role="status" aria-live="polite">
          <span className="correction-label">você quis dizer</span>
          <b>
            {suggestion.raw.toLowerCase() !== suggestion.name.toLowerCase()
              ? `“${suggestion.raw}” → ${suggestion.name}`
              : suggestion.name}
          </b>
          <span className="correction-note">envie de novo para confirmar · ou edite</span>
          <button type="button" className="correction-go" onClick={() => commit(value.trim())}>
            enviar
          </button>
        </div>
      ) : rejected ? (
        <div className="rejected" id="field-hint" role="status" aria-live="polite">
          <span>“{rejected.text}” não está no acervo.</span>
          <b>Tente outra — o tempo continua.</b>
          <em>
            {rejected.count} tentativa{rejected.count > 1 ? "s" : ""}
          </em>
        </div>
      ) : (
        <div className="field-hint" id="field-hint">
          <span>enter para cravar</span>
          <span>{prompt.answers.length} respostas no acervo</span>
        </div>
      )}

      <button
        type="button"
        className="btn"
        onClick={submit}
        disabled={!value.trim()}
        data-corrected={Boolean(suggestion)}
        style={{ marginTop: 20 }}
      >
        {suggestion ? "Enviar" : "Cravar"}
        <span className="btn-meta">{suggestion ? "resposta corrigida" : "desce o poço"}</span>
      </button>
    </div>
  );
}

function barRef(element: HTMLElement, left: number) {
  element.style.transform = `scaleX(${left / SECONDS})`;
}
