"""Combination strategies.

Full Cartesian product, pairwise (2-wise) via IPOG-ish greedy covering, and
random-N sampling. Pure standard library, no dependencies.
"""
from __future__ import annotations

import itertools
import random
from typing import Any


def generate(dimensions: dict[str, list[Any]], strategy: str = "pairwise") -> list[dict[str, Any]]:
    if not dimensions:
        return [{}]
    if strategy == "full":
        return _full(dimensions)
    if strategy == "pairwise":
        return _pairwise(dimensions)
    if strategy.startswith("random:"):
        try:
            n = int(strategy.split(":", 1)[1])
        except ValueError as e:
            raise ValueError(f"invalid random strategy {strategy!r}") from e
        return _random(dimensions, n)
    raise ValueError(f"unknown strategy: {strategy!r}")


def _full(dims: dict[str, list[Any]]) -> list[dict[str, Any]]:
    keys = list(dims)
    return [dict(zip(keys, combo)) for combo in itertools.product(*(dims[k] for k in keys))]


def _random(dims: dict[str, list[Any]], n: int) -> list[dict[str, Any]]:
    all_combos = _full(dims)
    if n >= len(all_combos):
        return all_combos
    rnd = random.Random(31)
    return rnd.sample(all_combos, n)


def _pairwise(dims: dict[str, list[Any]]) -> list[dict[str, Any]]:
    """Greedy pairwise cover.

    Build the set of all (i, j, a_i, a_j) pairs that must be covered, then
    repeatedly pick a full combination that covers the most uncovered pairs.
    Terminates when every pair is covered. Small-problem optimal it is not,
    but it produces substantially smaller matrices than full product for
    dims with 3+ parameters.
    """
    keys = list(dims)
    if len(keys) < 2:
        return _full(dims)

    # Enumerate required pairs.
    required: set[tuple[int, int, Any, Any]] = set()
    for i, j in itertools.combinations(range(len(keys)), 2):
        for a in dims[keys[i]]:
            for b in dims[keys[j]]:
                required.add((i, j, a, b))

    full = _full(dims)  # candidate pool

    selected: list[dict[str, Any]] = []
    covered: set[tuple[int, int, Any, Any]] = set()
    while covered != required:
        best = None
        best_gain = -1
        for combo in full:
            gain = 0
            for i, j in itertools.combinations(range(len(keys)), 2):
                pair = (i, j, combo[keys[i]], combo[keys[j]])
                if pair in required and pair not in covered:
                    gain += 1
            if gain > best_gain:
                best_gain = gain
                best = combo
                if gain == len(required) - len(covered):
                    break
        if best is None or best_gain <= 0:
            break
        selected.append(best)
        for i, j in itertools.combinations(range(len(keys)), 2):
            pair = (i, j, best[keys[i]], best[keys[j]])
            if pair in required:
                covered.add(pair)
    return selected


def explode_combinations(
    base: list[dict[str, Any]],
    viewports: list[str],
    browsers: list[str],
) -> list[dict[str, Any]]:
    """Cross every base combination with each viewport × browser."""
    out = []
    for b in base:
        for vp in viewports:
            for br in browsers:
                row = dict(b)
                row["_viewport"] = vp
                row["_browser"] = br
                out.append(row)
    return out
