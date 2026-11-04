import { useState } from "react";

type Props = {
  onStart: (seed: number) => void;
  onHome: () => void;
};

const SUGGESTIONS = [7, 51, 404, 1024, 8842];

export function Seed({ onStart, onHome }: Props) {
  const [value, setValue] = useState("");

  const start = (seed: number) => {
    if (!Number.isFinite(seed)) return;
    const clamped = Math.min(9999, Math.max(1, Math.round(seed)));
    onStart(clamped);
  };

  return (
    <div className="stage-narrow">
      <div className="page-head">
        <h1>Ilimitado</h1>
        <span className="quiet">mesma semente, mesmas sete perguntas</span>
      </div>

      <p style={{ color: "var(--ink-2)", maxWidth: "44ch", marginBottom: 24 }}>
        Escolha um número de 1 a 9999. Ele não muda as regras, só a ordem das perguntas — o mesmo
        número sempre traz a mesma mina.
      </p>

      <div className="seedbox">
        <div className="row">
          <input
            value={value}
            onChange={(event) => setValue(event.target.value.replace(/\D/g, "").slice(0, 4))}
            onKeyDown={(event) => {
              if (event.key === "Enter") start(Number(value));
            }}
            inputMode="numeric"
            placeholder="8842"
            aria-label="número da semente"
          />
          <button type="button" className="btn" onClick={() => start(Number(value) || 1)} style={{ width: 180 }}>
            Descer
            <span className="btn-meta">semente</span>
          </button>
        </div>

        <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
          {SUGGESTIONS.map((seed) => (
            <button key={seed} type="button" className="chip" onClick={() => start(seed)}>
              #{seed}
            </button>
          ))}
        </div>

        <div style={{ marginTop: 10 }}>
          <button type="button" className="btn btn-ghost" onClick={onHome}>
            ← Início
          </button>
        </div>
      </div>
    </div>
  );
}
