#!/usr/bin/env python3
"""Garimpo scoring-curve simulator (stdlib only).

The only question this tool answers: given a player skill mixture and a
candidate rarity->points curve, what total depth do people actually finish a
7-prompt dive with -- and does the curve leave dead zones where a clearly
rarer answer pays the same as a common one?

Model (fixed by the design brief):
  * one dive = 7 prompts, 25 s each, one typed answer per prompt
  * every catalogue answer carries an empirical rarity percentile p in [0,1]
    (p = 1 is the rarest answer in the pool, p = 0 the most common)
  * points for prompt i:  k_i = quantise(f(p_i)),  k in [1, 10]
  * depth for prompt i:   d_i = 10 * k_i  metres
  * a wrong/blank answer scores 0 points and 0 metres (12% chance per prompt)
  * player skill is sampled once per player, then p is drawn per prompt:
        55% casual  Beta(2,5)   mean p 0.286
        30% solid   Beta(4,3)   mean p 0.571
        15% expert  Beta(6,2)   mean p 0.750

Because p is a percentile inside the pool, a player who answers uniformly at
random from the pool draws p ~ U(0,1). That calibration is what makes p
comparable across prompts with pools of different sizes, and it is why an
equal-width ladder in p is an equal-probability ladder -- and also why its
bands are huge dead zones.

Modes:
    python tools/sim/curve.py                  # comparison table of candidates
    python tools/sim/curve.py --frontier       # (median, p90) frontier evidence
    python tools/sim/curve.py --chosen         # full spec of the shipped curve
    python tools/sim/curve.py --search         # grid-search shape parameters
    python tools/sim/curve.py --corr 0.5       # within-dive correlation (rho)
    python tools/sim/curve.py --json           # machine-readable numbers
"""
from __future__ import annotations

import argparse
import bisect
import json
import math
import random
from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass

# ---------------------------------------------------------------- constants --

DIVE_PROMPTS = 7
PLAYERS = 20_000
MISS_RATE = 0.12              # wrong / blank / timeout, per prompt
K_MIN, K_MAX = 1.0, 10.0      # points per prompt
METRES_PER_POINT = 10.0       # depth = k * 10 m
MAX_DEPTH = DIVE_PROMPTS * METRES_PER_POINT * K_MAX      # 700 m
SEED = 20260211               # fixed: the table in reports/game-loop.md must reproduce

# (share, label, beta_a, beta_b)
SKILL_MIX: tuple[tuple[float, str, float, float], ...] = (
    (0.55, "casual", 2.0, 5.0),
    (0.30, "solid", 4.0, 3.0),
    (0.15, "expert", 6.0, 2.0),
)

# Design targets, from the brief.
TARGET_MEDIAN = (380.0, 450.0)
TARGET_P90_MIN = 600.0
TARGET_LOW_SHARE_MAX = 0.08     # share of dives under 200 m
TARGET_DEAD_ZONE_MAX = 6.0      # percentage points of p that may share one k

DEAD_ZONE_GRID = 20_000         # dead-zone scan resolution: p steps of 0.005 pp

# The shipped curve ("the vein"): a cliff in p blended with a linear ladder.
# Everything downstream (report, TypeScript) quotes these numbers.
VEIN_W = 0.35                   # share of the scale that is linear in p
VEIN_A = 16.0                   # cliff steepness
VEIN_B = 0.20                   # cliff position in p
CHOSEN_STEP = 0.1               # k to one decimal -> 1 m of depth per step
CHOSEN_NAME = "vein w=.35 a=16 b=.20"
CHOSEN_NOTE = "k = 1 + 9*(g(p)-g(0))/(g(1)-g(0)), g = .35p + .65*sigmoid(16(p-.2))"
MIN_POOL = 40                   # scored prompts need N >= 40 (see --chosen)


# --------------------------------------------------------------- quantising --

