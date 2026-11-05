/// <reference types="node" />
// Coverage test: run the probe lists through the real matcher.
//   node tools/coverage/run.ts                     (current matcher + public/data)
//   node tools/coverage/run.ts --before DATA.json  (frozen v2 matcher on an old dataset)
//   node tools/coverage/run.ts --only g            (only probes_g.json, the precision set)
// Recall = correct guesses accepted OR offered as "corrige para X?" (right answer).
// False accept = a wrong guess auto-accepted. False suggestion = a wrong guess
// offered a correction (the player still has to confirm it).
import { readFileSync, readdirSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import * as current from "../../src/game/match.ts";
import * as frozen from "./baseline/match_v2.ts";

type Answer = { n: string; a: string[]; rarity: number };
type Matcher = {
  findAnswer: (g: string, a: Answer[]) => { answer: Answer } | null;
  findSuggestion: (g: string, a: Answer[]) => { answer: Answer } | null;
};
type Probe = { pos: string[]; neg?: string[] };

const argv = process.argv.slice(2);
const flag = (name: string) => {
  const i = argv.indexOf(name);
  return i >= 0 ? argv[i + 1] : undefined;
};
const before = argv.includes("--before");
const only = flag("--only");
const matcher = (before ? frozen : current) as unknown as Matcher;
const here = dirname(fileURLToPath(import.meta.url));
const root = join(here, "..", "..");
const dataPath = (before && flag("--before")) || join(root, "public/data/garimpo.json");

type Prompt = { id: string; text: string; answers: Answer[] };
function loadPrompts(path: string): Prompt[] {
  const data = JSON.parse(readFileSync(path, "utf8"));
  if (data.prompts?.length && data.prompts[0].answers) return data.prompts;
  // split layout: index + one file per prompt
  const dir = dirname(path);
  return data.prompts.map((p: { id: string; text: string; file: string }) => ({
    ...p,
    answers: JSON.parse(readFileSync(join(dir, p.file), "utf8")).answers,
  }));
}
const prompts = loadPrompts(
  !before && !flag("--data")
    ? join(root, "public/data/garimpo.json")
    : (flag("--data") ?? dataPath),
);

const probes: Record<string, Probe> = {};
for (const file of readdirSync(here)
  .filter((f: string) => /^probes_.*\.json$/.test(f))
  .filter((f: string) => !only || f === `probes_${only}.json`)
  .sort()) {
  const content = JSON.parse(readFileSync(join(here, file), "utf8"));
  for (const [id, probe] of Object.entries(content)) {
    if (id.startsWith("_")) continue;
    const p = probe as Probe;
    const prev = probes[id];
    probes[id] = prev
      ? { pos: [...prev.pos, ...p.pos], neg: [...(prev.neg ?? []), ...(p.neg ?? [])] }
      : { pos: [...p.pos], neg: [...(p.neg ?? [])] };
  }
}

let accepted = 0;
let suggested = 0;
let total = 0;
let falseAccept = 0;
let falseSuggest = 0;
let negTotal = 0;
const rows: unknown[] = [];
const perPrompt: { id: string; n: number; pct: number; miss: string[]; fp: string[] }[] = [];
const noProbe: string[] = [];
for (const prompt of prompts) {
  const probe = probes[prompt.id];
  if (!probe) {
    noProbe.push(prompt.id);
    continue;
  }
  const miss: string[] = [];
  const sugg: string[] = [];
  const fp: string[] = [];
  const fs: string[] = [];
  for (const guess of probe.pos) {
    total += 1;
    if (matcher.findAnswer(guess, prompt.answers)) accepted += 1;
    else if (matcher.findSuggestion(guess, prompt.answers)) {
      suggested += 1;
      sugg.push(`${guess} -> ${matcher.findSuggestion(guess, prompt.answers)!.answer.n}`);
    } else miss.push(guess);
  }
  for (const guess of probe.neg ?? []) {
    negTotal += 1;
    const match = matcher.findAnswer(guess, prompt.answers);
    if (match) {
      falseAccept += 1;
      fp.push(`${guess} -> ${match.answer.n}`);
      continue;
    }
    const hint = matcher.findSuggestion(guess, prompt.answers);
    if (hint) {
      falseSuggest += 1;
      fs.push(`${guess} -> ${hint.answer.n}?`);
    }
  }
  const pct = probe.pos.length ? (probe.pos.length - miss.length) / probe.pos.length : 1;
  perPrompt.push({ id: prompt.id, n: probe.pos.length, pct, miss, fp });
  rows.push({
    id: prompt.id,
    text: prompt.text,
    probes: probe.pos.length,
    accepted: probe.pos.length - miss.length - sugg.length,
    suggested: sugg,
    missed: miss,
    falseAccepts: fp,
    falseSuggestions: fs,
  });
}
perPrompt.sort((a, b) => a.pct - b.pct);
const summary = {
  matcher: before ? "v2 (partial words)" : "v3 (exact + suggestions)",
  probeSet: only ? `probes_${only}.json` : "all",
  probes: total,
  acceptedRate: total ? accepted / total : 0,
  recall: total ? (accepted + suggested) / total : 0,
  accepted,
  suggested,
  promptsTested: perPrompt.length,
  promptsBelow90: perPrompt.filter((p) => p.pct < 0.9).map((p) => p.id),
  negativesTested: negTotal,
  falseAccepts: falseAccept,
  falseAcceptRate: negTotal ? falseAccept / negTotal : 0,
  falseSuggestions: falseSuggest,
  promptsWithoutProbes: only ? [] : noProbe,
};
const out = before ? "results_before.json" : only ? `results_${only}.json` : "results.json";
writeFileSync(join(here, out), JSON.stringify({ summary, prompts: rows }, null, 1));
console.log(JSON.stringify(summary, null, 1));
for (const p of perPrompt.filter((x) => x.pct < 0.95))
  console.log(
    `${(p.pct * 100).toFixed(0).padStart(3)}% ${p.id} (${p.n}) miss: ${p.miss.join(", ")}`,
  );
for (const p of perPrompt.filter((x) => x.fp.length)) console.log(`FA ${p.id}: ${p.fp.join(", ")}`);
