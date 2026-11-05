import type { Answer } from "./types";

/**
 * Matching rules (acervo v3):
 *
 *  - ACCEPT only on a normalised full match of the answer's name or one of its
 *    explicit aliases. "Normalised" forgives case, accents, punctuation,
 *    hyphen/space, articles/prepositions ("o", "de", "da"...), simple plurals
 *    ("coxinhas", "pastéis") and glued words ("pao de queijo" = "paodequeijo").
 *    Short forms (surnames, nicknames) are accepted only when the dataset lists
 *    them as aliases, which the build does only when they are unambiguous.
 *  - Never accept a part of a name: "Grêmio" does not match "Grêmio Novorizontino".
 *  - Typos and unique partial names are only SUGGESTED (findSuggestion); the
 *    player confirms "corrige para X?".
 */

const STOP = new Set(["de", "da", "do", "das", "dos", "e", "o", "a", "os", "as", "um", "uma"]);

/** Structural words that name no answer on their own ("clube", "futebol"...). */
const GENERIC = new Set([
  "clube",
  "futebol",
  "esporte",
  "esportes",
  "sport",
  "associacao",
  "agremiacao",
  "municipal",
  "estadio",
  "parque",
  "cidade",
  "estado",
  "time",
  "santo",
  "santa",
  "sao",
  "rio",
  "nova",
  "novo",
  "jose",
  "maria",
  "joao",
]);

export function norm(value: string): string {
  return value
    .normalize("NFD")
    .replace(/[̀-ͯ]/g, "")
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, " ")
    .trim()
    .replace(/\s+/g, " ");
}

export function key(value: string): string {
  return norm(value)
    .split(" ")
    .filter((token) => token && !STOP.has(token))
    .join(" ");
}

/** Singular-ish form of one normalised token (pastéis → pastel, pães → pao). */
function stemToken(token: string): string {
  if (token.length <= 3 || /^\d+$/.test(token)) return token;
  if (token.endsWith("oes") || token.endsWith("aes")) return `${token.slice(0, -3)}ao`;
  if (token.endsWith("eis")) return `${token.slice(0, -3)}el`;
  if (token.endsWith("ais")) return `${token.slice(0, -3)}al`;
  if (token.endsWith("ns")) return `${token.slice(0, -2)}m`;
  if (token.endsWith("res") || token.endsWith("zes") || token.endsWith("ses"))
    return token.slice(0, -2);
  if (token.endsWith("s") && !token.endsWith("ss")) return token.slice(0, -1);
  return token;
}

function stem(value: string): string {
  return key(value).split(" ").filter(Boolean).map(stemToken).join(" ");
}

/** Every exact-match form of a label. */
function forms(value: string): string[] {
  const n = norm(value);
  if (!n) return [];
  const k = key(value) || n;
  const s = stem(value) || k;
  return [...new Set([n, k, s, k.replace(/ /g, ""), s.replace(/ /g, "")])];
}

/** Optimal-string-alignment distance (adjacent swaps cost 1), early exit past `cap`. */
function levenshtein(a: string, b: string, cap: number): number {
  if (a === b) return 0;
  if (Math.abs(a.length - b.length) > cap) return cap + 1;
  if (!a.length || !b.length) return Math.max(a.length, b.length);
  let before: number[] = [];
  let prev = Array.from({ length: b.length + 1 }, (_, i) => i);
  for (let i = 1; i <= a.length; i += 1) {
    const row = [i];
    let best = i;
    for (let j = 1; j <= b.length; j += 1) {
      let v = Math.min(prev[j] + 1, row[j - 1] + 1, prev[j - 1] + (a[i - 1] === b[j - 1] ? 0 : 1));
      if (i > 1 && j > 1 && a[i - 1] === b[j - 2] && a[i - 2] === b[j - 1]) {
        v = Math.min(v, before[j - 2] + 1);
      }
      row[j] = v;
      if (v < best) best = v;
    }
    if (best > cap) return cap + 1;
    before = prev;
    prev = row;
  }
  return prev[b.length];
}

