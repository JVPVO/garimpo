# Garimpo — art direction

**Status:** direction sheet v1 · owner: art direction · consumer: implementation engineer
**Scope:** visual system, layout, strata engine, motion. Not scoring maths, not copy backlog.
**Constraint stated up front:** every number in this file is in px unless it is a metre or a
percentile. Nothing here is a wireframe sketch — everything is meant to be typed into code.

---

## 0. The three non-negotiables

If only three things from this sheet survive implementation, they are:

1. **The cross-section is not decoration, it is the layout.** The depth axis (0 → 700 m) is a
   printed survey plate that is present on every screen, flush to the left edge, and _always shows
   all 700 m_. You never scroll the shaft. Only the pin moves.
2. **The strata are drawn with hatch patterns, not fills.** Seven named bands, seven different
   pattern vocabularies (pebbles, bedding, cleavage, joints, veins, folds, indicator crystals).
   If a band can be recognised with the colour removed, the plate is correct.
3. **Rarity is never a colour.** Five tiers, five _silhouettes_, plus a tick count, plus the tier
   name in text. Colour is the last cue, not the first.

---

## 1. The idea in one sentence

> **On this screen, an answer's rarity becomes a metre of shaft — and the strata you cut through
> are the dataset's own rarity bands, so the cross-section you're standing in is the histogram.**

Everything else follows. The plate is a _geological survey of a corpus_, drawn as if a 19th-century
mining engineer had charted Portuguese Wikipedia. The seven named strata are not geology-flavoured
set dressing: each band owns a declared percentile window and publishes what share of the corpus
lands in it (`ardósia · p38–57 · 17% do acervo`). The depth axis and the rarity axis are the same
axis, printed once.

