import { memo, useEffect, useRef, useState } from "react";
import { PixelSprite } from "../art/PixelSprite.tsx";
import {
  CART,
  HEADFRAME,
  LANTERN,
  MANDACARU,
  MINER,
  MINERALS,
  MOON,
  TOOLS,
  type MineralId,
  type ToolId,
} from "../art/sprites.ts";
import { STRATA, stratumForDepth } from "../game/strata.ts";

/**
 * The whole site sits on this: a pixel-art cross-section of one mine, from the
 * night sky down to 700 m. It is fixed behind the UI; a single "track" element
 * holds the world and only its translateY moves (the camera). During a dig the
 * hole, the tool and the depth tag are written straight to the DOM from a rAF
 * loop, so React never re-renders the world while it animates.
 */

/** Pixels per metre of shaft. 700 m → 7 000 px of rock. */
const PX = 10;
/** Sky above the surface line, in px. */
const SKY = 640;
const MAX = 700;
const WORLD = SKY + MAX * PX + 260;

export type WorldMode = "surface" | "round" | "dig" | "reveal" | "result";

export type WorldMark = {
  /** Cumulative depth after this answer, in metres. */
  at: number;
  index: number;
  label: string;
  meters: number;
  tier: number;
};

type Props = {
  mode: WorldMode;
  /** Depth the shaft should end at. A deeper value in a dive mode triggers a dig. */
  depth: number;
  tool: ToolId;
  /** The app's dig flag; turning it off mid-animation skips to the end. */
  digging: boolean;
  marks: WorldMark[];
  /** Called once when a dig animation starts, with its real total duration. */
  onDigStart?: (durationMs: number) => void;
  /** Called when the dig finished (also right away when nothing moved). */
  onDigEnd?: () => void;
};

/** Timing of one dig. Bigger digs take longer, but never drag. */
function digTiming(metres: number) {
  const windUp = 250;
  const travel = Math.min(1600, 500 + metres * 10);
  const settle = 260;
  return { windUp, travel, settle, total: windUp + travel + settle };
}

const ACCENT: Record<MineralId, string> = {
  carvao: "#5a5350",
  ferro: "#a65a44",
  bauxita: "#c47c45",
  cobre: "#d4834f",
  ouro: "#f2b65a",
  esmeralda: "#3fae78",
  turmalina: "#2fd4c8",
  rubi: "#d8344f",
  diamante: "#d3eef2",
};

function rng(seed: number) {
  let s = seed;
  return () => {
    s = (s * 1103515245 + 12345) & 0x7fffffff;
    return s / 0x7fffffff;
  };
}

