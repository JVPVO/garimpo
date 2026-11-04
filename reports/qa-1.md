# Garimpo — QA 1

**Date:** 2026-11-04  
**Build:** Vite dev server on `http://localhost:5173`, dataset at that moment: `116 perguntas · 2.336 respostas`  
**Played in:** a real Chrome session via `agent-browser`; screenshots at 1280×800 and 390×844 in `reports/shots/`.

## What was played

- **Full dive A, obvious answers (daily 04 nov):** Páginas da Vida, Tijuca, Londrina, Roberto Carlos, As Tartarugas Ninja, Morumbi, Curupira → **325 metros.** / “Granada · xisto”.
- **Full dive B, deliberately rare (seed 283):** Vespasiano, Gilka Machado, Efó, Roraima, Bananada, Corinthians Alagoano, Cainamé → **691 metros.** / “Diamante · kimberlito” / “7 gemas no caminho.”
- Edge cases: unknown (“Atlântida”), structural junk (“clube”, “sport”), empty submit, timer timeout, reload mid-dive, archive after finishing, archived-dive replay, “Como medimos”, seed `#s=8842`, seed 101, seed 3, and a full seven-answer keyboard dive.

## Scores (final, after the two hillclimb fixes)

| category | score | evidence |
| --- | ---: | --- |
| first_impression | 9 | The home screen lands: “Sete respostas. Uma mina.” over the hatched shaft, with “116 perguntas · 700 m” and the 691 m record; it never looks like a template. |
| clarity | 6 | The prompt and “enter para cravar” are clear, but the answer placeholder is nearly invisible and “p 19” sitting above “1 em 16” is never defined. |
| visual | 7 | Desktop home/round are composed and legible, but the result headline starts at y=738 on an 800 px viewport, so “691 metros.” is cut off; mobile “Como medimos” scrolls sideways. |
| typography | 8 | The Fraunces/Plex pairing carries the mine motif well; the mono metadata drops to 9.5 px and the reveal prints “1 wikis” for a single sitelink. |
| answer_feedback | 9 | After the fix, Enter shows the full paper reveal (“p 19 / 1 em 16 / 0→63 m”) and a timeout reads “sem resposta”; before, Enter submitted and skipped the sheet entirely. |
| rarity_fairness | 8 | Monotonic and verified: São Paulo (UF) p 0 → 10 m vs Roraima p 96 → 99 m; Flamengo p 19 → 63 m, Juventude p 34 → 74 m, obvious São Paulo FC p 5 → 45 m. |
| speed | 7 | 25 s per prompt, immediate submit/next, no spinner; the timer hits 0 and reveals, though the opening second is busy with the reveal animation. |
| mobile | 5 | Playable at 390×844, but the method page scrolls sideways (443 vs 375 px), the result score begins below the 844 px fold, and the reveal wraps “0 → 47” with the “m” alone. |
| audio | 6 | The mute control swaps ◉/◌ and persists in localStorage; the engine is fully synthesized (no files) with strike/tick/gem voices, but headless playback cannot be judged by ear. |
| replay | 5 | The archive opens past dives, but “Descer de novo” on the archived 691 m unlimited dive starts the daily instead, and reloading after starting seed 8842 lands on Home. |
| trust | 6 | Invalid structural answers (“clube”, “sport”) used to pay 45/54 m; they are now refused. The seed URL, daily memory and streak still misreport. |

### Total: 76 / 110 (69.1%)

**Single weakest category before fixes:** **trust, 4** — tied numerically with `answer_feedback` (4), but chosen first because it corrupts the score itself. After iteration 1 the sole remaining 4 was `answer_feedback`; after iteration 2 the single weakest is **mobile, 5** (replay is also 5).

## Hillclimb

