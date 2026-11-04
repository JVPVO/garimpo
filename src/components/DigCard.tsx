import { useEffect, useRef, useState } from "react";
import { PixelSprite } from "../art/PixelSprite.tsx";
import { TOOLS } from "../art/sprites.ts";
import { TIERS, tierForRarity } from "../game/score.ts";
import type { Round } from "../game/types.ts";

type Props = {
  round: Round;
  onSkip: () => void;
};

/** Shown in the stage while the shaft digs: which machine, how far. */
export function DigCard({ round, onSkip }: Props) {
  const tier = round.matched ? tierForRarity(round.matched.rarity) : TIERS[0];
  const tool = TOOLS[tier.tool];
  const [frame, setFrame] = useState(0);
  const skip = useRef<HTMLButtonElement | null>(null);

  useEffect(() => {
    skip.current?.focus({ preventScroll: true });
  }, []);

  useEffect(() => {
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
    const timer = window.setInterval(() => setFrame((value) => (value + 1) % 2), 140);
    return () => window.clearInterval(timer);
  }, []);

  return (
    <div className="digcard panel" data-tier={tier.id}>
      <div className="digcard-row">
        <div className="digcard-tool">
          <PixelSprite sprite={tool.frames[frame]} scale={3} title={tool.name} />
        </div>
        <div className="digcard-text">
          <p className="digcard-verb">
            <b>{tool.name}</b> cavando
          </p>
          <p className="digcard-answer">{round.matched?.n ?? round.guess}</p>
        </div>
        <div className="digcard-meta">
          <span className="digcard-tier">{tier.label}</span>
          <span className="digcard-m">+{round.meters} m</span>
        </div>
      </div>
      <ol className="digcard-ladder" aria-label="Ferramentas, da resposta mais óbvia à mais rara">
        {TIERS.map((item) => (
          <li key={item.id} data-on={item.id === tier.id} data-past={item.id < tier.id}>
            <PixelSprite sprite={TOOLS[item.tool].frames[0]} scale={1} />
            <span>{item.toolName}</span>
            <em>{item.label}</em>
          </li>
        ))}
      </ol>
      <button ref={skip} type="button" className="digcard-skip" onClick={onSkip}>
        pular animação <kbd>enter</kbd>
      </button>
    </div>
  );
}
