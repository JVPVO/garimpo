import type { ToolId } from "../art/sprites.ts";

/** What an answer of this tier turns up in the ground. */
export type FindId = "carvao" | "ferro" | "cobre" | "ouro" | "rubi" | "diamante";

export type Tier = {
  id: number;
  /** Rarity label shown to the player. */
  label: string;
  /** Tool that digs for an answer of this rarity. */
  tool: ToolId;
  toolName: string;
  /** Fixed metres (= points) this tier digs. Same scale as Krillion: 10 to 100. */
  meters: number;
  /** Lowest rarity percentile (0–1) that lands in this tier. */
  minRarity: number;
  find: FindId;
  /** "Você encontrou …" */
  findName: string;
  fill: string;
};

/**
 * Six fixed steps. An obvious answer always digs 10 m, the rarest always 100 m.
 * Seven perfect answers reach 700 m, the bottom of the world.
 *
 * `minRarity` cut points are calibrated by tools/dataset against the pools'
 * rarity distribution (see reports/dataset.md).
 */
export const TIERS: Tier[] = [
  {
    id: 1,
    label: "Óbvia",
    tool: "pa",
    toolName: "Pá",
    meters: 10,
    minRarity: 0,
    find: "carvao",
    findName: "carvão",
    fill: "#8f8274",
  },
  {
    id: 2,
    label: "Comum",
    tool: "aspirador",
    toolName: "Aspirador",
    meters: 15,
    minRarity: 0.2,
    find: "ferro",
    findName: "ferro",
    fill: "#d9d2c3",
  },
  {
    id: 3,
    label: "Boa",
    tool: "escavadeira",
    toolName: "Escavadeira",
    meters: 30,
    minRarity: 0.37,
    find: "cobre",
    findName: "cobre",
    fill: "#f2b65a",
  },
  {
    id: 4,
    label: "Rara",
    tool: "broca",
    toolName: "Broca",
    meters: 60,
    minRarity: 0.58,
    find: "ouro",
    findName: "ouro",
    fill: "#e2733b",
  },
  {
    id: 5,
    label: "Raríssima",
    tool: "broca-ultra",
    toolName: "Broca ultra",
    meters: 85,
    minRarity: 0.76,
    find: "rubi",
    findName: "um rubi",
    fill: "#d8344f",
  },
  {
    id: 6,
    label: "Uma em um milhão",
    tool: "dinamite",
    toolName: "Dinamite",
    meters: 100,
    minRarity: 0.95,
    find: "diamante",
    findName: "um diamante",
    fill: "#2fd4c8",
  },
];

export const MAX_DEPTH = 700;

export function clamp01(value: number): number {
  return Math.min(1, Math.max(0, Number.isFinite(value) ? value : 0));
}

/** Tier of a single answer, from its rarity percentile. */
export function tierForRarity(rarity: number): Tier {
  const p = clamp01(rarity);
  let tier = TIERS[0];
  for (const item of TIERS) if (p >= item.minRarity) tier = item;
  return tier;
}

/** Points for one answer. Points and metres are the same number. */
export const pointsFor = (rarity: number) => tierForRarity(rarity).meters;

/** One answer's contribution to the shaft, in whole metres (10 to 100). */
export const dig = (rarity: number) => tierForRarity(rarity).meters;

/** Overall rank of a finished dive, from its total depth. */
export function tierForDepth(depth: number): Tier {
  const average = depth / 7;
  let tier = TIERS[0];
  for (const item of TIERS) if (average >= item.meters) tier = item;
  return tier;
}

export function styleScale(oneIn: number | null): string {
  if (!oneIn || oneIn < 2) return "1 em 2";
  if (oneIn >= 1000) return `1 em ${Math.round(oneIn / 100) * 100}`;
  if (oneIn >= 100) return `1 em ${Math.round(oneIn / 10) * 10}`;
  return `1 em ${Math.round(oneIn)}`;
}