def quantise(k: float, step: float) -> float:
    """Snap k to a step (0.5 = half points, 0.1 = 1 m of depth) inside [1,10]."""
    k = min(K_MAX, max(K_MIN, k))
    snapped = round(k / step) * step
    return min(K_MAX, max(K_MIN, round(snapped, 6)))


def dead_zones(f: Callable[[float], float], step: float) -> dict:
    """Scan p in [0,1] and measure how wide the widest same-point band is.

    A dead zone is an interval of p over which a strictly rarer answer earns
    exactly the same points. Wide bands at the top are the real failure mode:
    they make "rare" and "very rare" indistinguishable, which is the thing the
    whole game is about.
    """
    n = DEAD_ZONE_GRID
    bands: list[tuple[float, float, float]] = []   # (lo_p, hi_p, k)
    start = 0.0
    prev = quantise(f(0.0), step)
    for i in range(1, n + 1):
        p = i / n
        k = quantise(f(p), step)
        if k != prev:
            bands.append((start, p, prev))
            prev, start = k, p
    bands.append((start, 1.0, prev))

    widest = max(bands, key=lambda b: b[1] - b[0])
    supports = sorted({round(k, 4) for _, _, k in bands})
    wide = [b for b in bands if (b[1] - b[0]) * 100.0 > TARGET_DEAD_ZONE_MAX]
    return {
        "distinct_k": len(supports),
        "k_values": supports,
        "max_band_pp": round((widest[1] - widest[0]) * 100.0, 2),
        "max_band_k": round(widest[2], 3),
        "max_band_at_p": round(widest[1], 4),
        "bands_over_target": [
            {"k": round(b[2], 3), "lo": round(b[0], 4), "hi": round(b[1], 4),
             "pp": round((b[1] - b[0]) * 100.0, 2)}
            for b in sorted(wide, key=lambda b: b[1] - b[0], reverse=True)
        ][:6],
        "unreachable_k": [
            round(K_MIN + i * step, 4)
            for i in range(int(round((K_MAX - K_MIN) / step)) + 1)
            if round(K_MIN + i * step, 4) not in supports
        ],
    }


# ------------------------------------------------------------------- curves --

def c_linear(p: float, **_: float) -> float:
    """k = 1 + 9p. The naive baseline: rank and reward move together."""
    return 1.0 + 9.0 * p


def c_power(p: float, exp: float = 1.4, **_: float) -> float:
    """k = 1 + 9 * p^exp. exp > 1 punishes common answers superlinearly."""
    return 1.0 + 9.0 * (p ** exp)


def c_logistic(p: float, gain: float = 7.0, mid: float = 0.5, **_: float) -> float:
    """k = 1 + 9 / (1 + e^(-gain*(p-mid))). S-curve: flat at both ends."""
    return 1.0 + 9.0 / (1.0 + math.exp(-gain * (p - mid)))


def vein_raw(p: float, w: float, a: float, b: float) -> float:
    """Unnormalised vein curve: a linear rarity ladder blended with a cliff."""
    sig = 1.0 / (1.0 + math.exp(-a * (p - b)))
    return w * p + (1.0 - w) * sig


def c_vein(p: float, w: float = 0.35, a: float = 16.0, b: float = 0.20,
           **_: float) -> float:
    """k = 1 + 9 * (g(p) - g(0)) / (g(1) - g(0)),  g = w*p + (1-w)*sigmoid(a(p-b)).

    Two recognisable halves:
      * sigmoid(a(p-b)) is the cliff -- the point p=b where depth takes off;
      * w*p is the ladder -- a fixed number of points that every extra
        percentile still buys, so the top end never goes dead.
    Endpoints are normalised so p=0 is exactly 1 point and p=1 exactly 10."""
    g0 = w * 0.0 + (1.0 - w) * (1.0 / (1.0 + math.exp(a * b)))
    g1 = w * 1.0 + (1.0 - w) * (1.0 / (1.0 + math.exp(-a * (1.0 - b))))
    return 1.0 + 9.0 * (vein_raw(p, w, a, b) - g0) / (g1 - g0)


