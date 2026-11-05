# Garimpo — game-loop economics

Design sub-agent output: scoring curve, depth ladder, reveal beat, session shape, integrity rules.
Everything numeric here is reproducible from `tools/sim/curve.py` (stdlib only, no deps):

```bash
python3 tools/sim/curve.py            # candidate table (20 000 dives per curve)
python3 tools/sim/curve.py --chosen   # full spec of the shipped curve
python3 tools/sim/curve.py --frontier # median/p90/dead-zone frontier
python3 tools/sim/curve.py --search   # 294-parameter grid over the chosen family
```

Fixed seed `20260211`. Same seed, same numbers.

---

## 1. The model

| Input                 | Value                                                                    | Source      |
| --------------------- | ------------------------------------------------------------------------ | ----------- |
| Prompts per dive      | 7                                                                        | brief       |
| Time per prompt       | 25 s                                                                     | brief       |
| Rarity percentile `p` | empirical rank in the catalogued pool, `p=1` = rarest                    | brief       |
| Points per prompt     | `k = quantise(f(p))`, `k ∈ [1,10]`, step 0.1                             | chosen here |
| Depth per prompt      | `10 · k` metres                                                          | brief       |
| Max depth             | 700 m                                                                    | derived     |
| Wrong / blank         | 0 points, 0 m, 12 % per prompt                                           | brief       |
| Skill mix             | 55 % casual `Beta(2,5)`, 30 % solid `Beta(4,3)`, 15 % expert `Beta(6,2)` | brief       |

Two modelling decisions that matter, both stated here so they can be argued with:

1. **Skill class is drawn once per player; `p` is drawn per prompt** from that class's Beta.
   This is the brief's literal model and it is the _pessimistic_ one — independent draws
   concentrate the sum. §8 shows what happens when players are streaky instead.
2. **`p` is a percentile, so a player answering uniformly at random draws `p ~ U(0,1)`.**
   That is what makes `p` comparable across pools of different sizes, and it is why an
   equal-width ladder in `p` is an equal-probability ladder — and also why its bands are
   enormous dead zones: one band swallows 10 % of every pool.

---

## 2. Candidate curves, measured

`tools/sim/curve.py`, 20 000 dives per row, seed 20260211, ρ=0.
Reproduced verbatim from the tool:

```
curve                        k step    p10    p50    p90  >=600   <200   k  dz pp  verdict
-------------------------------------------------------------------------------------------------
linear                          0.1    177    275    474   0.2%  18.3%  91    1.1  no: median 275 outside 380-450; p90 474 < 600; under-200m 18.3% > 8%
power p^1.4                     0.1    130    215    425   0.0%  44.7%  91    2.9  no: median 215 outside 380-450; p90 425 < 600; under-200m 44.7% > 8%
ladder (10 tiers)               0.1    160    270    490   1.2%  22.7%  10   10.0  no: median 270 outside 380-450; p90 490 < 600; under-200m 22.7% > 8%; dead zone 10.0pp > 6pp
buckets (6 tiers)               0.1     80    145    310   0.0%  64.1%   6   30.0  no: median 145 outside 380-450; p90 310 < 600; under-200m 64.1% > 8%; dead zone 30.0pp > 6pp
logistic a=7 mid=.5             0.1    143    252    509   2.1%  33.5%  85    4.2  no: median 252 outside 380-450; p90 509 < 600; under-200m 33.5% > 8%
softfloor 2+8p^.85              0.1    242    342    514   1.4%   2.8%  81    1.5  no: median 342 outside 380-450; p90 514 < 600
power p^0.45                    0.1    306    417    568   5.7%   0.5%  91    2.4  no: p90 568 < 600
chosen: vein w=.35 a=16 b=.20   0.1    272    420    603  10.8%   1.9%  91    3.1  OK
chosen @ 0.5 step               0.5    270    420    605  11.2%   1.8%  19   15.4  no: dead zone 15.4pp > 6pp
```

Columns: `p10/p50/p90` = total dive depth percentiles; `>=600`, `<200` = share of dives;
`k` = distinct point values the curve can produce (score granularity); `dz pp` = the widest
interval of `p`, in percentage points, that earns exactly the same points.

Why each family fails on its own:

- **Linear (275 / 474).** Reads correctly — rank and reward move together, 91 values, no dead
  zone — but it is too poor at the bottom and too flat globally. Under a population that is
  55 % casual it parks the median 105 m too low and still never reaches 600. It is the honest
  baseline that proves the target is not reachable by "just be linear".