/** Edits tolerated for a typo suggestion, by label length. */
function typoBudget(length: number): number {
  if (length <= 3) return 0;
  if (length <= 5) return 1;
  if (length <= 10) return 2;
  return 3;
}

type Entry = { answer: Answer; labels: string[]; compact: string[] };
type Index = { exact: Map<string, Answer[]>; entries: Entry[] };
const cache = new WeakMap<Answer[], Index>();

function indexFor(answers: Answer[]): Index {
  const hit = cache.get(answers);
  if (hit) return hit;
  const exact = new Map<string, Answer[]>();
  const entries: Entry[] = [];
  for (const answer of answers) {
    const labels = [answer.n, ...(answer.a ?? [])];
    const all = new Set<string>();
    for (const label of labels) for (const form of forms(label)) all.add(form);
    for (const form of all) {
      const bucket = exact.get(form);
      if (bucket) bucket.push(answer);
      else exact.set(form, [answer]);
    }
    entries.push({
      answer,
      labels: labels.map((l) => key(l) || norm(l)).filter(Boolean),
      compact: labels.map((l) => (stem(l) || norm(l)).replace(/ /g, "")).filter(Boolean),
    });
  }
  const index = { exact, entries };
  cache.set(answers, index);
  return index;
}

/** Most popular first (lowest rarity). */
function mostPopular(list: Answer[]): Answer {
  return list.reduce((best, item) => (item.rarity < best.rarity ? item : best), list[0]);
}

export type Match = { answer: Answer; score: number };

/** Find the catalogued answer a guess refers to, if any (exact forms only). */
export function findAnswer(guess: string, answers: Answer[]): Match | null {
  const trimmed = guess.trim();
  if (!trimmed) return null;
  const index = indexFor(answers);
  const order = forms(trimmed);
  for (let i = 0; i < order.length; i += 1) {
    const found = index.exact.get(order[i]);
    if (found?.length) return { answer: mostPopular(found), score: i === 0 ? 1 : 0.99 };
  }
  return null;
}

/**
 * Looser pass used only to *suggest* a correction ("corrige para X?"). It never
 * accepts an answer on its own: the player sees the canonical name and confirms.
 * Two kinds: a small typo (edit distance relative to length) or a guess that is
 * the unique first/last name of exactly one long answer.
 */
export function findSuggestion(guess: string, answers: Answer[]): Match | null {
  const trimmed = guess.trim();
  const g = (stem(trimmed) || norm(trimmed)).replace(/ /g, "");
  if (g.length < 4) return null;
  if (findAnswer(trimmed, answers)) return null;
  const index = indexFor(answers);

  let best: { answer: Answer; d: number } | null = null;
  const tied: Answer[] = [];
  for (const entry of index.entries) {
    let d = Infinity;
    for (const label of entry.compact) {
      const budget = typoBudget(Math.min(label.length, g.length));
      if (!budget) continue;
      const dist = levenshtein(g, label, budget);
      if (dist <= budget && dist < d) d = dist;
    }
    if (d === Infinity) continue;
    if (!best || d < best.d) {
      best = { answer: entry.answer, d };
      tied.length = 0;
      tied.push(entry.answer);
    } else if (d === best.d) tied.push(entry.answer);
  }
  if (best) {
    const answer = mostPopular(tied);
    const length = Math.max(g.length, 1);
    return { answer, score: Math.max(0.5, 1 - best.d / length) };
  }

  // Unique partial name: one guess token = first or last name of one answer.
  const gk = key(trimmed);
  const gTok = gk.split(" ").filter(Boolean);
  if (!gTok.length || gk.length < 5 || gTok.some((t) => GENERIC.has(t))) return null;
  const owners: Answer[] = [];
  for (const entry of index.entries) {
    const hitLabel = entry.labels.some((label) => {
      const lTok = label.split(" ");
      if (lTok.length <= gTok.length) return false;
      const head = lTok.slice(0, gTok.length).join(" ");
      const tail = lTok.slice(-gTok.length).join(" ");
      return head === gk || tail === gk;
    });
    if (hitLabel) owners.push(entry.answer);
    if (owners.length > 1) return null;
  }
  return owners.length === 1 ? { answer: owners[0], score: 0.6 } : null;
}