def c_softfloor(p: float, floor: float = 2.0, exp: float = 0.85, **_: float) -> float:
    """k = floor + (10-floor) * p^exp. Nobody scores 1 point, ever."""
    return floor + (K_MAX - floor) * (p ** exp)


LADDER_10 = (0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9)


def make_ladder(edges: Sequence[float]):
    """Equal-width tier ladder: the k jumps at each edge, flat in between."""
    tiers = len(edges)

    def f(p: float) -> float:
        rank = 0
        for i, edge in enumerate(edges):
            if p >= edge:
                rank = i
        return K_MIN + (K_MAX - K_MIN) * (rank / (tiers - 1))

    return f


def make_buckets(edges: Sequence[float], offsets: Sequence[float]):
    """Explicit ladder: edges in p, offsets are the k values per band."""

    def f(p: float) -> float:
        rank = 0
        for i, edge in enumerate(edges):
            if p >= edge:
                rank = i
        return offsets[min(rank, len(offsets) - 1)]

    return f


# ----------------------------------------------------- correlated p sampling --

_NORM_C = (
    -7.784894002430293e-03, -3.223964580411365e-01, -2.400758277161838e+00,
    -2.549732539343734e+00, 4.374664141464968e+00, 2.938163982698783e+00,
)
_NORM_D = (7.784695709041462e-03, 3.224671290700398e-01, 2.445134137142996e+00,
           3.754408661907416e+00)
_NORM_A = (-3.969683028665376e+01, 2.209460984245205e+02, -2.759285104469687e+02,
           1.383577518672690e+02, -3.066479806614716e+01, 2.506628277459239e+00)
_NORM_B = (-5.447609879822406e+01, 1.615858368580409e+02, -1.556989798598866e+02,
           6.680131188771972e+01, -1.328068155288572e+01)
_P_LOW = 0.02425


def norm_cdf(x: float) -> float:
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def norm_ppf(u: float) -> float:
    """Inverse standard normal CDF (Acklam 2003), |relative error| < 1.2e-9."""
    if u <= 0.0:
        return -8.0
    if u >= 1.0:
        return 8.0
    if u < _P_LOW:
        q = math.sqrt(-2.0 * math.log(u))
        c, d = _NORM_C, _NORM_D
        return (((((c[0] * q + c[1]) * q + c[2]) * q + c[3]) * q + c[4]) * q + c[5]) / \
               ((((d[0] * q + d[1]) * q + d[2]) * q + d[3]) * q + 1.0)
    if u <= 1.0 - _P_LOW:
        q = u - 0.5
        r = q * q
        a, b = _NORM_A, _NORM_B
        return (((((a[0] * r + a[1]) * r + a[2]) * r + a[3]) * r + a[4]) * r + a[5]) * q / \
               (((((b[0] * r + b[1]) * r + b[2]) * r + b[3]) * r + b[4]) * r + 1.0)
    q = math.sqrt(-2.0 * math.log(1.0 - u))
    c, d = _NORM_C, _NORM_D
    return -(((((c[0] * q + c[1]) * q + c[2]) * q + c[3]) * q + c[4]) * q + c[5]) / \
        ((((d[0] * q + d[1]) * q + d[2]) * q + d[3]) * q + 1.0)


class Quantiles:
    """Empirical CDF/PPF per skill class, used by the correlated-p model.

    The brief specifies p as an independent Beta draw per prompt. Real players
    are not independent: a player who knows the corner of the catalogue they
    were asked about is likely to know several prompts. `rho` models that as a
    Gaussian copula over the class marginal, which keeps each class's p
    distribution exactly Beta and changes only the within-dive correlation.
    """

    def __init__(self, size: int = 100_001, seed: int = SEED + 1):
        rng = random.Random(seed)
        self._tables: dict[str, list[float]] = {}
        self._n = size
        for _, label, a, b in SKILL_MIX:
            draw = sorted(rng.betavariate(a, b) for _ in range(size))
            self._tables[label] = draw

    def cdf(self, label: str, p: float) -> float:
        return bisect.bisect_left(self._tables[label], p) / self._n

    def ppf(self, label: str, u: float) -> float:
        i = int(u * (self._n - 1))
        return self._tables[label][min(self._n - 1, max(0, i))]


