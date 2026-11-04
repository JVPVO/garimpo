export type Answer = {
  n: string;
  a: string[];
  qid?: string | null;
  rarity: number;
  share: number;
  popPercentile: number;
  oneIn: number | null;
  points: number;
  rank: number;
  pv: number | null;
  sl: number;
  wf: number;
  g: number | null;
  an?: number | null;
  src?: string | null;
  cat?: string;
};

export type Prompt = {
  id: string;
  text: string;
  cat: string;
  answers: Answer[];
};

export type Dataset = {
  builtAt: string;
  method: {
    version: number;
    weights: Record<string, number>;
    pageviewsWindow: string;
    pointsFormula: string;
    rarityDefinition: string;
    shareFormula: string;
    depthPerPoint: number;
    sources: { name: string; url: string }[];
  };
  stats: {
    prompts: number;
    answers: number;
    uniqueAnswers: number;
    withPageviews: number;
    pools: Record<string, number>;
  };
  prompts: Prompt[];
};

export type Round = {
  prompt: Prompt;
  guess: string;
  matched: Answer | null;
  meters: number;
  ms: number;
  timedOut: boolean;
};

export type Dive = {
  id: string;
  mode: "daily" | "unlimited";
  label: string;
  date: string;
  seed: number;
  depth: number;
  tier: number;
  finishedAt: string;
  rounds: {
    promptId: string;
    prompt: string;
    guess: string;
    name: string | null;
    p: number | null;
    meters: number;
    rank: number | null;
    count: number;
  }[];
};
