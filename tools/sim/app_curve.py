"""Calibrate the points curve against this dataset's own answer pools.

Player model is rank-based, because that is what a player actually chooses
between: the obvious answer, the second obvious, and so on. Run:

    PYTHONPATH=tools .venv-data/bin/python tools/sim/app_curve.py
"""
import json
import math
import random
from pathlib import Path

DATA = Path(__file__).resolve().parents[2] / "public" / "data" / "garimpo.json"
RNG = random.Random(20261104)  # noqa: S311 - simulation only, not cryptography


def vein(p: float) -> float:
    def g(x: float) -> float:
        return 0.35 * x + 0.65 / (1 + math.exp(-16 * (x - 0.2)))

    return (g(p) - g(0)) / (g(1) - g(0))


CURVES = {
    "vein": lambda p: 1 + 9 * vein(p),
    "p^0.30": lambda p: 1 + 9 * p**0.30,
    "p^0.32": lambda p: 1 + 9 * p**0.32,
    "p^0.35": lambda p: 1 + 9 * p**0.35,
    "p^0.40": lambda p: 1 + 9 * p**0.40,
    "p^0.45": lambda p: 1 + 9 * p**0.45,
}


def pick_rank(n: int, skill: float) -> int:
    """Return 1-based rank within the prompt, or 0 for a blank answer."""
    if RNG.random() < 0.12:
        return 0
    if skill < 0.55:  # casual: the obvious one, maybe the second
        weights = [0.55, 0.25, 0.12, 0.08]
    elif skill < 0.85:  # solid: a handful of options
        floor = max(6, n // 3)
        weights = [1 / (r**0.9) for r in range(1, floor + 1)]
    else:  # expert: digs past the obvious ones, sometimes straight for the deep cut
        if RNG.random() < 0.35:
            start = max(4, int(n * 0.66))
            if start <= n:
                return RNG.randint(start, n)
        floor = min(n, max(12, n // 2))
        weights = [0.06, 0.06, 0.06]
        weights += [r**0.9 for r in range(4, floor + 1)]
    total = sum(weights)
    roll = RNG.random() * total
    acc = 0.0
    for i, weight in enumerate(weights, start=1):
        acc += weight
        if roll <= acc:
            return i
    return 1


def main() -> None:
    try:
        data = json.loads(DATA.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise SystemExit(f"build the dataset first: {exc}") from exc

    prompts = data["prompts"]
    sizes = sorted(len(p["answers"]) for p in prompts)
    print(f"prompts={len(prompts)} median_pool={sizes[len(sizes) // 2]} "
          f"min={sizes[0]} max={sizes[-1]}")

    for name, curve in CURVES.items():
        totals = []
        for _ in range(4000):
            dive = 0.0
            for prompt in RNG.sample(prompts, 7):
                n = len(prompt["answers"])
                rank = pick_rank(n, RNG.random())
                if rank == 0:
                    continue
                answer = prompt["answers"][rank - 1]
                dive += round(curve(answer["rarity"]) * 10)
            totals.append(int(min(700, dive)))
        totals.sort()
        p50 = totals[len(totals) // 2]
        p10 = totals[len(totals) // 10]
        p90 = totals[int(len(totals) * 0.9)]
        over600 = sum(1 for t in totals if t >= 600) / len(totals)
        under200 = sum(1 for t in totals if t < 200) / len(totals)
        print(f"{name:10s} p10={p10:3d} p50={p50:3d} p90={p90:3d} "
              f">=600={over600 * 100:4.1f}% <200={under200 * 100:4.1f}%")


if __name__ == "__main__":
    main()