# ----------------------------------------------------------------- simulate --

@dataclass(frozen=True)
class Curve:
    name: str
    f: Callable[[float], float]
    step: float = CHOSEN_STEP      # quantisation of k (0.1 -> 1 m of depth)
    note: str = ""


def simulate(curve: Curve, players: int = PLAYERS, seed: int = SEED,
             prompts: int = DIVE_PROMPTS, miss: float = MISS_RATE,
             corr: float = 0.0) -> dict:
    """Play `players` dives and return the depth distribution plus diagnostics."""
    rng = random.Random(seed)
    f, step = curve.f, curve.step
    shares = [s for s, _, _, _ in SKILL_MIX]
    params = [(a, b, label) for _, label, a, b in SKILL_MIX]
    q = Quantiles() if corr > 0.0 else None
    rho, scale = corr, math.sqrt(max(0.0, 1.0 - corr * corr))

    totals: list[float] = []
    per_class: dict[str, list[float]] = {label: [] for _, label, _, _ in SKILL_MIX}
    z_hits = 0.0
    answers = 0

    for _ in range(players):
        r = rng.random()
        acc, idx = 0.0, 0
        for i, share in enumerate(shares):
            acc += share
            idx = i
            if r < acc:
                break
        a, b, label = params[idx]
        z_common = rng.gauss(0.0, 1.0) if q else 0.0
        total = 0.0
        for _ in range(prompts):
            if rng.random() < miss:
                continue                      # wrong / blank: 0 points, 0 m
            p = rng.betavariate(a, b)
            if q:
                z = scale * norm_ppf(q.cdf(label, p)) + rho * z_common
                p = q.ppf(label, norm_cdf(z))
            k = quantise(f(p), step)
            total += METRES_PER_POINT * k
            z_hits += k
            answers += 1
        totals.append(total)
        per_class[label].append(total)

    totals.sort()
    return {
        "curve": curve.name,
        "step": step,
        "players": players,
        "corr": corr,
        "mean": round(sum(totals) / len(totals), 1),
        "mean_k": round(z_hits / answers, 3) if answers else 0.0,
        "p10": _pct(totals, 0.10),
        "p50": _pct(totals, 0.50),
        "p90": _pct(totals, 0.90),
        "share_600": round(sum(1 for t in totals if t >= 600) / len(totals), 4),
        "share_200": round(sum(1 for t in totals if t < 200) / len(totals), 4),
        "share_max": round(sum(1 for t in totals if t >= MAX_DEPTH - 10) / len(totals), 4),
        "by_class": {
            label: {
                "p50": _pct(sorted(v), 0.50),
                "p90": _pct(sorted(v), 0.90),
                "mean": round(sum(v) / len(v), 1),
            }
            for label, v in per_class.items()
        },
        **dead_zones(f, step),
        "note": curve.note,
    }


def _pct(sorted_values: Sequence[float], q: float) -> float:
    """Linear-interpolated percentile of an already sorted sequence."""
    if not sorted_values:
        return 0.0
    if len(sorted_values) == 1:
        return round(sorted_values[0], 1)
    pos = q * (len(sorted_values) - 1)
    lo = int(math.floor(pos))
    hi = min(lo + 1, len(sorted_values) - 1)
    frac = pos - lo
    return round(sorted_values[lo] + (sorted_values[hi] - sorted_values[lo]) * frac, 1)


