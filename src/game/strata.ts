export type Stratum = {
  id: string;
  label: string;
  fact: string;
  from: number;
  to: number;
  fill: string;
  hatch: string;
  pFrom: number;
  pTo: number;
};

/** Seven bands. Depth and rarity share the same axis. */
export const STRATA: Stratum[] = [
  { id: "solo", label: "Solo", fact: "argila com seixos", from: 0, to: 20, fill: "#3A2C20", hatch: "var(--hatch-solo)", pFrom: 0, pTo: 0.23 },
  { id: "arenito", label: "Arenito", fact: "arenito friável", from: 20, to: 80, fill: "#2E2319", hatch: "var(--hatch-arenito)", pFrom: 0.23, pTo: 0.38 },
  { id: "ardosia", label: "Ardósia", fact: "ardósia, clivagem 76°", from: 80, to: 180, fill: "#26201A", hatch: "var(--hatch-ardosia)", pFrom: 0.38, pTo: 0.57 },
  { id: "quartzito", label: "Quartzito", fact: "quartzito maciço", from: 180, to: 320, fill: "#34291C", hatch: "var(--hatch-quartzito)", pFrom: 0.57, pTo: 0.76 },
  { id: "xisto", label: "Xisto", fact: "xisto com veios", from: 320, to: 460, fill: "#221B15", hatch: "var(--hatch-xisto)", pFrom: 0.76, pTo: 0.88 },
  { id: "gnaisse", label: "Gnaisse", fact: "gnaisse dobrado", from: 460, to: 600, fill: "#1D1712", hatch: "var(--hatch-gnaisse)", pFrom: 0.88, pTo: 0.94 },
  { id: "kimberlito", label: "Kimberlito", fact: "kimberlito, mineral indicador", from: 600, to: 700, fill: "#16110D", hatch: "var(--hatch-kimberlito)", pFrom: 0.94, pTo: 1 },
];

export function stratumForDepth(depth: number): Stratum {
  return STRATA.find((stratum) => depth < stratum.to) ?? STRATA[STRATA.length - 1];
}

/** Readable names for the ledger, keyed by pool id. */
export const CATEGORY_LABEL: Record<string, string> = {
  uf: "estados",
  cidade: "cidades",
  presidente: "presidentes",
  jogador: "seleção",
  time: "times",
  rio: "rios",
  parque: "parques",
  estadio: "estádios",
  frutas_nativas: "frutas",
  pratos_tipicos: "pratos",
  doces: "doces",
  novelas: "novelas",
  filmes: "filmes",
  cantores: "cantores",
  escritores: "escritores",
  atores: "atores",
  marcas: "marcas",
  aves: "aves",
  mamiferos: "mamíferos",
  folclore: "folclore",
  festas: "festas",
  dancas: "danças",
  instrumentos: "instrumentos",
  palavras_tupi: "tupi",
  girias: "gírias",
  bebidas: "bebidas",
  bbb: "BBB",
  bbb_campeoes: "BBB",
  tv_globinho: "TV Globinho",
  desenhos: "desenhos",
  pais: "países",
  capital_mundo: "capitais",
  elemento: "elementos",
  cidade_mundo: "cidades do mundo",
  videogame: "videogames",
  anime: "animes",
  banda: "bandas",
  pokemon: "Pokémon",
  heroi: "heróis",
  comida_mundo: "comida do mundo",
  marca_global: "marcas globais",
};

export function stratumForRarity(rarity: number): Stratum {
  const p = Math.min(1, Math.max(0, rarity));
  return STRATA.find((stratum) => p < stratum.pTo) ?? STRATA[STRATA.length - 1];
}

/** Share of the whole catalogue that landed in each band, from the real data. */
export function sharesFor(rarities: number[]): number[] {
  const counts = STRATA.map(() => 0);
  for (const rarity of rarities) {
    const index = STRATA.findIndex((stratum) => rarity < stratum.pTo);
    counts[index === -1 ? STRATA.length - 1 : index] += 1;
  }
  const total = rarities.length || 1;
  return counts.map((count) => count / total);
}
