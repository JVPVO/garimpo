export type Tier = {
  id: number;
  mineral: string;
  cut: string;
  fill: string;
  from: number;
  to: number;
  ticks: number;
};

/** Five tiers. Silhouette first, colour second, name third. */
export const TIERS: Tier[] = [
  { id: 1, mineral: "Quartzo leitoso", cut: "bruto", fill: "#CFC6B4", from: 0, to: 180, ticks: 1 },
  { id: 2, mineral: "Granada", cut: "cabochão", fill: "#C0503A", from: 180, to: 380, ticks: 2 },
  { id: 3, mineral: "Esmeralda", cut: "corte esmeralda", fill: "#35996B", from: 380, to: 520, ticks: 3 },
  { id: 4, mineral: "Ametista", cut: "octógono", fill: "#8A6ABE", from: 520, to: 640, ticks: 4 },
  { id: 5, mineral: "Diamante", cut: "brilhante", fill: "#C9E6EA", from: 640, to: 700, ticks: 5 },
];

export const MAX_DEPTH = 700;

/**
 * Reference plunge: the printed scale of the plate.
 * p = 0 is the most obvious possible answer, p = 1 the rarest.
 *
 * Calibrated by tools/sim/app_curve.py against this dataset's own pools:
 * 4 000 simulated dives, rank-based player model. p^0.32 puts a median dive
 * around 360 m and leaves 700 m only for seven genuinely rare answers.
 */
export const refDepth = (p: number) => MAX_DEPTH * Math.pow(clamp01(p), 1.5);

const CURVE_EXPONENT = 0.32;

/** Points for one answer: 1 to 10, from the empirical rarity percentile. */
export const pointsFor = (rarity: number) => 1 + 9 * Math.pow(clamp01(rarity), CURVE_EXPONENT);

/** One answer's contribution to the shaft, in whole metres (10 to 100). */
export const dig = (rarity: number) => Math.round(pointsFor(rarity) * 10);

export function clamp01(value: number): number {
  return Math.min(1, Math.max(0, Number.isFinite(value) ? value : 0));
}

export function tierForDepth(depth: number): Tier {
  return TIERS.find((tier) => depth < tier.to) ?? TIERS[TIERS.length - 1];
}

export function tierForPoints(points: number): Tier {
  const index = Math.min(TIERS.length - 1, Math.max(0, Math.round(points / 2) - 1));
  return TIERS[index];
}

/** Tier of a single answer, from its rarity percentile (not from metres). */
export function tierForRarity(rarity: number): Tier {
  const p = clamp01(rarity);
  if (p < 0.4) return TIERS[0];
  if (p < 0.65) return TIERS[1];
  if (p < 0.82) return TIERS[2];
  if (p < 0.95) return TIERS[3];
  return TIERS[4];
}

export function styleScale(oneIn: number | null): string {
  if (!oneIn || oneIn < 2) return "1 em 2";
  if (oneIn >= 1000) return `1 em ${Math.round(oneIn / 100) * 100}`;
  if (oneIn >= 100) return `1 em ${Math.round(oneIn / 10) * 10}`;
  return `1 em ${Math.round(oneIn)}`;
}