def verdict(r: dict) -> tuple[bool, list[str]]:
    """Check a result against the brief's targets."""
    fails: list[str] = []
    if not (TARGET_MEDIAN[0] <= r["p50"] <= TARGET_MEDIAN[1]):
        fails.append(f"median {r['p50']:.0f} outside {TARGET_MEDIAN[0]:.0f}-{TARGET_MEDIAN[1]:.0f}")
    if r["p90"] < TARGET_P90_MIN:
        fails.append(f"p90 {r['p90']:.0f} < {TARGET_P90_MIN:.0f}")
    if r["share_200"] > TARGET_LOW_SHARE_MAX:
        fails.append(f"under-200m {r['share_200'] * 100:.1f}% > {TARGET_LOW_SHARE_MAX * 100:.0f}%")
    if r["max_band_pp"] > TARGET_DEAD_ZONE_MAX:
        fails.append(f"dead zone {r['max_band_pp']:.1f}pp > {TARGET_DEAD_ZONE_MAX:.0f}pp")
    return (not fails), fails


def candidates() -> list[Curve]:
    """The four families in the brief, plus the quantisation question."""
    buckets6 = make_buckets(
        (0.0, 0.30, 0.55, 0.75, 0.90, 0.97),
        (1.0, 2.5, 4.0, 6.0, 8.0, 10.0),
    )
    return [
        Curve("linear", c_linear, 0.1, "k = 1 + 9p"),
        Curve("power p^1.4", c_power, 0.1, "k = 1 + 9p^1.4"),
        Curve("ladder (10 tiers)", make_ladder(LADDER_10), 0.1,
              "equal 10pp bands, k = 1..10"),
        Curve("buckets (6 tiers)", buckets6, 0.1,
              "k = 1/2.5/4/6/8/10 at p = 0/.30/.55/.75/.90/.97"),
        Curve("logistic a=7 mid=.5", c_logistic, 0.1, "k = 1 + 9/(1+e^(-7(p-.5)))"),
        Curve("softfloor 2+8p^.85", c_softfloor, 0.1, "k = 2 + 8p^.85"),
        Curve("power p^0.45", lambda p: c_power(p, exp=0.45), 0.1,
              "best smooth single-power curve"),
        Curve(f"chosen: {CHOSEN_NAME}", chosen_curve().f, CHOSEN_STEP, CHOSEN_NOTE),
        Curve("chosen @ 0.5 step", chosen_curve().f, 0.5,
              "same curve, half-point steps"),
    ]


def chosen_curve() -> Curve:
    return Curve(CHOSEN_NAME, lambda p: c_vein(p, w=VEIN_W, a=VEIN_A, b=VEIN_B),
                 CHOSEN_STEP, CHOSEN_NOTE)


# -------------------------------------------------------------------- spec --

def k_of_p(p: float) -> float:
    """The shipped map, unquantised (float in [1,10])."""
    return c_vein(p, w=VEIN_W, a=VEIN_A, b=VEIN_B)


def depth_of(p: float) -> float:
    """Shipped depth in metres for a rarity percentile."""
    return quantise(k_of_p(p), CHOSEN_STEP) * METRES_PER_POINT


def p_of_k(k: float) -> float:
    """Inverse of k_of_p by bisection (the vein curve has no closed inverse)."""
    lo, hi = 0.0, 1.0
    for _ in range(60):
        mid = (lo + hi) / 2.0
        if k_of_p(mid) < k:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2.0


def max_slope(samples: int = 20_000) -> tuple[float, float]:
    """Steepest dk/dp of the shipped curve, and where it happens.

    This is the pool-size guard rail: one rank of a pool with N answers moves p by
    1/N, so the worst swing per rank is max_slope/N points (10x that in metres).
    """
    best, at, prev = 0.0, 0.0, k_of_p(0.0)
    for i in range(1, samples + 1):
        p = i / samples
        cur = k_of_p(p)
        slope = (cur - prev) * samples
        if slope > best:
            best, at = slope, p
        prev = cur
    return best, at


STRATA = (
    # name, k at which the band starts (0.1 point = 1 m of depth)
    ("Barranco", 1.0),
    ("Cascalho", 4.0),
    ("Aluvião", 7.0),
    ("Veio", 9.0),
    ("Pepita", 9.6),
)