- **Power `p^1.4` (215 / 425).** Punishes common answers superlinearly, which is thematically
  right and numerically fatal: **44.7 % of dives land under 200 m**. Casual players (55 % of
  the audience) never see past mid-mountain. Rejected on retention grounds.
- **10-tier ladder (270 / 490).** Only 10 distinct scores, and every band is 10 pp wide: a
  top-20 % answer and a top-29 % answer pay identically. The median is also too low because
  equal-width `p` bands over-reward nothing in particular. This is the case the brief's
  "no dead zone" rule exists to kill.
- **6-tier bucket ladder (145 / 310).** 6 values, 30 pp bands, 64 % of dives under 200 m.
  A ladder built to feel chunky destroys the middle of the distribution.
- **Plain logistic (252 / 509).** The S-shape is the right _instinct_ — it is the only family
  whose slope peaks in the interior — but a bare logistic is flat at _both_ ends: below
  `p≈0.3` everything is worth ~1 point (that is the 33 % under 200 m) and above `p≈0.75`
  everything is worth ~10 (4.2 pp band). Both flat ends are dead zones in the two places
  players care most.
- **Soft floor `2 + 8p^0.85` (342 / 514).** Lifts the bottom by removing 1-point answers, which
  cuts the under-200 tail to 2.8 % — but a floor is a dead zone by construction (the most common
  0.3 % of answers all pay exactly 2), and the median is still 40 m short.

**The lesson from the six failures:** a single power law cannot hit this target set. Convex
curves starve the bottom, concave curves flatten the top, and any curve tuned for the median
of a 55 %-casual population loses the top decile.

---

## 3. Two structural facts the frontier exposes

### 3.1 With one smooth power law, p90 ≥ 600 requires a median of ~470–480

Sweeping `k = 1 + 9p^exp` (10 000 dives per point), from `--frontier`:

| exp  | p10 | p50 | p90 | ≥600   | <200   | widest band | median in 380–450 | p90 ≥ 600 |
| ---- | --- | --- | --- | ------ | ------ | ----------- | ----------------- | --------- |
| 0.20 | 399 | 530 | 637 | 18.2 % | 0.1 %  | 5.3 pp      | out               | yes       |
| 0.30 | 360 | 478 | 608 | 12.0 % | 0.1 %  | 3.6 pp      | out               | yes       |
| 0.40 | 324 | 436 | 581 | 7.0 %  | 0.3 %  | 2.7 pp      | **in**            | no        |
| 0.45 | 306 | 418 | 569 | 5.8 %  | 0.5 %  | 2.4 pp      | **in**            | no        |
| 0.60 | 261 | 370 | 538 | 2.9 %  | 1.7 %  | 1.8 pp      | out               | no        |
| 1.00 | 178 | 277 | 477 | 0.2 %  | 18.3 % | 1.1 pp      | out               | no        |

`p90 > 600` and `median ≤ 450` do not co-exist on this frontier. The trade rate near the
knee is ≈0.65 m of p90 per metre of median (from exp 0.30 → 0.40: −42 m median, −27 m p90).

### 3.2 …unless the curve is allowed an interior cliff plus a live top end

An arbitrary-shape search (700 random monotone curves, 4 free knots) shows the target set _is_
reachable — the shapes that do it all look the same:

```
[1.0, 3.4, 7.7, 9.0, 9.5, 10.0]   at p = 0, .15, .35, .55, .80, 1.0
→ p50 435, p90 623, <200 1.3 %, widest band 4.4 pp
```

Read the shape: **harsh in the bottom third, a cliff in the middle, a slow linear crawl at the
top.** That is the economics of the target set, not a preference: the top decile of dives is
driven by the 60th–90th percentile of `p` (solid players on a good day), not by the extreme
tail, so the curve has to spend points there — and paying for it requires taking them away from
the obvious answers, not from the rarest ones.

### 3.3 Quantisation: 0.1 points (1 m), not 0.5

Same curve, two precisions: `0.1` → 91 distinct scores and a 3.1 pp worst band; `0.5` → 19
scores and a **15.4 pp** worst band, i.e. 15 % of the pool tied at one number. Half-point
granularity alone recreates the ladder problem it was meant to avoid. **1 m of depth per 0.1
point is the granularity that makes the dead-zone rule hold.** Depth is therefore always an
integer number of metres — which is also the cleanest player-facing number ("437 m").