| iter | weakest | change | score before | score after |
| ---: | --- | --- | ---: | ---: |
| 1 | trust (4) | `src/game/match.ts`: reject a single structural token (`clube`, `futebol`, `esporte`, `sport`, `associacao`, `municipal`, `estadio`, `parque`, `cidade`, `estado`, `time`) before any fuzzy match. “clube” and “sport” now return “não está no acervo desta pergunta”; Flamengo, Juventude, São Paulo, Corinthians Alagoano, Londrina, Lagarto, Tijuca and Morumbi still match. Trust 4 → 6. | 69 | 71 |
| 2 | answer_feedback (4) | `src/screens/Round.tsx`: `event.stopPropagation()` on the submit Enter so the reveal’s global Enter handler does not consume the same keypress. `src/screens/Reveal.tsx`: a timeout now says “sem resposta” and “O tempo acabou antes da sua resposta…”, not “A sua ficou fora dele”. Verified Enter → reveal (`p 19`, `0→63 m`), second Enter → pergunta 2, and a full seven-answer keyboard dive ending at “318 metros.” Answer feedback 4 → 9. | 71 | 76 |

`pnpm exec tsc --noEmit && pnpm build` passed after both iterations (35 modules, build 212 ms).

## Concrete defects

| id | severity | status | defect and evidence | file:line |
| --- | --- | --- | --- | --- |
| D1 | P0 | fixed | **Enter submitted and skipped the reveal.** Typing “Flamengo” and pressing Enter once left the screen on “Cite um cantor brasileiro que começa com M” with the ledger showing “Clube de Regatas do Flamengo 63 m” and no sheet. The input handler and the reveal’s global listener both saw the same Enter. | `src/screens/Round.tsx:115-121`, `src/App.tsx:183-195` |
| D2 | P0 | fixed | **A structural word bought a real answer.** On “Cite um time que já foi campeão brasileiro”, “clube” matched “São Paulo Futebol Clube” (p 5, 0→45 m) and “sport” matched “Sport Club Corinthians Paulista” (p 11, 0→54 m). The token-subset rule accepted one generic token. | `src/game/match.ts:44-80` |
| D3 | P1 | fixed | **A timeout claimed the answer was out of catalog.** With no answer, the sheet read “o tempo acabou / — / não está no acervo desta pergunta / A sua ficou fora dele…”, which is false; it now reads “sem resposta / O tempo acabou antes da sua resposta…”. | `src/screens/Reveal.tsx:110-121` |
| D4 | P1 | open | **Seed links break immediately.** The seed screen starts “semente 8842”, but the address bar is rewritten to `#s=4020521479` (the derived 32-bit seed). `HASH_SEED` only accepts 1–4 digits, so reloading that URL lands on Home. Opening `#s=8842` while the app is already open does nothing because the hash is only read when the dataset loads. | `src/App.tsx:26`, `src/App.tsx:85`, `src/App.tsx:104-107` |
| D5 | P1 | open | **An archived dive replays the wrong thing.** Opening the 691 m archived dive (“ILIMITADO · SEMENTE 283”) and pressing “Descer de novo” started the daily (“04 nov · pergunta 1/7”, “Cite uma novela dos anos 2000”), not seed 283. | `src/App.tsx:364` |
| D6 | P1 | open | **The daily is stored, never remembered.** After a 325 m daily, localStorage has `dailyDone: {"04 nov": {...}}`, but Home reads `dailyDone["2026-11-04"]`; the button still says “Descer” and never “Descer de novo / hoje: 325 m”. | `src/screens/Home.tsx:24`, `src/game/storage.ts:42` |
| D7 | P1 | open | **Unlimited dives reset the daily streak.** After a daily then seed 283, the store was `streak: {last: "semente 283", count: 1}`; the archive showed “1 em sequência”. Unlimited labels enter the same streak path as daily labels. | `src/game/storage.ts:44-60` |
| D8 | P1 | open | **Mobile “Como medimos” overflows horizontally.** `document.documentElement.scrollWidth` was 443 against a 375 px client width; the 405 px table is clipped (“sobre aqu”, “sobre um l”, “postos pe”) and a horizontal scrollbar appears. | `src/index.css:1517`, `src/index.css:1456` |
| D9 | P1 | open | **The result hides its own score.** `.stage` already pads 70 px for the topbar; `.result` adds another 64 px. The plate starts at y=134, the headline at y=738 and ends at y=833, so on 1280×800 “691 metros.” is below the fold. On 390×844 the headline starts at y≈750. | `src/index.css:1034-1045`, `src/index.css:241` |
| D10 | P2 | open | **The mobile reveal wraps the unit and the p-value.** The depth row is a non-wrapping inline flex; “0 → 47” renders with “m” alone on the next line, and “p 6 / 1 em 6” breaks into four lines. | `src/screens/Reveal.tsx:132-153` |
| D11 | P2 | open | **The answer placeholder is effectively invisible.** `.field::placeholder` uses `#423325` on `#171210`; “sua resposta” is almost unreadable in the 1280 and 390 screenshots, even though it is the only cue in an empty field. | `src/index.css:525` |
| D12 | P2 | open | **“1 wikis”.** Efó and Cainamé both render “SITELINKS 1 wikis”; the singular is never handled. | `src/screens/Reveal.tsx:52` |
| D13 | P2 | open | **Two rarity scales sit side by side without labels.** The reveal prints “p 19” above “1 em 16”; `p` is the percentile, while `1 em N` is the crowd share (`oneIn`). Rio de Janeiro prints “p 2 / 1 em 2” because 41.8% of the crowd says it, which reads like a contradiction. The method page never defines `oneIn`. | `src/screens/Reveal.tsx:76-80`, `src/game/score.ts:63-67` |
| D14 | P2 | open | **Gem tiers contradict the method table.** The method maps gems to depth (“Quartzo leitoso … 0–180 m”), but the result counts gems with `tierForRarity(round.p)`. The 691 m dive shows “7 gemas” even though every answer is 97–99 m, i.e. Quartzo on the printed table. | `src/screens/Method.tsx:127-150`, `src/screens/Result.tsx:81`, `src/game/score.ts:54-60` |

