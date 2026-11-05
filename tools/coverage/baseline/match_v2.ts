// Frozen copy of the v2 matcher (partial-word acceptance), kept only so
// tools/coverage/run.ts can report "before" numbers. Not used by the game.
type Answer = { n: string; a: string[]; rarity: number };
const STOP = new Set(["de", "da", "do", "das", "dos", "e", "o", "a", "os", "as", "um", "uma"]);
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
]);
function norm(value: string): string {
  return value
    .normalize("NFD")
    .replace(/[̀-ͯ]/g, "")
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, " ")
    .trim()
    .replace(/\s+/g, " ");
}
function key(value: string): string {
  return norm(value)
    .split(" ")
    .filter((t) => t && !STOP.has(t))
    .join(" ");
}
function levenshtein(a: string, b: string): number {
  if (a === b) return 0;
  if (!a.length) return b.length;
  if (!b.length) return a.length;
  let prev = Array.from({ length: b.length + 1 }, (_, i) => i);
  for (let i = 1; i <= a.length; i += 1) {
    const row = [i];
    for (let j = 1; j <= b.length; j += 1)
      row[j] = Math.min(prev[j] + 1, row[j - 1] + 1, prev[j - 1] + (a[i - 1] === b[j - 1] ? 0 : 1));
    prev = row;
  }
  return prev[b.length];
}
const tokens = (v: string) => key(v).split(" ").filter(Boolean);
function scoreLabel(guess: string, label: string): number {
  const g = norm(guess);
  const l = norm(label);
  if (!g || !l) return 0;
  if (g === l) return 1;
  const gk = key(guess);
  const lk = key(label);
  if (gk && gk === lk) return 0.99;
  const gTok = tokens(guess);
  if (gTok.length === 1 && GENERIC.has(gTok[0])) return 0;
  const lTok = tokens(label);
  if (gTok.length && lTok.length) {
    if (gTok.every((t) => lTok.includes(t)) && gk.length >= 4) return 0.96;
    if (lTok.every((t) => gTok.includes(t)) && lk.length >= 4) return 0.94;
  }
  if (g.length >= 4 && (l.startsWith(`${g} `) || l.endsWith(` ${g}`) || l.includes(` ${g} `)))
    return 0.93;
  if (l.length >= 4 && (g.startsWith(`${l} `) || g.endsWith(` ${l}`) || g.includes(` ${l} `)))
    return 0.9;
  const distance = levenshtein(gk || g, lk || l);
  const longest = Math.max((gk || g).length, (lk || l).length);
  const ratio = 1 - distance / Math.max(longest, 1);
  const tolerance = longest <= 5 ? 1 : 2;
  if (distance <= tolerance && ratio >= 0.72) return ratio * 0.9;
  if (distance <= 3 && ratio >= 0.86 && longest >= 8) return ratio * 0.85;
  return 0;
}
export function findAnswer(
  guess: string,
  answers: Answer[],
): { answer: Answer; score: number } | null {
  const trimmed = guess.trim();
  if (!trimmed) return null;
  let best: { answer: Answer; score: number } | null = null;
  for (const answer of answers) {
    let score = scoreLabel(trimmed, answer.n);
    for (const alias of answer.a) score = Math.max(score, scoreLabel(trimmed, alias));
    if (score >= 0.72 && (!best || score > best.score)) best = { answer, score };
  }
  return best;
}
export function findSuggestion(): null {
  return null;
}