---

## 4. The chosen curve: "the vein"

```
k(p) = 1 + 9 · (g(p) − g(0)) / (g(1) − g(0))
g(p) = 0.35·p + 0.65·sigmoid(16·(p − 0.20))
k is rounded to 0.1 and clamped to [1, 10];  depth = 10·k metres
```

Constants measured by the tool: `g(0) = 0.025457720`, `g(1) = 0.999998206`,
`9/(g(1)−g(0)) = 9.235121713`. Endpoints are normalised so `p=0` is exactly 1 point and `p=1`
exactly 10.

The two halves are two design statements, not two fitted terms:

- `sigmoid(16(p − 0.20))` is the **cliff**. Below `p = 0.20` — the most obvious fifth of the
  catalogue — an answer earns almost nothing (1.0–4.4 points). Above it, depth takes off fast.
  This is what makes the game _about_ rarity instead of about trivia knowledge.
- `0.35·p` is the **ladder**. Above the cliff, every extra percentile still buys points, so the
  top end never goes dead. This term is the only reason p90 clears 600 without a 20 pp plateau.

### 4.1 What one answer is worth (from `--chosen`, k already rounded)

| p    | k    | depth | in words                                  |
| ---- | ---- | ----- | ----------------------------------------- |
| 0.00 | 1.0  | 10 m  | the single most common answer in the pool |
| 0.01 | 1.1  | 11 m  |                                           |
| 0.05 | 1.4  | 14 m  | obvious answer                            |
| 0.10 | 2.1  | 21 m  | top-of-mind answer                        |
| 0.20 | 4.4  | 44 m  | cliff: "rarer than most, still common"    |
| 0.30 | 6.7  | 67 m  |                                           |
| 0.40 | 7.8  | 78 m  |                                           |
| 0.50 | 8.3  | 83 m  | median-catalogue answer                   |
| 0.60 | 8.7  | 87 m  |                                           |
| 0.70 | 9.0  | 90 m  |                                           |
| 0.80 | 9.4  | 94 m  |                                           |
| 0.90 | 9.7  | 97 m  |                                           |
| 0.99 | 10.0 | 100 m | near-rarest                               |
| 1.00 | 10.0 | 100 m | rarest answer in the pool                 |

Inverse — the rarity an answer must beat to reach a score (this is what the ladder is cut
from, and what the reveal can state honestly):

| k   | p required | share of the pool rarer |
| --- | ---------- | ----------------------- |
| 2   | 0.0941     | 90.6 %                  |
| 3   | 0.1453     | 85.5 %                  |
| 4   | 0.1848     | 81.5 %                  |
| 5   | 0.2217     | 77.8 %                  |
| 6   | 0.2624     | 73.8 %                  |
| 7   | 0.3176     | 68.2 %                  |
| 8   | 0.4282     | 57.2 %                  |
| 9   | 0.6913     | 30.9 %                  |
| 9.5 | 0.8454     | 15.5 %                  |
| 10  | 1.0000     | 0 %                     |

### 4.2 Why these numbers

`--chosen`, 20 000 dives, ρ=0:

```
p10 272 | p50 420 | p90 603 | >=600 10.8% | <200 1.9% | perfect 0.00%
```

| Target            | Required          | Shipped                             | Verdict                                      |
| ----------------- | ----------------- | ----------------------------------- | -------------------------------------------- |
| Median depth      | 380–450 m         | **420 m**                           | met, mid-band (40 m of headroom down, 30 up) |
| p90               | > 600 m           | **603 m**                           | met, by 3 m                                  |
| Dives under 200 m | < 8 %             | **1.9 %**                           | met (4.2× margin)                            |
| Dead zone         | none that matters | **3.1 pp worst** (at `p=0.98`)      | met — 3 pp ≈ 7 answers in a 250-pool         |
| Score granularity | —                 | **91 distinct k**, none unreachable | finer than a 10-tier ladder by 9×            |

By skill class (median dive): casual **344 m**, solid **521 m**, expert **560 m** (expert p90
652 m). The spread between classes is the game: the class gap (216 m) is bigger than the
prompt-to-prompt noise inside a class, so the dive result _says something about the player_
instead of about luck.