## Confirmed working

- Rarity ordering is correct in both directions: Roraima 99 m vs São Paulo 10 m; Juventude 74 m vs Flamengo 63 m vs obvious São Paulo FC 45 m. The reveal also prints the explicit comparison (“O mais óbvio era São Paulo Futebol Clube (p 5), que desce só 45 m.”).
- Empty submit does nothing: the button stays disabled, Enter does not advance, the timer keeps running.
- The 25 s timer runs out, reveals, and keeps the round at 0 m; zero is never invented for an unknown answer.
- Archive after finishing lists the dive and reopens its result; the 691 m dive is intact.
- “Como medimos” is on the result, home and archive paths and the source/data claims are legible on desktop.
- Sound toggle is real state: ◉ → ◌, `aria-label` “ligar som”, persisted in `garimpo:v1`; the engine is procedural, no asset dependency.
- Two full dives completed: 325 m (obvious) and 691 m (rare); no crash, no stuck state.

## Files changed by this playtest

- `src/game/match.ts` — single-token structural-word guard.
- `src/screens/Round.tsx` — stop Enter propagation on submit.
- `src/screens/Reveal.tsx` — honest timeout copy.
- `reports/qa-1.md`, `reports/qa-1.json`, `reports/shots/*.png` — evidence.

(Concurrent edits to `src/game/score.ts`, `src/screens/Result.tsx` and `src/index.css` were already in the working tree during this session; the scores above judge the build as played, including those changes.)

## Correções depois do playtest (mesma sessão)

| defeito | correção |
|---|---|
| D9 resultado escondia o próprio score | `.result` perdeu o padding duplicado; placa em `60dvh` (44 no celular). A manchete aparece sem rolar. |
| D10 unidade e p quebravam no celular | `.reveal-foot` empilha no celular, `.reveal-depth` e `.pval` com `nowrap`. |
| D11 placeholder invisível | `--iron` no lugar de `--rock-3`. |
| D12 “1 wikis” | singular/plural resolvido. |
| D13 duas escalas sem rótulo | `p` virou “posto no acervo” e “≈ 1 em N” ganhou a explicação no método. |
| D14 gema contradizia a tabela | gema agora sai da profundidade acumulada do poço, que é a tabela impressa. |
| seed na URL virava hash interno | `#s=8842` preservado; recarregar restaura a mesma mina. |
| “Descer de novo” do arquivo caía no diário | usa modo/semente do mergulho aberto. |
| diário gravado como “04 nov” e lido como data ISO | chave agora é `dive.date`. |
| ilimitado mexia na sequência diária | só o diário conta para o streak. |

Também entrou o acervo internacional (países, capitais do mundo, elementos, cidades,
Pokémon, heróis, videogames, animes, bandas, comida e marcas): 157 perguntas e
6.223 respostas no total, com alias para o que brasileiro fala e a Wikipédia não
("EUA", "Tóquio/Tokyo", "GTA 5", "Spiderman").
