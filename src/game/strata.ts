import type { MineralId } from "../art/sprites.ts";

export type Stratum = {
  id: MineralId;
  label: string;
  fact: string;
  from: number;
  to: number;
  fill: string;
  hatch: string;
  pFrom: number;
  pTo: number;
};

/** Eight bands of Brazilian ore, from coal at the surface to diamond at the bottom. */
export const STRATA: Stratum[] = [
  {
    id: "carvao",
    label: "Carvão",
    fact: "Santa Catarina e Rio Grande do Sul concentram o carvão mineral do país",
    from: 0,
    to: 40,
    fill: "#1f1a17",
    hatch: "var(--hatch-solo)",
    pFrom: 0,
    pTo: 0.2,
  },
  {
    id: "ferro",
    label: "Ferro",
    fact: "Carajás, no Pará, é uma das maiores minas de ferro do mundo",
    from: 40,
    to: 120,
    fill: "#3a2019",
    hatch: "var(--hatch-arenito)",
    pFrom: 0.2,
    pTo: 0.35,
  },
  {
    id: "bauxita",
    label: "Bauxita",
    fact: "o Pará lidera a produção de bauxita, a rocha do alumínio",
    from: 120,
    to: 220,
    fill: "#4a2a17",
    hatch: "var(--hatch-ardosia)",
    pFrom: 0.35,
    pTo: 0.5,
  },
  {
    id: "cobre",
    label: "Cobre",
    fact: "Sossego e Salobo, em Carajás, são minas de cobre",
    from: 220,
    to: 330,
    fill: "#2b2a1d",
    hatch: "var(--hatch-quartzito)",
    pFrom: 0.5,
    pTo: 0.65,
  },
  {
    id: "ouro",
    label: "Ouro",
    fact: "Serra Pelada, no Pará, foi o maior garimpo a céu aberto dos anos 1980",
    from: 330,
    to: 440,
    fill: "#33280f",
    hatch: "var(--hatch-xisto)",
    pFrom: 0.65,
    pTo: 0.78,
  },
  {
    id: "esmeralda",
    label: "Esmeralda",
    fact: "Bahia, Goiás e Minas Gerais têm garimpos de esmeralda",
    from: 440,
    to: 550,
    fill: "#132a20",
    hatch: "var(--hatch-gnaisse)",
    pFrom: 0.78,
    pTo: 0.88,
  },
  {
    id: "turmalina",
    label: "Turmalina Paraíba",
    fact: "descoberta no interior da Paraíba no fim dos anos 1980",
    from: 550,
    to: 640,
    fill: "#0f2629",
    hatch: "var(--hatch-quartzito)",
    pFrom: 0.88,
    pTo: 0.95,
  },
  {
    id: "diamante",
    label: "Diamante",
    fact: "Diamantina, em Minas Gerais, nasceu do garimpo de diamante",
    from: 640,
    to: 700,
    fill: "#161c22",
    hatch: "var(--hatch-kimberlito)",
    pFrom: 0.95,
    pTo: 1,
  },
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