def spec() -> dict:
    """Everything the TypeScript implementation and the report need."""
    grid = [0.0, 0.01, 0.05, 0.10, 0.20, 0.30, 0.40, 0.50, 0.60, 0.70, 0.80, 0.90,
            0.95, 0.99, 1.0]
    return {
        "formula": "k(p) = 1 + 9*(g(p)-g(0))/(g(1)-g(0)),  g(p) = .35p + .65*sigmoid(16(p-.20))",
        "step": CHOSEN_STEP,
        "depth_per_point": METRES_PER_POINT,
        "k_at_p": [{"p": p, "k": round(quantise(k_of_p(p), CHOSEN_STEP), 2),
                    "depth_m": round(quantise(k_of_p(p), CHOSEN_STEP) * METRES_PER_POINT, 1)}
                   for p in grid],
        "p_at_k": [{"k": k, "p": round(p_of_k(k), 4),
                    "p_pct": round(100 * p_of_k(k), 2)} for k in
                   (1.5, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 9.5, 10.0)],
        "strata": strata_rows(),
        "dead_zones": dead_zones(k_of_p, CHOSEN_STEP),
    }


def strata_rows() -> list[dict]:
    """Named bands of the score axis, with the exact rarity each band requires."""
    rows = []
    for i, (name, k_lo) in enumerate(STRATA):
        first, last = i == 0, i == len(STRATA) - 1
        k_hi = K_MAX if last else round(STRATA[i + 1][1] - CHOSEN_STEP, 1)
        p_lo = 0.0 if first else p_of_k(k_lo)
        p_hi = 1.0 if last else p_of_k(STRATA[i + 1][1])
        rows.append({
            "name": name,
            "p_lo": round(p_lo, 4), "p_hi": round(p_hi, 4),
            "p_pct": f"{100 * p_lo:.1f}-{100 * p_hi:.1f}%",
            "pool_share": round(100 * (p_hi - p_lo), 1),
            "k_lo": round(k_lo, 1), "k_hi": round(k_hi, 1),
            "prompt_depth": f"{k_lo * METRES_PER_POINT:.0f}-{k_hi * METRES_PER_POINT:.0f} m",
        })
    return rows


# ------------------------------------------------------------------ reports --

def table(rows: Iterable[dict]) -> str:
    lines = [
        f"{'curve':<28}{'k step':>7}{'p10':>7}{'p50':>7}{'p90':>7}"
        f"{'>=600':>7}{'<200':>7}{'k':>4}{'dz pp':>7}  verdict"
    ]
    lines.append("-" * 97)
    for r in rows:
        ok, fails = verdict(r)
        mark = "OK" if ok else "no: " + "; ".join(fails)
        lines.append(
            f"{r['curve']:<28}{r['step']:>7}{r['p10']:>7.0f}{r['p50']:>7.0f}"
            f"{r['p90']:>7.0f}{r['share_600'] * 100:>6.1f}%{r['share_200'] * 100:>6.1f}%"
            f"{r['distinct_k']:>4}{r['max_band_pp']:>7.1f}  {mark}"
        )
    return "\n".join(lines)


def class_table(rows: Iterable[dict]) -> str:
    lines = [f"{'curve':<28}{'casual p50':>12}{'solid p50':>11}{'expert p50':>12}"
             f"{'expert p90':>12}"]
    lines.append("-" * 75)
    for r in rows:
        c = r["by_class"]
        lines.append(f"{r['curve']:<28}{c['casual']['p50']:>12.0f}"
                     f"{c['solid']['p50']:>11.0f}{c['expert']['p50']:>12.0f}"
                     f"{c['expert']['p90']:>12.0f}")
    return "\n".join(lines)


