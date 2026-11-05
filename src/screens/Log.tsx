import { STRATA, stratumForDepth } from "../game/strata.ts";

const lowerFirst = (text: string) => text.charAt(0).toLowerCase() + text.slice(1);
import type { Dive } from "../game/types.ts";
import type { Store } from "../game/storage.ts";

type Props = {
  store: Store;
  onOpen: (dive: Dive) => void;
  onHome: () => void;
};

function MiniPlate({ depth }: { depth: number }) {
  return (
    <span className="mini-plate" aria-hidden="true">
      {STRATA.map((stratum) => (
        <i
          key={stratum.id}
          style={{
            top: `${(stratum.from / 700) * 100}%`,
            height: `${((stratum.to - stratum.from) / 700) * 100}%`,
            background: stratum.fill,
          }}
        />
      ))}
      <i
        style={{
          top: 0,
          height: `${(depth / 700) * 100}%`,
          width: 3,
          left: 8,
          background: "rgba(242,182,90,.65)",
        }}
      />
    </span>
  );
}

export function Log({ store, onOpen, onHome }: Props) {
  const dives = store.dives;
  return (
    <div className="stage-narrow panel" style={{ maxWidth: 900 }}>
      <div className="page-head">
        <h1>Arquivo</h1>
        <span className="quiet">
          {dives.length} {dives.length === 1 ? "poço" : "poços"}{" "}
          {store.streak.count > 1 ? ` · ${store.streak.count} em sequência` : ""}
        </span>
      </div>

      {dives.length === 0 ? (
        <div className="empty">
          <h1 className="display" style={{ fontSize: "var(--fs-h1)" }}>
            Nenhum poço
            <br />
            aberto.
          </h1>
          <p>
            Cada descida fica registrada aqui com a profundidade e as sete respostas que você deu.
          </p>
          <button type="button" className="btn" onClick={onHome} style={{ maxWidth: 320 }}>
            Descer
            <span className="btn-meta">7 perguntas</span>
          </button>
        </div>
      ) : (
        <ul className="log-list">
          {dives.map((dive) => (
            <li key={dive.id}>
              <button type="button" className="log-row" onClick={() => onOpen(dive)}>
                <MiniPlate depth={dive.depth} />
                <span className="when">
                  <b>{dive.label}</b>
                  {dive.mode === "daily" ? "diário" : "ilimitado"} ·{" "}
                  {lowerFirst(stratumForDepth(dive.depth).label)}
                </span>
                <span className="depth">{dive.depth} m</span>
                <span className="mono" style={{ fontSize: 11, color: "var(--iron)" }}>
                  {dive.rounds.length}/7
                </span>
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