Note the two label voices, and do not merge them: the **round-screen tag** is `ARDÓSIA · P38–57`
(what your answer's rarity means, right now), and the **plate label** is `ardósia · 17% do acervo`
(what the rock contains, always). Same band, two questions.

Two consequences the engineer must preserve:

- **A published scale, measured once.** The plate's percentile windows are measured from where
  answers actually land in simulated 7-answer dives over the shipped corpus — not assumed from a
  formula. Those windows are build outputs (§9.2), and the method page reprints them with the date
  they were computed. The formula below is the _scale bar_, not the authority: it states what a
  percentile is worth in metres, so a reader can check the axis by hand.
- **Every answer digs.** Minimum 8 m even for a useless guess (you always move _some_ dirt). A
  shaft that does not move is a dead screen.

---

## 2. Palette

Nine tokens. Proportions are of painted surface across the five screens, not of code.

| Token        | Hex       | Role                                                                              | Surface share |
| ------------ | --------- | --------------------------------------------------------------------------------- | ------------- |
| `--void`     | `#0E0B09` | Frame, plate keylines, the space behind a gem, the 700 m floor                    | 6%            |
| `--rock-0`   | `#171210` | Default ground: page, prompt area, ledger                                         | 40%           |
| `--rock-1`   | `#221A14` | Raised surface: input strip, ledger cell, reveal eyebrow                          | 8%            |
| `--rock-2`   | `#2F241B` | Lamp pool, hover, pressed, selected filter                                        | 5%            |
| `--rock-3`   | `#423325` | 1px rules, timber props, dividers, disabled borders — **never text**              | 3%            |
| `--lamp`     | `#F2B65A` | The light: primary action, depth numerals, timer wick, stratum tag                | 6%            |
| `--lamp-low` | `#B0752E` | Secondary accent: pressed state, spent lamp, dust, tier chip border               | 2%            |
| `--paper`    | `#EADFC6` | Body + display text; and the _surface_ of reveal sheet, result sheet, method page | 27%           |
| `--iron`     | `#7B6E5E` | 1px hairlines, ticks, rules — **never text** (fails 4.5:1)                        | 3%            |

Derived, documented, not a tenth token: **`--ink-2: #B7A98F`** — secondary text. It is exactly
`--paper` at 78% over `--rock-0`, but as a _solid_ hex so it has one measurable contrast value.
Never reduce text contrast with `opacity`; use this token.

Gem colours are **data ink**, not UI tokens — see §6. They never appear on buttons, links, or chrome.

### 2.1 Measured contrast (WCAG 2.1, computed)

Body text = `--paper` and `--ink-2`. Both must clear 4.5:1 on every ground they sit on.

| Foreground             | on `--rock-0` | on `--rock-1` | on `--rock-2` | on `--rock-3` |
| ---------------------- | ------------- | ------------- | ------------- | ------------- |
| `--paper` `#EADFC6`    | **14.04**     | **12.95**     | **11.42**     | **9.16**      |
| `--ink-2` `#B7A98F`    | **8.04**      | **7.41**      | **6.54**      | **5.25**      |
| `--lamp` `#F2B65A`     | **10.27**     | **9.47**      | **8.36**      | **6.71**      |
| `--lamp-low` `#B0752E` | 4.80          | 4.43          | 3.91          | 3.14          |
| `--iron` `#7B6E5E`     | 3.75          | 3.45          | 3.05          | 2.44          |
| `--rock-3` `#423325`   | 1.79          | 1.65          | 1.46          | 1.00          |

Rules that fall out of the numbers:

- `--paper` on any of the four rock grounds: pass everywhere. This is why the design is legible
  without any glow.
- `--ink-2` passes down to `--rock-3` at 5.25 — safe for 12–15px support copy.
- **`--iron` and `--rock-3` are structure only.** `--iron` at 3.75 on the page ground is fine for a
  1px rule and illegal for a 12px caption. There is no third grey for text.
- `--lamp-low` clears 4.5 only on `--rock-0`. Allowed on large numerals (≥24px) at 3:1, and on
  1px rules; not on body copy over `--rock-1`/`--rock-2`.
- Inverted surfaces (reveal sheet, result strip, method page): `--ink` `#1A1108` on `--paper` =
  **14.07**. `--paper` on `--lamp` = 1.05 (illegal pair); `--ink` on `--lamp` = 10.30 (the legal
  pair, used for filled buttons).

### 2.2 How the light works

The lamp is a **value shift with a hard edge**, not a glow. Its pool is a `--rock-2` fill at 100%
opacity in a shape with a defined edge (or a `radial-gradient` that terminates at a stated radius
and never exceeds 22% alpha). No `box-shadow` blur above 8px anywhere in the app. No `backdrop-filter`.

---

## 3. Type

Three families, all Google Fonts, all with full Portuguese coverage (`ã ç õ á â é ê í ó ô ú à`).
Verify before shipping by rendering `SÃO PAULO · ARDÓSIA · CLIVAGEM · 700 m` in every face.

| Role    | Family            | Weights                            | Notes                                                                                                                                                                                                            |
| ------- | ----------------- | ---------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Display | **Fraunces**      | variable `400..900`, `opsz 9..144` | Headlines, prompt text, tier names, the result number's label. Set `font-optical-sizing: auto` — never hand-set `opsz`. Ink-trap / wonky forms appear at large optical sizes, which is the woodcut feel we want. |
| Text    | **IBM Plex Sans** | 400, 500, 600                      | UI, body, labels. Humanist, slightly industrial: reads as equipment lettering, not SaaS.                                                                                                                         |
| Mono    | **IBM Plex Mono** | 400, 500                           | All numbers: metres, percentiles, timers, ledger rows, axis ticks. `font-variant-numeric: tabular-nums slashed-zero`.                                                                                            |

```html
<link rel="preconnect" href="https://fonts.googleapis.com" />
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
<link
  href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400..900&family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500&display=swap"
  rel="stylesheet"
/>
```

The CSS2 API reliably exposes `opsz` and `wght`. Do **not** design against the `SOFT`/`WONK` axes;
if you want `WONK 1` on the home headline, self-host the variable TTF from the google/fonts repo and
set it behind `@supports (font-variation-settings: "WONK" 1)`. Treat it as an enhancement.

`font-display: swap` for text, `optional` for Fraunces (a swapped display face on a headline this
large is uglier than a system serif). Fallback stack is declared per token below.

### 3.1 Scale (390 → 1280)

Fluid between the two breakpoints with an exact linear interpolation, clamped at both ends:
`clamp(mobile, <slope>vw + <intercept>px, desktop)`.

| Token         | 390 px | 1280 px | Value                                  | Line-height | Tracking         |
| ------------- | ------ | ------- | -------------------------------------- | ----------- | ---------------- |
| `--fs-hero`   | 52     | 88      | `clamp(52px, 4.05vw + 36.2px, 88px)`   | 0.94        | −1.3px           |
| `--fs-meter`  | 56     | 96      | `clamp(56px, 4.49vw + 38.5px, 96px)`   | 1.00        | −2.0px           |
| `--fs-h1`     | 34     | 56      | `clamp(34px, 2.47vw + 24.4px, 56px)`   | 1.00        | −1.1px           |
| `--fs-prompt` | 24     | 30      | `clamp(24px, 0.67vw + 21.4px, 30px)`   | 1.28        | −0.2px           |
| `--fs-h3`     | 18     | 22      | `clamp(18px, 0.45vw + 16.3px, 22px)`   | 1.20        | 0                |
| `--fs-body`   | 16     | 17      | `clamp(16px, 0.11vw + 15.6px, 17px)`   | 1.55        | 0                |
| `--fs-ui`     | 14     | 15      | `clamp(14px, 0.11vw + 13.6px, 15px)`   | 1.35        | 0.1px            |
| `--fs-label`  | 11     | 12      | `clamp(11px, 0.11vw + 10.6px, 12px)`   | 1.15        | 1.5px, UPPERCASE |
| `--fs-mono-s` | 9.5    | 10.5    | `clamp(9.5px, 0.11vw + 9.1px, 10.5px)` | 1.30        | 0.2px            |

Family assignment:

- `--fs-hero`, `--fs-h1`, `--fs-prompt`, `--fs-h3` → Fraunces. Weights: hero 800, h1 700,
  prompt 550, h3 600.
- `--fs-body`, `--fs-ui`, `--fs-label` → IBM Plex Sans (400 / 500 / 600).
- `--fs-meter`, `--fs-mono-s` → IBM Plex Mono (500 / 400).
- `--fs-label` is the only uppercase + tracked style in the app. It is the survey-plate label
  voice — use it for stratum tags, axis names, section eyebrows. Never for buttons.

### 3.2 Headline copy (do not invent new ones)

The display face exists to carry 2–4 words. It is not for paragraphs.

| Screen      | Headline                            | Size        | Treatment                                                                         |
| ----------- | ----------------------------------- | ----------- | --------------------------------------------------------------------------------- |
| Home        | `Sete respostas.` ⏎ `Uma mina.`     | `--fs-hero` | Hard line break. All `--paper`. No accent-coloured word, no gradient, no outline. |
| Result      | `442 metros.` (or `Fundo do poço.`) | `--fs-hero` | All `--paper`.                                                                    |
| Log (empty) | `Nenhum poço` ⏎ `aberto.`           | `--fs-h1`   | `--paper`.                                                                        |
| Reveal      | tier name, e.g. `Esmeralda`         | `--fs-h3`   | `--ink` on paper.                                                                 |
| Method      | `Como medimos`                      | `--fs-h1`   | `--ink` on paper.                                                                 |

Prompts are set in Fraunces at `--fs-prompt` / 550 — the one place the display face does long-form.
Add `text-wrap: balance` on the prompt and `hyphens: none` (Portuguese hyphenation on 3-line
prompts produces ugly rivers; let it break at word boundaries).

Input text is **IBM Plex Sans 24px** on mobile / 26px on desktop. Never below 16px (iOS zoom) —
24px also gives the answer field the weight of an inscription, which is the point.

---

## 4. The strata system

### 4.1 The plate

One element, present on every screen, flush to the left edge at `x = 0`.

```
--plate-h: 100dvh
--px-per-m: calc(var(--plate-h) / 700)      /* ≈1.206 px/m at 390, ≈0.971 at 800 h */
```

Every band position is expressed in metres and multiplied by `--px-per-m`, so the plate is always
exactly 700 m tall and always fully visible. Never scroll it. Never crop it below 700 m.

```css
.stratum {
  position: absolute;
  left: 0;
  right: 0;
  top: calc(var(--px-per-m) * var(--from));
  height: calc(var(--px-per-m) * var(--thick));
  background-color: var(--fill);
  background-image: var(--hatch);
  background-repeat: repeat;
}
```

**Texture scale rule.** Hatch tiles are sized in _px_ (22–48 px), never in `%`. Mine rock is a
constant texture; the plate is a printed drawing at a fixed scale. This also means hatch never
stretches when the plate widens between screens.

**Tiling rule.** A pattern tile may only contain: full-width horizontal lines, closed periodic
curves that return to their start y with matching slope, and geometry that starts _and_ ends inside
the tile. Any other shape produces a visible seam every tile width. Every recipe below obeys this.

### 4.2 The seven strata

| #   | Depth     | Name (pt)  | Fill      | Pattern family              | p window | Share | Plate label                        |
| --- | --------- | ---------- | --------- | --------------------------- | -------- | ----- | ---------------------------------- |
| 1   | 0–20 m    | Solo       | `#3A2C20` | rounded pebbles + grit dots | p00–23   | 9%    | `argila com seixos · 9% do acervo` |
| 2   | 20–80 m   | Arenito    | `#2E2319` | broken horizontal bedding   | p23–38   | 14%   | `arenito friável · 14% do acervo`  |
| 3   | 80–180 m  | Ardósia    | `#26201A` | dense parallel cleavage     | p38–57   | 17%   | `ardósia, clivagem 76° · 17%`      |
| 4   | 180–320 m | Quartzito  | `#34291C` | offset jointed blocks       | p57–76   | 19%   | `quartzito maciço · 19% do acervo` |
| 5   | 320–460 m | Xisto      | `#221B15` | one long wavy quartz vein   | p76–88   | 16%   | `xisto com veios · 16% do acervo`  |
| 6   | 460–600 m | Gnaisse    | `#1D1712` | folded foliation + stipple  | p88–94   | 15%   | `gnaisse dobrado · 15% do acervo`  |
| 7   | 600–700 m | Kimberlito | `#16110D` | 4 sparse indicator crystals | p94–100  | 10%   | `kimberlito, mineral indicador`    |

`p window` is the p25–p75 of the answers that land in the band; `Share` is the proportion of
answer-segments landing there across the shipped corpus. **Both are build outputs.** The numbers
above are plausible placeholders so layout and copy can be built today — they are not authored by
hand and they are not rounded to look nice. If the build says ardósia holds 11%, the label says
11% and the design does not move.

Two deliberate reversals make this read as a drawing rather than a gradient:

- **The fill ramp is not monotonic.** Quartzito (`#34291C`, 180–320 m) is _lighter_ than the
  ardósia above it and the xisto below it. A hard, resistant bed drawn pale is the single most
  recognisable convention of a geological section. Keep it.
- **The bottom band is the quietest.** Kimberlito is nearly empty — four specks on `#16110D`, the
  darkest fill in the plate. Emptiness is the luxury cue; it makes the gem at 700 m the only bright
  thing. Do not add texture here to "balance" the composition.

The `% do acervo` figures above are **example values from the corpus simulation**. Recompute them
from the shipped corpus (`tools/` → `src/data/strata.json`) and keep the label grammar fixed:
`<nome> · <fact> · <share>% do acervo`. If a share changes to 23%, the label says 23%; the design
does not move. Do not invent a share that the build did not compute.

### 4.3 Depth contract

```ts
// scale bar: what one answer's rarity is worth in metres, printed on /metodo
// (the plate's printed percentile windows are measured from landing depth, not from this formula)
const refDepth = (p: number) => 700 * Math.pow(p, 1.5); // p ∈ [0,1], 1 = rarest

// live dive — one answer's contribution; seven of these fill 700 m
const dig = (p: number) => Math.max(8, Math.round(refDepth(p) / 4)); // 8..175 m

// dive
const depth = Math.min(
  700,
  answers.reduce((m, a) => m + dig(a.p), 0),
);
```

Sanity check of the resulting feel (keep these in the result copy):
median answer `p 0.50` → 62 m; strong answer `p 0.80` → 125 m; exceptional `p 0.97` → 165 m;
seven median answers → 433 m; seven strong answers → 700 m (bottom reached on answer 6).

### 4.4 Pattern recipes (exact, copy-paste)

Each is a CSS custom property holding an SVG data URI. `#` must be written `%23`. Do not switch to
base64 — these must stay readable in the repo.

**1 · Solo — argila com seixos.** Tile 24×20. Three stroked pebbles, rotated, + 2 grit dots.

```css
--hatch-solo: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='24' height='20'%3E%3Cg fill='none' stroke='%236B5539' stroke-width='1' opacity='.55'%3E%3Cellipse cx='5' cy='6' rx='3' ry='2.2' transform='rotate(-14 5 6)'/%3E%3Cellipse cx='16' cy='12' rx='3.6' ry='2.4' transform='rotate(9 16 12)'/%3E%3Cellipse cx='9' cy='17' rx='2.4' ry='1.8' transform='rotate(-6 9 17)'/%3E%3C/g%3E%3Cg fill='%236B5539' opacity='.4'%3E%3Ccircle cx='21' cy='4' r='.9'/%3E%3Ccircle cx='13' cy='8' r='.7'/%3E%3C/g%3E%3C/svg%3E");
```

**2 · Arenito — bedding.** Tile 34×18. Two full-width dashed lines at different dash rhythms (that
is the "beds"), plus two interior-only diagonal slivers (the cross-bedding). Full-width lines tile
perfectly; interior slivers cannot seam.

```css
--hatch-arenito: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='34' height='18'%3E%3Cg fill='none' stroke='%236B5539' stroke-width='1'%3E%3Cpath d='M0 6h34' stroke-dasharray='9 7' opacity='.5'/%3E%3Cpath d='M0 13h34' stroke-dasharray='13 9' opacity='.35'/%3E%3Cpath d='M12 9l5 4M24 4l4 4' opacity='.45' stroke-width='.9'/%3E%3C/g%3E%3C/svg%3E");
```

**3 · Ardósia — cleavage 76°.** Tile 12×24. One family of parallel lines whose horizontal run per
tile (6 px over 24 px height) is exactly `24 / tan 76°`. Two lines per tile; the second is the first
shifted 6 px, so the family is continuous across tiles by construction.

```css
--hatch-ardosia: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='24'%3E%3Cg fill='none' stroke='%237A6446' stroke-width='.9' opacity='.62'%3E%3Cpath d='M0 24L6 0'/%3E%3Cpath d='M6 24L12 0'/%3E%3C/g%3E%3C/svg%3E");
```

**4 · Quartzito — jointed blocks.** Tile 30×24. Two full-width horizontals (y 0 and 12) and two
interior verticals that stop 1 px short of the edges: at `x 8` in the upper course, `x 22` in the
lower. The offset is what makes it a bond, not a grid.

```css
--hatch-quartzito: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='30' height='24'%3E%3Cg fill='none' stroke='%236B5539' stroke-width='1' opacity='.55'%3E%3Cpath d='M0 0h30M0 12h30'/%3E%3Cpath d='M8 1v10M22 13v10' stroke-width='.9'/%3E%3C/g%3E%3Cg fill='%236B5539' opacity='.35'%3E%3Ccircle cx='15' cy='7' r='.8'/%3E%3Ccircle cx='27' cy='18' r='.6'/%3E%3C/g%3E%3C/svg%3E");
```

**5 · Xisto — quartz vein.** Tile 48×28. One full sine period as two cubics whose join at x=24 has a
matching tangent on both sides, returning to `y 14` at x=48. This is the signature rock of the plate;
give it 1.3 stroke weight and the brightest hatch colour.

```css
--hatch-xisto: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='48' height='28'%3E%3Cg fill='none' stroke='%238A7150' stroke-width='1.3' opacity='.7'%3E%3Cpath d='M0 14C8 6 16 22 24 14C32 6 40 22 48 14'/%3E%3C/g%3E%3Cg fill='none' stroke='%238A7150' stroke-width='.9' opacity='.4'%3E%3Cpath d='M6 4l4 4M30 24l4 3M20 2l3 3'/%3E%3C/g%3E%3C/svg%3E");
```

**6 · Gnaisse — folded foliation.** Tile 20×32. Two near-vertical periodic curves, each returning to
its start x at y=32 with matching slope, plus stipple. This is the only _vertical_ rhythm in the
plate — it reads as the rock being folded before it was cut.

```css
--hatch-gnaisse: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='20' height='32'%3E%3Cg fill='none' stroke='%236B5539' stroke-width='1' opacity='.45'%3E%3Cpath d='M6 0C9 5 3 11 6 16C9 21 3 27 6 32'/%3E%3Cpath d='M15 0C12 6 18 12 15 18C12 24 18 28 15 32'/%3E%3C/g%3E%3Cg fill='%236B5539' opacity='.5'%3E%3Ccircle cx='4' cy='9' r='.8'/%3E%3Ccircle cx='17' cy='7' r='.6'/%3E%3Ccircle cx='12' cy='25' r='.7'/%3E%3C/g%3E%3C/svg%3E");
```

**7 · Kimberlito — indicator minerals.** Tile 26×26. Four 1.8px squares rotated 45°, nothing else.
Deliberately ~70% empty.

```css
--hatch-kimberlito: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='26' height='26'%3E%3Cg fill='%238A7150' opacity='.55'%3E%3Crect x='3.2' y='5.2' width='1.8' height='1.8' transform='rotate(45 4.1 6.1)'/%3E%3Crect x='14.2' y='3.2' width='1.8' height='1.8' transform='rotate(45 15.1 4.1)'/%3E%3Crect x='8.2' y='16.2' width='1.8' height='1.8' transform='rotate(45 9.1 17.1)'/%3E%3Crect x='19.2' y='14.2' width='1.8' height='1.8' transform='rotate(45 20.1 15.1)'/%3E%3C/g%3E%3C/svg%3E");
```

### 4.5 Edges, ticks, labels

- **Strata contacts:** 1px `--void` line at the boundary, with a 1px `--iron` line at 55% directly
  below it. Two hairlines, not a shadow.
- **Depth axis:** ticks every 20 m, 3px long, `--iron`; every 100 m, 7px long, `--iron` + a
  `--fs-mono-s` numeral. On narrow rails (<120px) numerals are hidden and only the 100 m ticks
  survive; numerals reappear when the plate widens (result/log-detail).
- **Reached vs. not reached:** strata above the reached depth render at 100%; everything below
  renders at **45% opacity** with hatch at 30%. This is the ghost of the rock you did not cut, and it
  is the single most important honesty cue on the result screen. Do not fade it to nothing — at 45%
  the pattern must still be legible.
- **The 700 m floor:** a 3px `--void` band with one `--lamp` hairline above it. The gem sits on it.
- **Stratum tag** (round screen, top of the content column): `--fs-label`, `--lamp`, e.g.
  `ARDÓSIA · P38–57`. One line, never wraps (truncate the percentile if <340px wide).

---

## 5. Screen blueprints

Shared anatomy: `--plate` (left edge, full height) · top bar 44px · content column starting at
`--rail-w + 22px` (mobile) / `+ 56px` (desktop) · right gutter 22/72.

### 5.1 Home — "boca da mina"

```
0                                                    390
┌───────────────────────────────────────────────────────┐
│ GARIMPO                        pt.wikipedia · 700 m   │ 44 top bar, 1px rule
├───────────────────────────────────────────────────────┤
│▌▒▌│                                                  │
│▌▒▌│      ╱▔▔▔▔▔▔▔▔▔▔╲        ← collar 120×104       │
│▌▒▌│     │ ▏▏ ░ ░ ░  ▕│        overlaps the plate      │
│▌▒▌│      ╲▁▁▁▁▁▁▁▁▁▁╱         edge by 20px           │
│▌▒▌│                                                  │
│▌▒▌│  Sete respostas.                                 │ Fraunces 52/0.94
│▌▒▌│  Uma mina.                                       │
│▌▒▌│                                                  │
│▌▒▌│  Cada acerto desce o poço.                       │ Plex 16/1.55
│▌▒▌│  No fundo fica a resposta                        │ --ink-2
│▌▒▌│  mais rara que você souber.                      │
│▌▒▌│                                                  │
│▌▒▌│ ┏━━━━━━━━━━ DESCER ━━━━━━━━━━━━ 700 m ┓  ← 56  │
│▌▒▌│                                                  │
│▌▒▌│ diário · 03 nov      ilimitado · semente 8842 →  │ 44 rows
│▌▒▌│ arquivo 62 · método                              │
│▌▒▌│                                                  │
│▌▒▌│                                                  │
│▌▒▌│                                                  │
│▌▒▌│                                          ◇       │ the gem, unlit, 8px
└───────────────────────────────────────────────────────┘
 88px plate, all seven strata, no channel, hatched at 100%
```

- **Where the shaft is:** the plate is _un-dug_. All seven strata at full opacity, no channel, no
  pin. The unopened section is the hero image; the collar (a 120×104 woodcut) sits at the 0 m line
  and overlaps the plate's right edge by 20px, so the plate reads as something the object stands on.
- Desktop: plate widens to 296 and gains its full label column (labels were clipped on mobile — the
  widening _reveals_ them, it does not reflow them). Content 576 wide, ledger strip 232 at right.
- The home plate is the only place all seven bands are at 100% opacity. Do not add a "preview strip"
  anywhere; the plate already is the preview.
- **The gem at 700 m is present but unlit** (8px, `--rock-3` outline, `--lamp` 20%). It is a promise,
  not a reward.

### 5.2 Round — prompt, timer, input

```
┌───────────────────────────────────────────────────────┐
│ pergunta 3/7                                 0:17  ∎  │ 44
│██████████████████████▓░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░  │ wick 3px, lamp
├───────────────────────────────────────────────────────┤
│▌▌▌│                                                  │
│▌▌▌│  ARDÓSIA · P38–57              ← --fs-label lamp │
│▌▌▌│                                                  │
│▌▌▌│  Qual rio atravessa a capital                    │
│▌▌▌│  do Amazonas sem tocar no                        │ Fraunces 24/1.28
│▌▌▌│  rio Negro?                                      │
│▌▌▌│                                                  │
│▌▌▌│                                                  │
│▌▌▌│  Rio Negro▏                          ← 24px Plex │
│▌▌▌│  ──────────────────────────────────             │ rule 1px rock-3
│▌▌▌│  enter para cravar                 ← 12px ink-2 │
│▌▌▌│                                                  │
│▌▌▌│ ┏━━━━━━━━━━━ CRAVAR ━━━━━━━━━━━━━━━┓ ← 56      │
│▌▌▌│                                                  │
│▌▌▌│                                                  │
│▌▌▌│                                          214 m   │ mono 56, lamp
│▌▌▌│                                    ← --fs-meter  │
└───────────────────────────────────────────────────────┘
 44px plate: hatch + 10px channel (x 14–24) + pin at 214 m
```

```
1280×800
┌───────────────────────────────────────────────────────────────────────┐
│ GARIMPO   ilimitado · semente 8842              03/07   0:17      ▽   │
├──────────────────┬───────────────────────────────────┬────────────────┤
│ 0 m ───────────  │                                   │ LEDGER         │
│ ▨▨▨  argila   9% │  ARDÓSIA · P38–57                 │ 1 ◈ esmer. 122 │
│ 20 ────────────  │                                   │ 2 ◈ gran.   64 │
│ ▤▤▤  arenito 14% │  Qual rio atravessa a capital     │ 3 ◈ esmer.  28 │
│ 80 ────────────  │  do Amazonas sem tocar no         │ ─────────────  │
│ ▧▧▧  ardósia 17% │  rio Negro?                       │ PROFUNDIDADE   │
│ ░░▐▌░░░░░░░░░░░  │                                   │ 214 m          │
│ ▧▧▧              │  Rio Negro▏                       │ ardósia        │
│ 180 ───────────  │  ────────────────────────────     │ p38–57         │
│ ▩▩▩  quartzito   │  enter para cravar                │                │
│ ...              │  ┏━━━━━ CRAVAR ━━━━━━━┓           │                │
└──────────────────┴───────────────────────────────────┴────────────────┘
   296px plate with labels      576px stage               232px ledger
```

- **Timer is oil, not a ring.** A 3px full-bleed bar under the top bar, `--lamp`, draining right to
  left with `transform: scaleX()` and `transform-origin: right`, `linear`, 25 s, driven by one CSS
  animation (or one rAF, not a 1s interval — the bar must be smooth). The mono `0:17` is the
  redundant readout. **Last 7 s:** the bar narrows 3px → 2px and the numerals jump 500 → 600 weight
  and gain a 1px `--lamp` under-rule. No colour change, no pulsing, no shaking. Under
  `prefers-reduced-motion` keep the bar but run it `animation-timing-function: steps(25, end)`.
- **Input is a ruled line, not a box.** 1px `--rock-3` bottom rule on a transparent field; focus
  swaps the rule to 2px `--lamp` **via `box-shadow`, not `border-width`** (`box-shadow: 0 2px 0
  var(--lamp)`) so nothing reflows. `caret-color: var(--lamp)`. Autofocus on mount, `autocapitalize`
  off, `spellcheck` off, `enterkeyhint="go"`.
- Button 56px tall, full column width, fill `--lamp`, label `--ink` 15px/600, 1.5px `--lamp-low`
  bottom edge (letterpress, no border-radius except 2px). Disabled: fill transparent, 1.5px
  `--rock-3` keyline, label `--iron`.
- The depth readout sits bottom-right of the column, `--fs-meter`, `--lamp`, tabular, in a fixed
  196px block so counting up cannot cause layout shift.
- The pin: a 10px `--lamp` ellipse at the channel's bottom with a 1px `--void` keyline; the channel
  is a 10px `--lamp` at 26% fill with 1px `--lamp` edges. Timber props: 14×3px `--rock-3` bars every
  100 m, protruding 2px each side of the channel.
- Desktop: plate 296 with right-aligned labels (name + share), channel at x 20–30. Stage 576,
  prompt capped at 30ch. Ledger 232: seven rows (index, gem 16px, tier name, metres) + a
  `PROFUNDIDADE` block. The ledger is live during the round — past answers stay visible.

### 5.3 Reveal — answer + rarity proof

```
┌───────────────────────────────────────────────────────┐
│ pergunta 3/7 · respondida                    0:00     │
├───────────────────────────────────────────────────────┤
│▌▌▌│                                                  │
│▌▌▌│  ┌───────────────────────────────────────────┐   │ ← paper sheet
│▌▌▌│  │ VOCÊ                                  ← 11  │   │
│▌▌▌│  │ Rio Amazonas                     ← 26 ink  │   │
│▌▌▌│  │ ────────────────────────────────────────  │   │
│▌▌▌│  │ vulgo                      rio Amazonas   │   │
│▌▌▌│  │ ────────────────────────────────────────  │   │
│▌▌▌│  │  ◈        Esmeralda          p 71         │   │
│▌▌▌│  │  88px     corte esmeralda                 │   │
│▌▌▌│  │           380–520 m                       │   │
│▌▌▌│  │ ────────────────────────────────────────  │   │
│▌▌▌│  │ atenção  ▓▓▓▓▓▓▓▓▓░░░  1,4 M/mês          │   │
│▌▌▌│  │ sitelinks▓▓▓▓▓▓░░░░░░       47 wikis      │   │
│▌▌▌│  │ corpus   ▓▓▓▓▓▓▓▓▓▓░░     4,1 ppm        │   │
│▌▌▌│  └───────────────────────────────────────────┘   │
│▌▌▌│                                                  │
│▌▌▌│ ┏━━━━━━━━━━━ PRÓXIMA · 4/7 ━━━━━━━━━━━━━━┓ 56   │
└───────────────────────────────────────────────────────┘
 sheet: left 12, right 0, top 340, bottom 0 · 1px ink keyline on top+left
```

- **The sheet is paper, and it is the inversion.** `--paper` ground, `--ink` text, 0 border-radius
  except a 2px top-left corner. It covers the content column but leaves a 12px sliver of plate at
  the far left, so the shaft never disappears from the screen.
- **The rarity proof is three engraved bars, not a score.** Each row: an 11px `--fs-label` signal
  name, an 8px-tall bar (fill `--ink` at 88%, track `--ink` at 10%), the value in mono 13px. Bars
  normalise _within the prompt's answer universe_ — say so on the method page. The percentile `p 71`
  is the number that matters and is set in mono, right-aligned.
- Order on the sheet is fixed: **your answer → the canonical name → tier gem + p → the three
  signals → button.** Never lead with the tier; the tier is a consequence.
- Under 380px width the gem drops below the tier text (single column); at 390 it sits left of it.
- Desktop: sheet 352→1216, top 120, bottom 64, with a 1px `--void` shadow-edge of 3px (hard edge,
  not blur) and the gem at 104px.

### 5.4 Result — shaft summary

```
┌───────────────────────────────────────────────────────┐
│ RESULTADO · 03 nov        442 m · 3 gemas · p 71      │
├───────────────────────────────────────────────────────┤
│0 m▒▒▒│▐▌│                             argila · 9%     │
│     ▒│▐▌│                                             │
│ 20 ──┼──│─────────────────────       arenito · 14%   │
│     ░│▐▌│                                             │
│     ░│▐▌│                                             │
│ 80 ──┼──│─────────────────────       ardósia · 17%   │
│     ░│▐▌│                                             │
│     ░│▌▐│ ①                                           │
│180 ──┼──│─────────────────────     quartzito · 19%   │
│     ▓│▐▌│                                             │
│     ▓│▌▐│      ②    ③                                 │
│320 ──┼──│─────────────────────         xisto · 16%   │
│     ▓│▐▌│                                             │
│460 ──┼──│─────────────────────       gnaisse · 15%   │
│     █│▐▌│ ④                                           │
│600 ──┼──│─────────────────────    kimberlito · 10%   │
│     █│▐▌│          ⑤   ⑥   ⑦                          │
│700 ══╧══╧══════════════════════ ◇ fundo (não batido)  │
├───────────────────────────────────────────────────────┤
│ 442 metros.   ▪▪▪▪▪             [refazer]  [diário →] │
└───────────────────────────────────────────────────────┘
 plate full-bleed 390 · channel x 96–120 · marks ①②… 9px mono
```

- **The plate becomes the page.** Full-bleed width, channel down the middle at x 96–120, strata
  labels right-aligned at x 370, depth ticks at the left edge. This is the screen where the whole
  design argument is visible at once.
- The seven answers are **marks struck on the channel's face** at their cumulative depth: a 5px
  `--lamp` square rotated 45°, with a 9px mono index to its right. Shallower marks stack visibly at
  the top; that is the story of a dive.
- Gem finds are drawn on the mark in the tier's silhouette at 18px (`--lamp` keyline 1px).
- Un-reached rock below the depth: 45% opacity (§4.5). The bottom gem is drawn unlit at `--rock-3`
  unless 700 m was reached, in which case it is the tier-5 brilliant at 32px in `--lamp`, with the
  only static highlight facet in the app.
- Headline `442 metros.` bottom-left in Fraunces, `--fs-hero`, `--paper`. Beside it, five 6px tick
  marks = tier reached (not a percentage bar).
- Desktop: plate 0→560 with labels on both sides (names left, shares + marks right), result card
  608→928 on paper, ledger of the 7 answers 960→1208.

### 5.5 Log / archive, and method

```
┌───────────────────────────────────────────────────────┐
│ ARQUIVO                    62 mergulhos · 41 dias     │ 44
├───────────────────────────────────────────────────────┤
│ todos │ diário │ ilimitado        ← 44px filter row   │
├───────────────────────────────────────────────────────┤
│ ▌ 03 nov · diário        442 m    ◈                   │
│ ▌▌                       462 m    ◇                   │ 88px rows,
│ ▌▌▌                                                  │ 12px mini-plate
│ ────────────────────────────────────────────────────  │
│ ▌ 02 nov · ilimitado     318 m    ◈                   │
│ ▌▌                                                   │
│ ────────────────────────────────────────────────────  │
│ ▌ 02 nov · ilimitado     605 m    ◆                   │
│ ▌▌▌▌                                                 │
└───────────────────────────────────────────────────────┘
```

- Each row carries a **12×56 mini-plate**: the same seven strata, a channel, and 7 notches as 1px
  marks. It is a real thumbnail of that dive, generated from the same `--hatch-*` tokens — not an icon.
- Row height 88, separated by a 1px `--rock-3` rule (no cards, no shadows). Depth in mono
  right-aligned at x 300; tier gem 16px at x 330. Tap → pushes the result plate for that dive.
- Empty state: `Nenhum poço aberto.` in `--fs-h1` + an un-dug mini-plate at 88×120 + the primary
  "descer" button. No illustration of a sad miner.
- **Method page is the paper screen.** `--paper` ground, `--ink` text, two columns at 1280 (each
  460 wide, 48 gutter), one column at 390. Content: the label grammar, the reference-plunge table
  (`p` → m, 11 rows), the tier table with silhouettes at 24px, the three signals with their sources
  and refresh dates, and the strata legend rendered with the live patterns at 1:1. Set the plate
  legend in a bordered table with 1px `--ink` rules at 30% — this is the one place we look like a
  printed plate, so allow the extra ink.

### 5.6 How the shaft travels between screens

The plate is **one persistent element**, hoisted above the router (`position: fixed; left: 0;
top: 0; height: 100dvh`). Its inner drawing is a fixed 390px (mobile) / 296px (desktop) wide layer;
its visible column is a wrapper with `width: var(--rail-w); overflow: hidden`. Animating the wrapper
width therefore _reveals_ label columns from under the edge instead of reflowing them, and the hatch
never stretches.

| Screen     | `--rail-w` (390)                     | `--rail-w` (1280) | Channel         | Labels                                |
| ---------- | ------------------------------------ | ----------------- | --------------- | ------------------------------------- |
| Home       | 88                                   | 296               | none            | clipped on mobile, visible on desktop |
| Round      | 44                                   | 296               | 10px at x 14–24 | clipped / visible                     |
| Reveal     | 44                                   | 296               | same as round   | same                                  |
| Result     | 390 (full-bleed)                     | 560               | 24px centred    | revealed + right column               |
| Log        | 0 (rows carry their own mini-plates) | 0                 | —               | —                                     |
| Log detail | 390                                  | 560               | as result       | as result                             |
| Method     | 0 (paper page)                       | 0                 | —               | —                                     |

Transitions: `width` 420 ms `cubic-bezier(.22,.68,.12,1)` on the wrapper, and a matching
`translateX` on the content column so text does not jump under a moving plate. On the log, the plate
collapses to 0 px and the mini-plates carry the metaphor; returning from a dive briefly expands the
plate back to full-bleed before settling — one shared-element move, 420 ms, no crossfade.

---

## 6. Gems and rarity encoding

Five tiers. Each is a **silhouette** first, a colour second, a label third. All five are drawn in a
64×64 user space with 1.25px strokes (`vector-effect: non-scaling-stroke`), flat fill, one facet
highlight, zero gradients, zero filters.

| Tier | Mineral         | Cut                       | Fill      | Depth     | Percentile | Tick marks | Stroke |
| ---- | --------------- | ------------------------- | --------- | --------- | ---------- | ---------- | ------ |
| I    | Quartzo leitoso | **brutes** (raw fragment) | `#CFC6B4` | 0–180 m   | p 0–40     | 1          | 1.0    |
| II   | Granada         | **cabochon** (dome)       | `#C0503A` | 180–380 m | p 40–65    | 2          | 1.2    |
| III  | Esmeralda       | **emerald cut** (step)    | `#35996B` | 380–520 m | p 65–82    | 3          | 1.4    |
| IV   | Ametista        | **octagon**               | `#8A6ABE` | 520–640 m | p 82–95    | 4          | 1.6    |
| V    | Diamante        | **brilliant**             | `#C9E6EA` | 640–700 m | p 95–100   | 5          | 1.8    |

Contrast of each fill on `--rock-0`: 10.96 / 3.94 / 5.24 / 4.32 / 14.15 — all clear 3:1 for a
graphic object. On paper they all sit between 1.01 and 4.14, so **every gem drawn on a paper surface
carries a 1.5px `--ink` keyline** and its label is `--ink`. Pale gems (I, V) additionally get the
keyline on rock, or they dissolve into the highlight.

### 6.1 The five cuts (SVG, 64×64)

```html
<!-- I · brutes: 8-vertex irregular fragment, two internal fracture lines -->
<path
  d="M14 40 L10 24 L22 11 L39 8 L52 18 L56 34 L44 52 L26 55 Z M22 11 L24 33 L44 52 M10 24 L24 33 L56 34"
  fill="#CFC6B4"
  stroke="#0E0B09"
  stroke-width="1"
/>

<!-- II · cabochon: dome on a flat base, one off-centre highlight arc -->
<path d="M6 44 H58 A26 26 0 0 0 6 44 Z" fill="#C0503A" stroke="#0E0B09" stroke-width="1.2" />
<path d="M18 32 A14 14 0 0 1 32 20" fill="none" stroke="#EADFC6" stroke-width="1.6" opacity=".55" />

<!-- III · emerald cut: chamfered rectangle + two step lines -->
<path
  d="M20 8 H44 L52 16 V48 L44 56 H20 L12 48 V16 Z"
  fill="#35996B"
  stroke="#0E0B09"
  stroke-width="1.4"
/>
<path
  d="M24 16 H40 L44 20 V44 L40 48 H24 L20 44 V20 Z M28 24 H36 L36 40 H28 Z"
  fill="none"
  stroke="#0E0B09"
  stroke-width="1"
  opacity=".7"
/>

<!-- IV · octagon: regular 8-gon + girdle cross -->
<path
  d="M22 6 H42 L58 22 V42 L42 58 H22 L6 42 V22 Z"
  fill="#8A6ABE"
  stroke="#0E0B09"
  stroke-width="1.6"
/>
<path d="M32 6 V58 M6 32 H58" fill="none" stroke="#0E0B09" stroke-width="1" opacity=".6" />

<!-- V · brilliant: girdle octagon, table octagon, 8 crown facets -->
<path
  d="M32 6 L52 14 L58 32 L52 50 L32 58 L12 50 L6 32 L12 14 Z"
  fill="#C9E6EA"
  stroke="#0E0B09"
  stroke-width="1.8"
/>
<path
  d="M24 20 H40 L44 24 V40 L40 44 H24 L20 40 V24 Z"
  fill="none"
  stroke="#0E0B09"
  stroke-width="1.2"
/>
<path
  d="M32 6 L24 20 M52 14 L40 20 M58 32 L44 24 M52 50 L40 40 M32 58 L24 44 M12 50 L20 40 M6 32 L20 24 M12 14 L24 20"
  fill="none"
  stroke="#0E0B09"
  stroke-width="1"
  opacity=".75"
/>
```

Facet lines are `--void` (`#0E0B09`) on rock and `--ink` (`#1A1108`) on paper. One highlight only,
always upper-left, always a single arc or facet — see §8, refusal 1.

### 6.2 Redundant encoding (mandatory, all four channels)

1. **Silhouette** — a chip of Tier I and a chip of Tier V must be distinguishable at 16px in
   greyscale.
2. **Tick marks** — 1 to 5 small `2×6px` bars beside every gem, in `--iron` (rock) / `--ink` at 40%
   (paper). This is the "hardness scale" cue.
3. **Stroke weight** — 1.0 → 1.8 as the tier rises; an engraver's convention, visible at a glance.
4. **Text** — the tier name, always, in `--fs-h3` on reveal and `--fs-ui` in the ledger, plus the
   percentile range in mono. A gem without its name is not rendered.

Tier chip for dense rows (ledger, log): a 16px silhouette + the name in `--fs-ui`. No coloured
pill, no badge, no glow.

---

## 7. Motion signature

One move carries the entire product: **o corte** — the channel is carved downward and the rock
above it settles.

### 7.1 The signature

The channel exists at full plate height as a solid element. It is revealed with
`transform: scaleY(var(--dug)); transform-origin: 50% 0`. Because it is a flat fill, scaling it is
invisible; the timber props are **separate elements** that fade in on a 60 ms stagger at 100 m
intervals, so nothing stretches. Dust is exactly 3 particles (`--lamp-low` at 0.5, 2×2 and 3×3px)
translating `y 0 → 18px` while fading. No canvas, no per-frame JS, no `clip-path` animation.

After the channel lands, a 1px `--lamp` hairline snaps to the new depth (opacity 0 → 1, 220 ms) and
the pin settles. That snap is the "struck the rock" beat and it is the move people will remember.

### 7.2 Reveal timing (from `submit`)

| t (ms)      | Event                                                                              | Property                   | Easing                        |
| ----------- | ---------------------------------------------------------------------------------- | -------------------------- | ----------------------------- |
| 0           | input locks; answer text stays, caret removed                                      | —                          | —                             |
| 0 → 640     | channel carves `scaleY` to new depth                                               | transform                  | `cubic-bezier(.22,.68,.12,1)` |
| 60 → 880    | 3 dust particles                                                                   | transform + opacity        | `cubic-bezier(.3,.5,.5,1)`    |
| 640 → 860   | depth hairline snaps on                                                            | opacity                    | `linear`                      |
| 680 → 800   | pin settles (lamp ellipse)                                                         | opacity, scale .92→1       | `cubic-bezier(.16,1,.3,1)`    |
| 760 → 1060  | reveal sheet rises (`translateY 100% → 0`)                                         | transform                  | `cubic-bezier(.16,1,.3,1)`    |
| 860 → 1280  | three signal bars grow (`scaleX`, origin left, 60/120/180 ms stagger, 420 ms each) | transform                  | `cubic-bezier(.22,.68,.12,1)` |
| 980 → 1360  | gem draws (`stroke-dashoffset`) then fill fades 200 ms                             | stroke-dashoffset, opacity | `linear`                      |
| 1120 → 1420 | metres count up (12 steps, tabular)                                                | text content               | —                             |
| 1240        | "próxima" enabled (not before)                                                     | —                          | —                             |

Hard cap: **1.42 s** from submit to interactive. If a tween overruns, shorten the count-up first,
never the carve.

### 7.3 Everywhere else

- Result: the plate reprises the carve — seven notches stamp in at 70 ms stagger from the top, and
  the un-dug rock fades from 100% → 45% over 400 ms _after_ the last notch. `scale` 0.6 → 1 +
  opacity, transform only.
- Screen changes: one move only — the plate wrapper's width (§5.6). Content columns move with
  `translateX` by the same delta so nothing jumps under a moving plate. 420 ms.
- Hover/press: colour only, 120 ms. No lift, no scale on buttons, no shadow growth.
- Focus: 2px `--lamp` ring, 2px offset, 0 transition (instantly visible). On paper: 2px `--ink`.

### 7.4 Reduced motion

`@media (prefers-reduced-motion: reduce)`:

- Channel: `transform: scaleY` is applied instantly; no tween, no dust, no hairline animation.
- Reveal sheet: `opacity 0 → 1` over 120 ms, no `translateY`.
- Bars, gem draw, notches, count-up: set to final state immediately; reveal sheet still appears.
- Timer bar: `steps(25, end)` so time still reads, with no continuous motion.
- The plate width transition between screens becomes an instant swap.
- Nothing in the app is load-bearing on animation: every state is correct at t = 0.

---

## 8. Three things I refuse

**1. No jewel-shop sparkle.** No animated glints, no shine sweep across a gem, no `rotate` glint, no
lens-flare, no gradient sheen on buttons, no `filter: brightness()` pulse on a find. Gems are drawn
like a mineralogy plate: flat fill, 1px facets, **one** static highlight facet. The moment a gem
twinkles, this becomes a loot game, and a game about measurement stops being about measurement.

**2. No reward chrome.** No confetti, no "NOVO RECORDE", no streak flame, no streak counter, no
badge shelf, no progress-diamond filling up, no "+250 pts" floating numbers, no sound-effect-shaped
UI. The shaft, the log and the percentile are the entire scoreboard. A dive that ends at 180 m must
feel like a bad day at the mine, not like a consolation prize.

**3. No glass over the rock.** No `backdrop-filter`, no blurred panels, no 24px-radius card stacks,
no translucent scrims, no purple/violet ambient glow, no soft drop shadows. Surfaces are rock,
paper or iron; edges are 1–2px and hard. The lamp is a value shift with a stated edge, never a halo.
Opacity is reserved for dust (≤12%) and for the un-dug rock (45%) — nowhere else.

Runner-ups I will also reject in review: pixel art, neon accents, a cartoon miner mascot, Brazilian
flag clip-art, emoji in any label, and any illustration that is not either a woodcut of mine
furniture or a measured section.

---

## 9. Implementation appendix

### 9.1 Tokens (paste into `src/index.css`)

```css
:root {
  /* palette */
  --void: #0e0b09;
  --rock-0: #171210;
  --rock-1: #221a14;
  --rock-2: #2f241b;
  --rock-3: #423325;
  --lamp: #f2b65a;
  --lamp-low: #b0752e;
  --paper: #eadfc6;
  --iron: #7b6e5e;
  --ink: #1a1108;
  --ink-2: #b7a98f; /* solid mix of paper@78% over rock-0 — never use opacity for text */

  /* type */
  --f-display: "Fraunces", "Iowan Old Style", Georgia, serif;
  --f-text: "IBM Plex Sans", system-ui, -apple-system, sans-serif;
  --f-mono: "IBM Plex Mono", ui-monospace, SFMono-Regular, monospace;

  --fs-hero: clamp(52px, 4.05vw + 36.2px, 88px);
  --fs-meter: clamp(56px, 4.49vw + 38.5px, 96px);
  --fs-h1: clamp(34px, 2.47vw + 24.4px, 56px);
  --fs-prompt: clamp(24px, 0.67vw + 21.4px, 30px);
  --fs-h3: clamp(18px, 0.45vw + 16.3px, 22px);
  --fs-body: clamp(16px, 0.11vw + 15.6px, 17px);
  --fs-ui: clamp(14px, 0.11vw + 13.6px, 15px);
  --fs-label: clamp(11px, 0.11vw + 10.6px, 12px);
  --fs-mono-s: clamp(9.5px, 0.11vw + 9.1px, 10.5px);

  /* plate */
  --plate-h: 100dvh;
  --px-per-m: calc(var(--plate-h) / 700);
  --rail-w: 44px;
  --rail-w-home: 88px;
  --gutter: 22px;
}

@media (min-width: 1024px) {
  :root {
    --rail-w: 296px;
    --rail-w-home: 296px;
    --gutter: 56px;
  }
}

.tnum {
  font-variant-numeric: tabular-nums slashed-zero;
}
.label-caps {
  font-family: var(--f-text);
  font-size: var(--fs-label);
  font-weight: 600;
  letter-spacing: 1.5px;
  text-transform: uppercase;
  line-height: 1.15;
}
```

### 9.2 Data the plate needs (`src/data/strata.json`)

```ts
type Stratum = {
  id: "solo" | "arenito" | "ardosia" | "quartzito" | "xisto" | "gnaisse" | "kimberlito";
  from: number; // metres
  to: number; // metres
  fill: string; // hex from the table in §4.2
  hatch: string; // `var(--hatch-*)` key, resolved in CSS
  label: string; // rail label, ≤3 words
  fact: number; // share of the corpus that lands in this band, 0..1 — COMPUTED, not authored
  pFrom: number; // percentile window, measured from landing depth — COMPUTED
  pTo: number;
};
```

Build step: `tools/` emits this file from the corpus; the site never authors `fact` or `pFrom/pTo`
by hand. If the file is missing, the plate still renders with the fill + hatch and omits the share
— degraded, never fabricated.

### 9.3 Accessibility contract

- The plate is `role="img"` with a live-updating `aria-label`:
  `"Seção geológica. 442 de 700 metros. Ardósia, entre 80 e 180 metros."` The 7 bands are not
  separate DOM landmarks.
- Timer: `role="timer"`, `aria-live="off"`. Announce twice, once at 7 s and once at 3 s, via a
  polite live region (`"7 segundos"`, `"3 segundos"`). No per-second announcements.
- Reveal verdict: `aria-live="polite"` on one node: `"Esmeralda. Percentil 71. 148 metros."`
- Focus order: prompt → input → submit. The plate is never focusable.
- All touch targets ≥44px. The input's tap area includes the 12px line below it.
- `prefers-reduced-motion`, `prefers-contrast: more` (bump `--iron` → `#8E8170`, `--rock-3` →
  `#4E3D2C`), and 200% zoom at 390 width must not produce horizontal scroll. The plate is the only
  element allowed to be cropped under 320px, and only its label column (never the channel).

### 9.4 Acceptance checklist

- [ ] At 390×844, the full 700 m plate is visible with zero scrolling, and the pin is at the correct
      metre on all five screens.
- [ ] At 1280×800, the plate never exceeds 296px except on result/log-detail (560px).
- [ ] Remove all colour from the plate (greyscale): the seven bands remain distinguishable.
- [ ] Remove the labels from all five gems at 16px: each is still identifiable by silhouette.
- [ ] `#EADFC6` on `#171210` measures 14.04:1; verifies in DevTools on the shipped build.
- [ ] No `backdrop-filter`, no `box-shadow` blur above 8px, no `border-radius` above 2px anywhere
      except the reveal sheet's 2px top-left corner.
- [ ] Reveal is interactive at ≤1420 ms and fully correct at t = 0 with reduced motion on.
- [ ] `SÃO PAULO · ARDÓSIA · CLIVAGEM · 700 m` renders without fallback glyphs in all three faces.
- [ ] Input font-size ≥16px at 390 (no iOS zoom).
- [ ] Method page states the scale bar (`dig`), the percentile windows, and the recalculation date
      of the dataset.