Splitting dives into 150 m buckets, as a description of the distribution and not as a second
ladder (§5 explains why there isn't one): 0.1 % under 100 m, 6.5 % 100–249 m, 37.9 %
250–399 m, 35.3 % 400–549 m, 18.5 % 550–649 m, 1.9 % 650 m+.

**The cost, stated plainly:** the top 30 % of the pool is worth only 1.0 point (90 → 100 m).
The budget that would have gone to the extreme tail went instead to keeping a 55 %-casual
population out of the 200 m basement. If the product would rather have a breathing top end
than a 420 m median, the knob is `w` (§8): `w = 0.40` gives 409/591 with a 2.7 pp band.

One consequence worth naming before it surprises someone in playtest: **600 m is an expert
badge.** 40.7 % of expert dives and 15.1 % of solid dives clear it; casual dives clear it
essentially never (0.0 % of 11 000 simulated). The depth a player can reach is a statement
about their rarity vocabulary — which is the honest read for this game, but it does mean the
"great dive" screen is something most casuals see in a stream, not on their own phone.

### 4.3 TypeScript-ready

Integer metres are the source of truth; points exist only for display. No float drift, so a
stored dive re-scores bit-identically.

```ts
// src/game/scoring.ts

export const PROMPTS_PER_DIVE = 7;
export const SECONDS_PER_PROMPT = 25;
export const METRES_PER_POINT = 10;

// ── the vein curve ─────────────────────────────────────────────────────────
const W = 0.35; // share of the scale that is linear in p — keeps the top alive
const A = 16; // cliff steepness
const B = 0.2; // cliff position: below this rarity, gravel
const sigmoid = (x: number): number => 1 / (1 + Math.exp(-x));
const shape = (p: number): number => W * p + (1 - W) * sigmoid(A * (p - B));
const G0 = shape(0); // 0.025457720
const G1 = shape(1); // 0.999998206

export const clamp01 = (p: number): number => (p < 0 ? 0 : p > 1 ? 1 : p);

/** Depth in whole metres for one answer of rarity percentile p. Always 10..100. */
export function depthForRarity(p: number): number {
  const k = 1 + (9 * (shape(clamp01(p)) - G0)) / (G1 - G0); // 1..10 points
  return Math.min(100, Math.max(10, Math.round(k * 10))); // 0.1 point == 1 m
}

/** A wrong or blank answer is 0 m — not a floor. */
export const depthForAnswer = (p: number | null): number => (p === null ? 0 : depthForRarity(p));

export function diveDepth(answers: ReadonlyArray<number | null>): number {
  return answers.reduce<number>((total, p) => total + depthForAnswer(p), 0);
}

/* p from the catalogue ---------------------------------------------------
   Sort the pool by rarity (ascending, index 0 = most common). rank is 1-based.
   rank N -> p = 1 (the rarest thing anyone could answer).
   Never derive p from live player answers: that is fake scarcity (§9).      */
export const rarityPercentile = (rank: number, poolSize: number): number => rank / poolSize;

/* the audit line the reveal prints ---------------------------------------
   "8º mais raro de 250" and "top 3,2%" are the same fact twice;
   rankFromRare / N == top share.                                   */
export function rankFromRare(p: number, poolSize: number): number {
  return Math.max(1, Math.min(poolSize, Math.round((1 - p) * poolSize) + 1));
}

/* named bands ------------------------------------------------------------ */
const STRATA = [
  { name: "Barranco", kLo: 1.0 }, // 10-39 m
  { name: "Cascalho", kLo: 4.0 }, // 40-69 m
  { name: "Aluvião", kLo: 7.0 }, // 70-89 m
  { name: "Veio", kLo: 9.0 }, // 90-95 m
  { name: "Pepita", kLo: 9.6 }, // 96-100 m
] as const;

export function stratumFor(depthMetres: number): string {
  const k = depthMetres / METRES_PER_POINT;
  let name: string = STRATA[0].name;
  for (const s of STRATA) if (k >= s.kLo) name = s.name;
  return name;
}
```

Invariants worth a unit test:
`depthForRarity(0) === 10`, `depthForRarity(1) === 100`, `depthForRarity` is
non-decreasing, `diveDepth([1,1,1,1,1,1,1]) === 700`, `diveDepth([null×7]) === 0`, and no
input yields a depth outside `[10,100]`.

---

## 5. The depth ladder

The ladder is **narrative only**. Bucketing lost the head-to-head (§2), so scoring stays
continuous and the names are cut from the score axis: each rung is a band of points, and the
rarity threshold that opens each rung is published so the label never overclaims.

| Rung         | Points   | Per-answer depth | Opens at `p` | Pool share | Flavour                                              |
| ------------ | -------- | ---------------- | ------------ | ---------- | ---------------------------------------------------- |
| **Barranco** | 1.0–3.9  | 10–39 m          | `p < 0.1848` | 18.5 %     | the overburden: the answers everybody types          |
| **Cascalho** | 4.0–6.9  | 40–69 m          | `p ≥ 0.1848` | 13.3 %     | gravel: you thought about it, but it is a known fact |
| **Aluvião**  | 7.0–8.9  | 70–89 m          | `p ≥ 0.3176` | 37.4 %     | the wide working band: solid, not special            |
| **Veio**     | 9.0–9.5  | 90–95 m          | `p ≥ 0.6913` | 18.5 %     | the vein: a genuinely rare answer                    |
| **Pepita**   | 9.6–10.0 | 96–100 m         | `p ≥ 0.8763` | 12.4 %     | a nugget: top ~12 % of the pool                      |

Exact `p` edges, unrounded: `0.184783 · 0.317551 · 0.691332 · 0.876281` — the rarity at which
the curve reaches 4.0 / 7.0 / 9.0 / 9.6 points. They are derived by inverting the curve, not
hand-set: retune the curve and the edges move with it (`p_of_k` in the tool).

Two rules that keep the ladder from becoming a scoreboard again:

1. **The reveal badges the answer's rung; the dive summary badges the dive's best find**
   ("seu melhor achado: Veio") next to the total metres. There is deliberately no second
   "dive depth ladder": a sum is a score, and inventing a second set of bands over totals is
   exactly how dead zones come back in through the side door.
2. Naming is a _depth_ claim, not a rarity claim. Rarity is always shown as its own number
   (percentile + rank + pool size). A rung name never appears without the number that proves it.

---

## 6. The reveal: 2 s after submit

One card, four beats, no new screen, no modal. The timer for the next prompt starts at
`t = 2000 ms`, so the reveal never eats answer time.

| Time         | On screen                                                                                                                                                                                                    | Rule                                                                                                                                                                                                                  |
| ------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 0–250 ms     | **Your answer**, exactly as typed, with the catalogue label if an alias matched (`"ceara" → Ceará`). Not in the pool: `não catalogada`, in the same slot — never an error state.                             | Never show a red X. A miss is data, not a scolding.                                                                                                                                                                   |
| 250–750 ms   | **The two proof numbers.** Headline `top 3,2%` counts up; underneath, one audit line: `8º mais raro de 250 respostas · acervo 2026.02.11`.                                                                   | This is "the number that proves it": a **rank over a stated N**, plus the catalogue version. The two figures are the same fact twice (`8/250 = 3,2 %`); percentile alone is a claim, rank + N + version is checkable. |
| 750–1350 ms  | **One more-common answer you missed.** The catalogue entry nearest _below_ your answer in rarity (strictly more common, different entry), with its own percentile: `Você passou perto: Tocantins — top 41%`. | Rarity only. **Never its points** — quoting what you could have scored turns a fact into a fine. If your answer was the pool's most common, show the 5th most common so the slot is never empty.                      |
| 1350–1800 ms | **The new depth.** `+97 m` travels into the depth bar; the running total lands: `437 m`, with the rung badge.                                                                                                | The only place the score is named.                                                                                                                                                                                    |
| 1800–2000 ms | Settle. `Continuar` appears; auto-advance at 2000 ms.                                                                                                                                                        | Tapping early advances immediately — waiting is never rewarded, skipping is never punished. The card stays in the dive log either way.                                                                                |

Hard rules for the beat:

- **Blank / wrong:** same card, no percentile, `não catalogada`, `+0 m`, and the missed-answer
  slot shows the prompt's _easiest_ catalogued answer with its rarity — help, not a taunt.
  Because the daily dive is scored once, this leaks nothing.
- **Never shown:** what other players answered, live answer counts, a projected rank, "you were
  12 m from a record", a countdown, or a share prompt (share lives on the end screen only).
- **Reduced motion:** numbers set instantly, the bar jumps, the card holds the same 2 s. The
  count-up is `aria-live="off"`; the final values are announced once, politely, after beat 4.
  Rung names are text, never colour alone. `Continuar` is ≥44 px.
- The reveal is the only place `p` appears; it is never shown during the 25 s prompt (knowing
  the pool as you type would turn the game into a lookup drill).

---

## 7. Session shape

| Mode                          | Seed                                                     | Scored?                              | Notes                                                                                                                                                |
| ----------------------------- | -------------------------------------------------------- | ------------------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------- |
| **A descida do dia** (daily)  | `YYYY-MM-DD` in `America/Sao_Paulo`, day flips 00:00 BRT | **Yes — one scored attempt per day** | Same 7 prompts for everyone. A second attempt is `treino`: it never overwrites the recorded depth and never touches the streak.                      |
| **Garimpo livre** (unlimited) | a number the player types, or `aleatório`                | No leaderboard                       | Unlimited practice. Counts for personal bests and for freeze-token progress (§7.2), never for the daily board.                                       |
| **Arquivo** (archive/log)     | —                                                        | read-only                            | Last 60 dives, daily and free, each replayable as `treino`. The archive is the anti-FOMO answer: nothing is ever lost, so nothing needs a countdown. |

### 7.1 What persists (localStorage)

One namespaced key, `garimpo.v1`, **written once at the end of a dive** (atomic, no per-prompt
writes), versioned, no PII, no analytics id, no network copy of the player's text.

```json
{
  "v": 1,
  "streak": { "current": 12, "best": 19, "lastDay": "2026-02-11", "freezes": 2, "earned": 7 },
  "dives": [
    {
      "day": "2026-02-11",
      "mode": "daily",
      "seed": 20260211,
      "total": 437,
      "catalogue": "2026.02.11",
      "best": "Veio",
      "prompts": [
        { "id": "uf-03", "answer": "Tocantins", "p": 0.9167, "m": 97 },
        { "id": "esc-01", "answer": null, "p": null, "m": 0 }
      ]
    }
  ],
  "prefs": { "motion": "full", "sound": true },
  "seen": { "howto": true, "revealHint": false }
}
```

- `dives` is capped at 60 entries, oldest pruned first; `p` is stored **with** the catalogue
  version so an archived dive can be re-scored and audited later.
- `answer` is the player's own text, stored locally only (it is their archive), never sent.
- Unknown `v`: show "acervo atualizado", keep the archive read-only, **never wipe it**.
- A dive is written only when it ends, so a killed tab loses one dive, never the archive.

### 7.2 Streak that does not punish a missed day

- The streak counts **daily dives only**, and only the first scored one of the day.
- A dive on day `D` extends the streak when the previous counted day is `D−1`.
- When it is not, **a ficha is spent automatically and silently** — one ficha per skipped day,
  the streak continues, the log records `ficha usada em 14/02`. No modal asking permission:
  asking permission _is_ the punishment.
- **Fichas are earned, never bought:** 1 per 3 completed dives (any mode), hold at most 3, never
  expire, never giftable, not in the store, not in the pass, not in an ad. They are a buffer,
  not a currency.
- With 0 fichas and a gap, the streak resets to 1 on today's dive. No red screen, no "você
  perdeu sua sequência" — the number simply reads `1`, and the archive still shows the old run
  ("sequência anterior: 19 dives, até 09/02").
- A 3-day holiday costs 3 fichas and keeps a long streak; scarcity still keeps the streak
  meaningful. The streak **never gates content**: no prompt, mode or cosmetic is locked behind it.

Monthly rhythm this produces, at the modelled distribution: a median player lands at 420 m with
their best answer in Aluvião or Veio; 600 m arrives about once a week (10.8 % of dives) and
650 m+ about once a month (1.9 %). A perfect 700 m dive is possible in principle and did not
occur once in 20 000 simulated dives — the ceiling stays a story, not a routine.

---

## 8. Sensitivity, the knobs, and the pool-size requirement

Measured with the shipped curve, 20 000 dives per row.

**Audience mix** (casual/solid/expert → p50 / p90 / under-200):

| mix                  | p50     | p90     | <200      |
| -------------------- | ------- | ------- | --------- |
| 70/25/5              | 381     | 568     | 2.4 %     |
| **55/30/15 (brief)** | **420** | **603** | **1.9 %** |
| 45/35/20             | 449     | 616     | 1.5 %     |
| 40/35/25             | 465     | 624     | 1.2 %     |

The 380–450 target band is, in effect, the whole plausible span of the assumed mix. That is a
feature: the curve was tuned at the middle, so a wrong guess about the audience moves the median
to the edge of the band, not out of it.

**Miss rate** (wrong/blank per prompt → p50 / p90 / <200): 6 % → 447/624/0.6 % · **12 % →
420/603/1.9 %** · 18 % → 388/570/4.0 % · 25 % → 354/541/**8.0 %**. The under-200 budget is
consumed by misses faster than by anything else: above ~25 % the target breaks even with a
better curve, and the fix would be a floor lift, not a redesign.

**Within-dive correlation ρ** (0 = the brief's iid model, 0.75 = players are very streaky):

| ρ    | p50 | p90 | <200      | ≥600   |
| ---- | --- | --- | --------- | ------ |
| 0    | 420 | 603 | 1.9 %     | 10.8 % |
| 0.25 | 425 | 607 | 2.4 %     | 11.3 % |
| 0.50 | 436 | 610 | 4.5 %     | 11.8 % |
| 0.75 | 448 | 614 | **8.4 %** | 12.7 % |

Streakiness does not break the curve — it lifts the top and fattens the low tail at the same
time. The first target to fail is "under 200 m", at ρ ≈ 0.7. The shipped constants were tuned on
the iid case, which is the conservative one for the median.

**The three knobs** (all in `tools/sim/curve.py`, all re-runnable in seconds):

| Knob                           | Effect                                                                               | When to turn it                                                                          |
| ------------------------------ | ------------------------------------------------------------------------------------ | ---------------------------------------------------------------------------------------- |
| `B` (cliff position, now 0.20) | the **median** knob. 0.16 → base 435 / casual-heavy 405; 0.18 → 428 / 394            | median lands under 380 in the live data: lower `B` by 0.01–0.02                          |
| `A` (steepness, now 16)        | sharpness of the cliff; barely moves the median, changes how legible the boundary is | if playtests show players can't tell a 0.15 answer from a 0.25 one                       |
| `W` (linear share, now 0.35)   | the **top-end** knob. 0.30 → p90 616, band 3.6 pp; 0.40 → p90 591, band 2.7 pp       | if fewer than ~8 % of dives reach 600 m, lower `W`; if the top feels saturated, raise it |

Two things bound everything above — one hard requirement, one open assumption.

1. **Pool size floor: `N ≥ 40` for any scored prompt** (worst case 6.8 m per rank at the cliff;
   at `N = 60` it is 4.5 m). `p = rank/N` needs a rarity-sorted pool with 1-based ranks. This is
   not a nice-to-have — see the audit below.
2. **Skill expressed as `p`** assumes a player who knows the rare answer _picks_ the rare answer.
   A player who knows the answer but types the famous variant is scored at the variant's `p`.
   That is the design, but two mitigations are mandatory for it to feel fair: every scored pool
   must contain the 5 most obvious correct answers (so "right but not listed" ≈ never happens),
   and the reveal's copy for a common-but-correct answer is `a resposta certa era comum`, never
   `errado`.

### 8.1 The catalogue does not yet meet the pool floor

From `reports/dataset.md` (snapshot 2026-11-04): 90 prompts, 2 931 catalogued answers, pool
sizes from 3 to 319 — **median 15**.

| Prompt pools with | Count | Share of 90 |
| ----------------- | ----- | ----------- |
| `N < 5`           | 7     | 8 %         |
| `N < 10`          | 28    | 31 %        |
| `N < 20`          | 53    | 59 %        |
| `N < 40`          | 68    | **76 %**    |
| `N < 60`          | 74    | 82 %        |

Under the shipped curve that is not a rounding detail — it is a scoring bug with a price:

| `N` | One rank | Worst metres per rank | Depth of the _most common_ answer |
| --- | -------- | --------------------- | --------------------------------- |
| 3   | 33.3 pp  | 90.8 m                | **72 m**                          |
| 5   | 20.0 pp  | 54.5 m                | 44 m                              |
| 9   | 11.1 pp  | 30.3 m                | 23 m                              |
| 27  | 3.7 pp   | 10.1 m                | 13 m                              |
| 60  | 1.7 pp   | 4.5 m                 | 11 m                              |
| 250 | 0.4 pp   | 1.1 m                 | 10 m                              |

Two distinct failures:

1. **Granularity.** A 3-answer prompt can only produce `p ∈ {1/3, 2/3, 1}` — 72, 89, 100 m. One
   rank of difference is worth 17–28 m on one answer.
2. **Directional bias.** Because `p = rank/N`, the _most obvious_ answer in a 3-answer pool pays
   **72 m**, while the most obvious answer in a 250-answer pool pays **10 m**. Small pools pay
   more for worse answers — up to 62 m per prompt, and ~430 m on a dive that drew seven of them.
   Concretely: `Cite um estado do Sul` (3 answers) has a 72 m floor; `Cite uma cidade brasileira`
   (319 answers) pays 10 m for "São Paulo".

It is not literally wrong — a 3-answer prompt really has no obvious tier for a player to avoid —
but it means `p` is not comparable across prompts, and comparable metres is the entire promise.
Rules, in order of preference:

1. **Scored prompts need `N ≥ 40`.** On the current snapshot only 22 of 90 qualify, so growing
   pools is a launch dependency, not a polish item. The dataset loaders already take
   `limit=150–400`; the small pools are narrow queries, not a pipeline limit.
2. 40–59 is allowed but tagged `raso` in the catalogue, to be extended.
3. Below 40: practice/archive only, never personal bests.
4. CI gate on the catalogue: every prompt in the scored rotation asserts `pool_size >= 40`, and
   the daily seed builder fails loudly if the eligible set cannot cover the planned days.

---

## 9. Anti-manipulation checklist

**No fake scarcity**

- `p` comes from a **published, versioned catalogue snapshot**, and the reveal shows rank + pool
  size + version. Any player can recompute the number; nobody has to trust a scoreboard.
- **No live rarity.** Never compute `p` from what current players answered, never show "only 3
  people got this". It is spoofable by a handful of accounts, it makes the same answer worth
  different points on different days, and it manufactures pressure. Answer counts are not a
  feature.
- **No re-rolling.** Prompts are fixed per seed; no adaptive difficulty that makes a prompt
  rarer on the fly, no "shuffle for an easier one".
- `p` clamped to `[1/N, 1]`, `k` clamped to `[1, 10]`, depth computed from integer tenths of a
  point. Replays and audits reproduce exactly.
- Pools under `N = 40` are not eligible for scored prompts (§8.1).

**No notification spam**

- At most **one** local reminder per day, opt-in, offered after the first completed dive — never
  on by default.
- No streak-loss warnings ("você vai perder sua sequência"), no countdowns, no "seus amigos
  passaram você", no re-engagement ladder, no "sentimos sua falta".
- Copy states a fact, never a threat: `a descida de 11/02 está no acervo`. Truthfully — because
  of the archive, nothing is actually lost.
- No notification may reference a score, a rival, or a time limit.

**No paid advantage in scoring**

- Fichas: earned only (§7.2). Not purchasable, not giftable, not in a pass, not in a rewarded ad.
- No energy, no extra scored attempts, no score multiplier, no prompt re-roll, no "reveal the
  answer" purchase, no ad that grants metres.
- Ads, if any, sit **between** dives and pay out nothing. The only monetisation that is safe here
  is cosmetic (lantern, rig, card backs) and a supporter badge / ad-free pass.
- Leaderboard: per-seed, **one scored attempt per day**, ties broken by earliest completion. Paying
  cannot buy a slot, and practice runs are marked `treino` and never ranked.

**Scoring integrity**

- Repeating the same normalised answer within a dive scores the 1-point floor after the first
  use — one obscure answer cannot be typed seven times.
- Matching is normalised (case, accents, punctuation, catalogue aliases) against catalogue
  entries only; a miss is a miss, no partial credit, otherwise `p` stops meaning rarity.
- A stored dive keeps its `p` and catalogue version, so a retroactive curve change is a visible,
  versioned event rather than a silent rewrite of someone's archive.

---

## 10. What this design is betting on

1. **The fantasy is "rarer = deeper", not "smarter = deeper".** The curve spends its points on
   the 60th–90th percentile of rarity, which is where a real player can actually improve. The
   extreme tail is worth almost nothing extra (1 point over the top 30 %), which is deliberate:
   it keeps the ceiling a story and stops the game from becoming a lookup contest.
2. **Nobody should ever end a dive at zero.** 1.9 % under 200 m, 0.1 % under 100 m, and a
   guaranteed 10 m floor per correct answer. The retention risk is the 55 % casual block, and the
   curve is tuned for them while still letting experts clear 600 m on two dives out of five.
3. **One scored attempt per day, an archive that loses nothing, and a streak you cannot buy** are
   the whole anti-FOMO strategy. There is no mechanic in this loop that gets worse if the player
   leaves — which is the only version of a daily game that survives a year.