def frontier(players: int = 10_000) -> list[dict]:
    """Sweep the two live families to expose the median/p90/dead-zone frontier."""
    out = []
    for exp in (0.20, 0.25, 0.30, 0.35, 0.40, 0.45, 0.50, 0.60, 0.75, 1.00, 1.40):
        f = lambda p, e=exp: c_power(p, exp=e)   # noqa: E731
        r = simulate(Curve(f"power p^{exp}", f), players=players)
        r["family"] = "power"
        r["param"] = f"exp={exp}"
        out.append(r)
    for w, a, b in ((0.25, 16, 0.20), (0.30, 16, 0.20), (0.35, 16, 0.20),
                    (0.35, 12, 0.20), (0.40, 16, 0.20), (0.35, 16, 0.26),
                    (0.35, 20, 0.16)):
        f = lambda p, ww=w, aa=a, bb=b: c_vein(p, w=ww, a=aa, b=bb)   # noqa: E731
        r = simulate(Curve(f"vein w={w} a={a} b={b}", f), players=players)
        r["family"] = "vein"
        r["param"] = f"w={w} a={a} b={b}"
        out.append(r)
    for r in out:
        r["in_band"] = TARGET_MEDIAN[0] <= r["p50"] <= TARGET_MEDIAN[1]
        r["p90_ok"] = r["p90"] >= TARGET_P90_MIN
    return out


def search(players: int = 6_000) -> list[dict]:
    """Grid-search vein parameters that land every target."""
    out: list[dict] = []
    for w in (0.25, 0.30, 0.35, 0.40, 0.45, 0.50):
        for a in (10.0, 12.0, 14.0, 16.0, 18.0, 20.0, 24.0):
            for b in (0.14, 0.16, 0.18, 0.20, 0.22, 0.24, 0.28):
                f = lambda p, ww=w, aa=a, bb=b: c_vein(p, w=ww, a=aa, b=bb)  # noqa: E731
                r = simulate(Curve(f"vein w={w} a={a} b={b}", f), players=players)
                ok, fails = verdict(r)
                out.append({**r, "w": w, "a": a, "b": b, "ok": ok, "fails": fails})
    return out


def print_spec(players: int, corr: float) -> None:
    s = spec()
    r = simulate(chosen_curve(), players=players, corr=corr)
    ok, fails = verdict(r)

    print(f"CHOSEN CURVE  {s['formula']}     (k rounded to {s['step']})")
    print("depth = 10 * k  metres;  700 m max\n")
    print("p -> k (depth)")
    for row in s["k_at_p"]:
        bar = "#" * int(round(row["k"] * 4))
        print(f"  p={row['p']:.2f}  k={row['k']:>4.1f}  {row['depth_m']:>5.0f} m  {bar}")
    print("\nk -> p (a rarer answer is required to reach this point)")
    for row in s["p_at_k"]:
        print(f"  k={row['k']:>4.1f}  p >= {row['p']:.4f}  (top {100 - row['p_pct']:.1f}% of the pool)")
    print("\nnarrative strata (labels only; scoring stays continuous)")
    print(f"  {'stratum':<14}{'p band':>16}{'pool':>8}{'k':>12}{'depth':>12}")
    for row in s["strata"]:
        print(f"  {row['name']:<14}{row['p_pct']:>16}{row['pool_share']:>7.1f}%"
              f"{row['k_lo']:>7.1f}-{row['k_hi']:<5.1f}{row['prompt_depth']:>12}")
    dz = s["dead_zones"]
    print(f"\ngranularity: {dz['distinct_k']} distinct k values; widest same-k band "
          f"{dz['max_band_pp']:.2f} pp at p={dz['max_band_at_p']:.2f} (k={dz['max_band_k']})")
    print(f"unreachable k in range: {dz['unreachable_k'] or 'none'}")

    slope, at = max_slope()
    print(f"\npool-size floor: steepest slope {slope:.1f} points/p at p={at:.2f} "
          f"({slope / 100:.2f} points per pp)")
    print(f"  {'N':>5}{'one rank':>11}{'worst m/rank':>14}{'most common answer':>20}")
    for n in (3, 5, 9, 15, 27, 39, 60, 100, 250):
        worst = slope / n * METRES_PER_POINT
        common = depth_of(1.0 / n)
        flag = "  <- below floor" if n < MIN_POOL else ""
        print(f"  {n:>5}{100 / n:>10.1f}pp{worst:>13.1f} m{common:>19.0f} m{flag}")
    print(f"  floor MIN_POOL = {MIN_POOL} (worst {slope / MIN_POOL * METRES_PER_POINT:.1f} m per rank)")
    print(f"\nsim ({players} dives, rho={corr}): p10 {r['p10']:.0f} | p50 {r['p50']:.0f} | "
          f"p90 {r['p90']:.0f} | >=600 {r['share_600'] * 100:.1f}% | "
          f"<200 {r['share_200']*100:.1f}% | perfect {r['share_max']*100:.2f}%")
    print("targets:", "ALL MET" if ok else "MISSED -> " + "; ".join(fails))


