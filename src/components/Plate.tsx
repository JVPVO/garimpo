import { STRATA, stratumForDepth } from "../game/strata";

type Props = {
  depth?: number;
  shares?: number[];
  channel?: boolean;
  labels?: boolean;
  ticks?: boolean;
  dimBelow?: number | null;
  gemReached?: boolean;
};

/** The geological section: seven hatched bands, the depth axis, and the shaft. */
export function Plate({
  depth = 0,
  shares,
  channel = false,
  labels = true,
  ticks = true,
  dimBelow = null,
  gemReached = false,
}: Props) {
  const depthPct = Math.min(100, Math.max(0, (depth / 700) * 100));
  return (
    <div className="plate" aria-hidden="true">
      {STRATA.map((stratum, index) => {
        const top = (stratum.from / 700) * 100;
        const height = ((stratum.to - stratum.from) / 700) * 100;
        const dimmed = dimBelow !== null && stratum.from >= dimBelow;
        return (
          <div
            key={stratum.id}
            className="stratum"
            style={{
              top: `${top}%`,
              height: `${height}%`,
              ["--fill" as string]: stratum.fill,
              ["--hatch" as string]: stratum.hatch,
              opacity: dimmed ? 0.45 : 1,
            }}
            data-index={index}
          />
        );
      })}

      {channel && depth > 0 && (
        <>
          <div className="channel" style={{ height: `${depthPct}%` }} />
          <div className="pin" style={{ top: `${depthPct}%` }} />
        </>
      )}

      {ticks && (
        <div className="ticks">
          {Array.from({ length: 36 }, (_, index) => {
            const metres = index * 20;
            const major = metres % 100 === 0;
            return (
              <span
                key={metres}
                className={major ? "major" : undefined}
                style={{ top: `${(metres / 700) * 100}%` }}
              >
                {major && labels ? <b>{metres}</b> : null}
              </span>
            );
          })}
        </div>
      )}

      {labels && shares && (
        <div className="rail-labels">
          {STRATA.map((stratum, index) => {
            const middle = ((stratum.from + stratum.to) / 2 / 700) * 100;
            const top = Math.min(93, Math.max(7, middle));
            const narrow = ((stratum.to - stratum.from) / 700) * 100 < 6;
            return (
              <div
                key={stratum.id}
                className="rail-label"
                data-narrow={narrow}
                style={{ top: narrow ? `calc(${top}% - 2%)` : `${top}%` }}
              >
                <b>{stratum.label}</b>
                {stratum.fact}
                <br />
                {Math.round((shares[index] ?? 0) * 100)}% do acervo
              </div>
            );
          })}
        </div>
      )}

      <div className="plate-gem" style={{ opacity: gemReached ? 1 : 0.5 }}>
        <svg width="14" height="14" viewBox="0 0 64 64" aria-hidden="true">
          <path
            d="M32 6 L52 14 L58 32 L52 50 L32 58 L12 50 L6 32 L12 14 Z"
            fill={gemReached ? "#C9E6EA" : "none"}
            stroke={gemReached ? "#0E0B09" : "#423325"}
            strokeWidth="3"
          />
        </svg>
      </div>
      <div className="plate-keyline" />
      <div
        style={{
          position: "absolute",
          inset: 0,
          pointerEvents: "none",
          background: "linear-gradient(90deg, rgba(14,11,9,.35), transparent 38%)",
        }}
      />
      <div
        style={{
          position: "absolute",
          top: 0,
          bottom: 0,
          left: "50%",
          width: 1,
          background: "rgba(14,11,9,.35)",
        }}
      />
      <span hidden>{stratumForDepth(depth).label}</span>
    </div>
  );
}
