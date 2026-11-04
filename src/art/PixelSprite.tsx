import { useMemo, type JSX } from "react";
import type { Sprite } from "./sprites.ts";

type Run = { x: number; y: number; w: number; fill: string };

function toRuns(sprite: Sprite): Run[] {
  const runs: Run[] = [];
  if (!sprite) return runs;
  sprite.rows.forEach((row, y) => {
    let x = 0;
    while (x < row.length) {
      const ch = row[x];
      if (ch === ".") {
        x++;
        continue;
      }
      let end = x + 1;
      while (end < row.length && row[end] === ch) end++;
      const fill = sprite.palette[ch];
      if (fill) runs.push({ x, y, w: end - x, fill });
      x = end;
    }
  });
  return runs;
}

export function PixelSprite(props: {
  sprite: Sprite;
  scale?: number;
  title?: string;
  className?: string;
}): JSX.Element {
  const { sprite, scale = 2, title, className } = props;
  const runs = useMemo(() => toRuns(sprite), [sprite]);
  if (!sprite) return <></>;
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox={`0 0 ${sprite?.w} ${sprite?.h}`}
      width={(sprite?.w ?? 0) * scale}
      height={(sprite?.h ?? 0) * scale}
      shapeRendering="crispEdges"
      className={className}
      {...(title ? { role: "img" } : { "aria-hidden": true })}
    >
      {title ? <title>{title}</title> : null}
      {runs.map((r) => (
        <rect key={`${r.x},${r.y}`} x={r.x} y={r.y} width={r.w} height={1} fill={r.fill} />
      ))}
    </svg>
  );
}