def main(argv: Sequence[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Garimpo scoring-curve simulator")
    ap.add_argument("--search", action="store_true", help="grid-search shape parameters")
    ap.add_argument("--frontier", action="store_true", help="median/p90 frontier sweep")
    ap.add_argument("--chosen", action="store_true", help="full spec of the shipped curve")
    ap.add_argument("--json", action="store_true", help="emit JSON, not text")
    ap.add_argument("--players", type=int, default=PLAYERS)
    ap.add_argument("--corr", type=float, default=0.0,
                    help="within-dive skill correlation rho, 0 = brief's iid model")
    ap.add_argument("--curve", default=None, help="single curve by name")
    ap.add_argument("--step", type=float, default=CHOSEN_STEP, help="k quantisation step")
    args = ap.parse_args(argv)

    if args.chosen:
        print_spec(args.players, args.corr)
        return 0

    if args.frontier:
        rows = frontier()
        if args.json:
            print(json.dumps(rows, indent=1))
            return 0
        print("frontier: k = f(p) in 0.1 steps, 10 000 dives per point\n")
        print(f"{'family':<8}{'param':<20}{'p10':>7}{'p50':>7}{'p90':>7}{'>=600':>7}{'<200':>7}"
              f"{'dz pp':>7}  median / p90")
        for r in rows:
            print(f"{r['family']:<8}{r['param']:<20}{r['p10']:>7.0f}{r['p50']:>7.0f}"
                  f"{r['p90']:>7.0f}{r['share_600'] * 100:>6.1f}%{r['share_200'] * 100:>6.1f}%"
                  f"{r['max_band_pp']:>7.1f}  {'in band' if r['in_band'] else 'out':>7}"
                  f" / {'yes' if r['p90_ok'] else 'no':>3}")
        return 0

    if args.search:
        rows = search()
        good = [r for r in rows if r["ok"]]
        if args.json:
            print(json.dumps(good, indent=1))
            return 0
        print(f"{len(good)} of {len(rows)} parameter sets meet every target "
              f"(6 000 dives each)\n")
        if good:
            print(table(sorted(good, key=lambda r: -r["p90"])[:20]))
        return 0

    if args.curve:
        known = {c.name: c for c in candidates()}
        if args.curve not in known:
            print("known curves:", ", ".join(known))
            return 2
        base = known[args.curve]
        curve = Curve(base.name, base.f, args.step, base.note)
        rows = [simulate(curve, players=args.players, corr=args.corr)]
    else:
        rows = [simulate(c, players=args.players, corr=args.corr) for c in candidates()]

    if args.json:
        print(json.dumps(rows, indent=1))
        return 0

    print(f"Garimpo curve sim -- {args.players} dives x {DIVE_PROMPTS} prompts, "
          f"miss rate {MISS_RATE:.0%}, seed {SEED}, rho={args.corr}\n")
    print(table(rows))
    print("\nmedian depth by skill class (the 55/30/15 mixture):")
    print(class_table(rows))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
