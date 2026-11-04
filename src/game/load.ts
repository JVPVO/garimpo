import type { Dataset } from "./types";

let cache: Dataset | null = null;

export async function loadDataset(): Promise<Dataset> {
  if (cache) return cache;
  const response = await fetch(`${import.meta.env.BASE_URL}data/garimpo.json`);
  if (!response.ok) throw new Error(`dataset ${response.status}`);
  cache = (await response.json()) as Dataset;
  return cache;
}