/** A pixel speck tile for one band: dark pits, light grit, a few ore-coloured flecks. */
function speckTile(accent: string, seed: number): string {
  const rand = rng(seed);
  const size = 40;
  let rects = "";
  for (let i = 0; i < 26; i++) {
    const x = Math.floor(rand() * size);
    const y = Math.floor(rand() * size);
    const roll = rand();
    const fill = roll < 0.5 ? "rgba(0,0,0,.32)" : roll < 0.86 ? "rgba(255,240,220,.07)" : accent;
    const w = roll < 0.5 && rand() > 0.5 ? 2 : 1;
    const op = roll >= 0.86 ? ' opacity=".55"' : "";
    rects += `<rect x="${x}" y="${y}" width="${w}" height="1" fill="${fill}"${op}/>`;
  }
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="${size}" height="${size}" shape-rendering="crispEdges">${rects}</svg>`;
  return `url("data:image/svg+xml,${encodeURIComponent(svg)}")`;
}

/** Deterministic stars as one box-shadow list (2 px squares). */
function starField(count: number, seed: number): string {
  const rand = rng(seed);
  const shadows: string[] = [];
  for (let i = 0; i < count; i++) {
    const x = (rand() * 100).toFixed(2);
    const y = Math.round(rand() * (SKY - 220));
    const bright = rand() > 0.8;
    shadows.push(`${x}vw ${y}px 0 0 ${bright ? "#fff4d6" : "rgba(234,223,198,.55)"}`);
  }
  return shadows.join(",");
}

type Chunk = {
  id: string;
  side: "l" | "r";
  x: number;
  y: number;
  mineral: MineralId;
  flip: boolean;
};

function makeOre(): Chunk[] {
  const rand = rng(11);
  const chunks: Chunk[] = [];
  for (const band of STRATA) {
    const top = SKY + band.from * PX;
    const height = (band.to - band.from) * PX;
    const count = Math.max(3, Math.round(height / 90));
    for (let i = 0; i < count; i++) {
      chunks.push({
        id: `${band.id}-${i}`,
        side: i % 2 ? "r" : "l",
        x: rand(),
        y: top + 40 + rand() * Math.max(10, height - 80),
        mineral: band.id,
        flip: rand() > 0.5,
      });
    }
  }
  return chunks;
}

/** Everything that never changes after mount: sky, strata, ore, ticks, lanterns. */
const ORE = makeOre();
const TILES = STRATA.map((band, index) => speckTile(ACCENT[band.id], 31 + index * 7));
const STARS = starField(90, 5);
const STARS_B = starField(40, 17);

const Scenery = memo(function Scenery() {
  const ore = ORE;
  const tiles = TILES;
  const stars = STARS;
  const stars2 = STARS_B;

  return (
    <>
      <div className="w-sky" style={{ height: SKY }}>
        <i className="w-stars" style={{ boxShadow: stars }} />
        <i className="w-stars w-stars-b" style={{ boxShadow: stars2 }} />
        <div className="w-moon">
          <PixelSprite sprite={MOON} scale={4} />
        </div>
        <i className="w-cloud" style={{ ["--cy" as string]: "120px", ["--cd" as string]: "90s" }} />
        <i
          className="w-cloud w-cloud-b"
          style={{ ["--cy" as string]: "230px", ["--cd" as string]: "140s" }}
        />
        <i className="w-hills w-hills-far" />
        <i className="w-hills w-hills-near" />

        <div className="w-prop w-cactus-a">
          <PixelSprite sprite={MANDACARU} scale={4} />
        </div>
        <div className="w-prop w-cactus-b">
          <PixelSprite sprite={MANDACARU} scale={3} />
        </div>
        <i className="w-rails" />
        <div className="w-prop w-cart">
          <PixelSprite sprite={CART} scale={3} />
        </div>
        <div className="w-prop w-headframe">
          <PixelSprite sprite={HEADFRAME} scale={4} />
        </div>
        <div className="w-prop w-miner">
          <PixelSprite sprite={MINER[0]} scale={3} className="f0" />
          <PixelSprite sprite={MINER[1]} scale={3} className="f1" />
        </div>
      </div>

      <i className="w-grass" style={{ top: SKY - 6 }} />

      {STRATA.map((band, index) => (
        <div
          key={band.id}
          className="w-band"
          data-band={band.id}
          style={{
            top: SKY + band.from * PX,
            height: (band.to - band.from) * PX,
            ["--fill" as string]: band.fill,
            ["--tile" as string]: tiles[index],
            ["--accent" as string]: ACCENT[band.id],
          }}
        >
          <div className="w-caption" data-side={index % 2 ? "r" : "l"}>
            <b>
              <PixelSprite sprite={MINERALS[band.id].sprite} scale={2} />
              {band.from} m · {band.label}
            </b>
            <span>{band.fact}</span>
          </div>
        </div>
      ))}

      {ore.map((chunk) => (
        <div
          key={chunk.id}
          className="w-ore"
          data-side={chunk.side}
          style={{
            top: chunk.y,
            ["--x" as string]: chunk.x,
            transform: chunk.flip ? "scaleX(-1)" : undefined,
          }}
        >
          <PixelSprite sprite={MINERALS[chunk.mineral].sprite} scale={3} />
        </div>
      ))}

      <i className="w-ruler" style={{ top: SKY, height: MAX * PX }} />
      {Array.from({ length: 15 }, (_, i) => i * 50).map((m) => (
        <span key={m} className="w-tick" style={{ top: SKY + m * PX }}>
          {m} m
        </span>
      ))}

      {Array.from({ length: 12 }, (_, i) => 30 + i * 58).map((m, i) => (
        <div
          key={m}
          className="w-lantern"
          data-side={i % 2 ? "r" : "l"}
          style={{ top: SKY + m * PX }}
        >
          <PixelSprite sprite={LANTERN} scale={3} />
        </div>
      ))}

      <div className="w-floor" style={{ top: SKY + MAX * PX }}>
        <b>700 m · fundo do poço</b>
      </div>
    </>
  );
});

/** The digging tool; both frames are drawn and CSS alternates them. */
const Digger = memo(function Digger({ tool }: { tool: ToolId }) {
  const frames = TOOLS[tool].frames;
  return (
    <>
      <PixelSprite sprite={frames[0]} scale={3} className="f0" />
      <PixelSprite sprite={frames[1]} scale={3} className="f1" />
    </>
  );
});

export function World({ mode, depth, tool, digging, marks, onDigStart, onDigEnd }: Props) {
  const track = useRef<HTMLDivElement | null>(null);
  const hole = useRef<HTMLDivElement | null>(null);
  const face = useRef<HTMLDivElement | null>(null);
  const tagM = useRef<HTMLElement | null>(null);
  const tagLayer = useRef<HTMLElement | null>(null);
  const gauge = useRef<HTMLElement | null>(null);
  const shown = useRef(0);
  const anim = useRef<{ raf: number; to: number } | null>(null);
  const [active, setActive] = useState(false);

  const startRef = useRef(onDigStart);
  const endRef = useRef(onDigEnd);
  useEffect(() => {
    startRef.current = onDigStart;
    endRef.current = onDigEnd;
  }, [onDigStart, onDigEnd]);

  const kind = mode === "result" ? "result" : mode === "surface" ? "surface" : "dive";

  /** Writes the shaft (hole, face, tag, gauge) for a depth in metres. */
  const paintShaft = (metres: number) => {
    shown.current = metres;
    const y = metres * PX;
    if (hole.current) hole.current.style.height = `${y + 8}px`;
    if (face.current) face.current.style.transform = `translate3d(0, ${y}px, 0)`;
    const whole = Math.round(metres);
    if (tagM.current) tagM.current.textContent = `${whole} m`;
    if (tagLayer.current)
      tagLayer.current.textContent = stratumForDepth(Math.min(699, whole)).label;
    if (gauge.current) gauge.current.style.top = `${(metres / MAX) * 100}%`;
  };
  /** Moves the camera so `y` px of the world sits on the focus line. */
  const paintCamera = (y: number) => {
    track.current?.style.setProperty("--cam", `${y}px`);
  };

  // Digs, jumps and the result fly-over.
  useEffect(() => {
    const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    const from = shown.current;
    const to = Math.min(MAX, depth);

    if (kind === "surface") {
      paintShaft(to);
      paintCamera(SKY + Math.min(window.scrollY * 0.55, MAX * PX * 0.6));
      return;
    }

    if (kind === "result") {
      paintShaft(to);
      const target = SKY + to * PX;
      if (reduce) {
        paintCamera(target);
        return;
      }
      // Fly down the finished shaft once, past every plaque.
      const start = performance.now();
      const length = Math.min(2600, 900 + to * 2.4);
      const origin = SKY - 160;
      let raf = 0;
      const step = (now: number) => {
        const k = Math.min(1, (now - start) / length);
        const eased = k < 0.5 ? 2 * k * k : 1 - Math.pow(-2 * k + 2, 2) / 2;
        paintCamera(origin + (target - origin) * eased);
        if (k < 1) raf = requestAnimationFrame(step);
      };
      raf = requestAnimationFrame(step);
      return () => cancelAnimationFrame(raf);
    }

    // Dive.
    if (from === to) {
      paintShaft(to);
      paintCamera(SKY + to * PX);
      endRef.current?.();
      return;
    }
    if (to < from || reduce) {
      paintShaft(to);
      paintCamera(SKY + to * PX);
      const timer = window.setTimeout(() => endRef.current?.(), reduce && to > from ? 500 : 0);
      return () => window.clearTimeout(timer);
    }

    const { windUp, travel, total } = digTiming(to - from);
    const start = performance.now();
    const ease = (t: number) => 1 - Math.pow(1 - t, 3);
    setActive(true);
    startRef.current?.(total);
    const step = (now: number) => {
      const t = now - start;
      if (t >= windUp) {
        const k = Math.min(1, (t - windUp) / travel);
        const value = from + (to - from) * ease(k);
        paintShaft(value);
        paintCamera(SKY + value * PX);
      }
      if (t < total) {
        anim.current = { raf: requestAnimationFrame(step), to };
      } else {
        anim.current = null;
        paintShaft(to);
        paintCamera(SKY + to * PX);
        setActive(false);
        endRef.current?.();
      }
    };
    anim.current = { raf: requestAnimationFrame(step), to };
    return () => {
      // Stopping mid-dig keeps the current depth, so a re-run continues from here.
      if (anim.current) cancelAnimationFrame(anim.current.raf);
      anim.current = null;
      setActive(false);
    };
  }, [depth, kind]);

  // Skip: the app dropped its dig flag while the shaft was still moving.
  useEffect(() => {
    if (digging || !anim.current) return;
    const { raf, to } = anim.current;
    cancelAnimationFrame(raf);
    anim.current = null;
    paintShaft(to);
    paintCamera(SKY + to * PX);
    setActive(false);
  }, [digging]);

  // At the surface the camera follows the page scroll a little (parallax descent).
  useEffect(() => {
    if (kind !== "surface") return;
    let raf = 0;
    const onScroll = () => {
      cancelAnimationFrame(raf);
      raf = requestAnimationFrame(() =>
        paintCamera(SKY + Math.min(window.scrollY * 0.55, MAX * PX * 0.6)),
      );
    };
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => {
      window.removeEventListener("scroll", onScroll);
      cancelAnimationFrame(raf);
    };
  }, [kind]);

  const toolName = TOOLS[tool].name;

  return (
    <div className="world" data-mode={mode} data-active={active} aria-hidden="true">
      <div className="world-track" ref={track} style={{ height: WORLD }}>
        <Scenery />

        <div className="w-hole" ref={hole} style={{ top: SKY - 8 }}>
          <i className="w-cable" />
        </div>

        {marks.map((mark) => (
          <div
            key={mark.index}
            className="w-mark"
            data-side={mark.index % 2 ? "l" : "r"}
            data-tier={mark.tier}
            style={{ top: SKY + mark.at * PX }}
          >
            <b>{mark.index + 1}</b>
            <span>{mark.label}</span>
            <em>+{mark.meters} m</em>
          </div>
        ))}

        <div className="w-face" ref={face} style={{ top: SKY }}>
          <i className="w-glow" />
          {kind !== "surface" && (
            <div className="w-digger" data-tool={tool}>
              <Digger tool={tool} />
            </div>
          )}
          {active && (
            <div className="w-dirt">
              {Array.from({ length: 10 }, (_, i) => (
                <i key={i} style={{ ["--i" as string]: i }} />
              ))}
            </div>
          )}
          {kind !== "surface" && (
            <div className="w-tag">
              <b ref={tagM}>0 m</b>
              <span ref={tagLayer}>Carvão</span>
              {active ? <em>{toolName} cavando</em> : null}
            </div>
          )}
        </div>
      </div>

      <div className="w-gauge" data-show={kind !== "surface"}>
        {STRATA.map((band) => (
          <i
            key={band.id}
            style={{
              top: `${(band.from / MAX) * 100}%`,
              height: `${((band.to - band.from) / MAX) * 100}%`,
              background: ACCENT[band.id],
            }}
          />
        ))}
        <b ref={gauge} />
      </div>
      <i className="world-vignette" />
    </div>
  );
}
