/// <reference types="node" />
// Coverage test: run the probe lists through the real matcher.
//   node tools/coverage/run.ts            (Node >= 23, native type stripping)
import { readFileSync, readdirSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { findAnswer } from "../../src/game/match.ts";

type Probe = { pos: string[]; neg?: string[] };
const here = dirname(fileURLToPath(import.meta.url));
const root = join(here, "..", "..");
const data = JSON.parse(readFileSync(join(root, "public/data/garimpo.json"), "utf8"));
const probes: Record<string, Probe> = {};
for (const file of readdirSync(here)
  .filter((f: string) => /^probes_.*\.json$/.test(f))
  .sort()) {
  const content = JSON.parse(readFileSync(join(here, file), "utf8"));
  for (const [id, probe] of Object.entries(content))
    if (!id.startsWith("_")) probes[id] = probe as Probe;
}

const rows: unknown[] = [];
let hits = 0;
let total = 0;
let falsePos = 0;
let negTotal = 0;
const perPrompt: {
  id: string;
  text: string;
  n: number;
  pct: number;
  miss: string[];
  fp: string[];
}[] = [];
const noProbe: string[] = [];
for (const prompt of data.prompts) {
  const probe = probes[prompt.id];
  if (!probe) {
    noProbe.push(prompt.id);
    continue;
  }
  const miss: string[] = [];
  const fp: string[] = [];
  for (const guess of probe.pos) {
    const match = findAnswer(guess, prompt.answers);
    if (match) hits += 1;
    else miss.push(guess);
    total += 1;
  }
  for (const guess of probe.neg ?? []) {
    const match = findAnswer(guess, prompt.answers);
    negTotal += 1;
    if (match) {
      falsePos += 1;
      fp.push(`${guess} -> ${match.answer.n}`);
    }
  }
  const pct = probe.pos.length ? (probe.pos.length - miss.length) / probe.pos.length : 1;
  perPrompt.push({ id: prompt.id, text: prompt.text, n: probe.pos.length, pct, miss, fp });
  rows.push({
    id: prompt.id,
    text: prompt.text,
    probes: probe.pos.length,
    accepted: probe.pos.length - miss.length,
    missed: miss,
    falsePositives: fp,
  });
}
perPrompt.sort((a, b) => a.pct - b.pct);
const summary = {
  overall: total ? hits / total : 0,
  probes: total,
  accepted: hits,
  promptsTested: perPrompt.length,
  promptsBelow90: perPrompt.filter((p) => p.pct < 0.9).map((p) => p.id),
  falsePositives: falsePos,
  negativesTested: negTotal,
  promptsWithoutProbes: noProbe,
  unusedProbeIds: Object.keys(probes).filter(
    (id) => !data.prompts.some((p: { id: string }) => p.id === id),
  ),
};
writeFileSync(join(here, "results.json"), JSON.stringify({ summary, prompts: rows }, null, 1));
console.log(JSON.stringify(summary, null, 1));
for (const p of perPrompt.filter((x) => x.pct < 0.95)) {
  console.log(
    `${(p.pct * 100).toFixed(0).padStart(3)}% ${p.id} (${p.n}) miss: ${p.miss.join(", ")}${p.fp.length ? " | FP: " + p.fp.join(", ") : ""}`,
  );
}
for (const p of perPrompt.filter((x) => x.fp.length && x.pct >= 0.9))
  console.log(`FP ${p.id}: ${p.fp.join(", ")}`);
