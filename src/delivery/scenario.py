"""Scenario generation and exact solvers.

A scenario is one independent unit: one map, one delivery task, one blockage set.
The robot starts at `start`, follows an exact-optimal initial plan, finishes the
first delivery, and then `blocked_edges` become unusable.
"""
from __future__ import annotations

import itertools
import random
from dataclasses import asdict, dataclass

import networkx as nx


def norm(u: int, v: int) -> tuple[int, int]:
    return (u, v) if u < v else (v, u)


@dataclass
class Scenario:
    scenario_id: str
    seed: int
    severity: int
    num_nodes: int
    edges: list  # [[u, v, length_m], ...] with u < v, sorted
    start: int
    destinations: list  # original delivery order, 4 nodes
    original_route: list  # full initial route (start -> all deliveries)
    current_node: int  # location after the first delivery
    remaining_original_order: list  # destinations[1:]
    original_remaining_route: list  # planned route from current_node onward
    blocked_edges: list  # [[u, v], ...]
    optimal_order: list  # best order of remaining goals after the blockage
    optimal_route: list
    optimal_distance: int
    same_order_route: list  # shortest-path route keeping the original order
    same_order_distance: int
    budget: float

    @property
    def same_order_within_budget(self) -> bool:
        return self.same_order_distance <= self.budget

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "Scenario":
        return cls(**d)


def build_graph(num_nodes: int, edges, blocked=()) -> nx.Graph:
    bl = {norm(*e) for e in blocked}
    g = nx.Graph()
    g.add_nodes_from(range(num_nodes))
    for u, v, w in edges:
        if norm(u, v) not in bl:
            g.add_edge(u, v, weight=w)
    return g


def route_for_order(g: nx.Graph, source: int, order) -> list:
    route = [source]
    cur = source
    for x in order:
        path = nx.dijkstra_path(g, cur, x, weight="weight")
        route += path[1:]
        cur = x
    return route


def route_length(g: nx.Graph, route) -> int:
    return sum(g[a][b]["weight"] for a, b in zip(route, route[1:]))


def best_order(g: nx.Graph, source: int, goals):
    """Exact best visiting order: try every permutation, join shortest paths.

    Ties are broken by the lexicographically smallest order (deterministic).
    Returns (total_distance, order, route).
    """
    nodes = [source, *goals]
    dist = {s: nx.single_source_dijkstra_path_length(g, s, weight="weight") for s in nodes}
    best = None
    for perm in itertools.permutations(sorted(goals)):
        total, cur = 0, source
        for x in perm:
            total += dist[cur][x]
            cur = x
        if best is None or (total, perm) < best:
            best = (total, perm)
    total, perm = best
    return total, list(perm), route_for_order(g, source, perm)


def _random_edges(rng: random.Random, n: int, m: int, lo: int, hi: int) -> list:
    nodes = list(range(n))
    rng.shuffle(nodes)
    pairs = set()
    for i in range(1, n):  # random spanning tree -> connected
        pairs.add(norm(nodes[i], nodes[rng.randrange(i)]))
    while len(pairs) < m:
        u, v = rng.sample(range(n), 2)
        pairs.add(norm(u, v))
    return [[u, v, rng.randint(lo, hi)] for u, v in sorted(pairs)]


def generate_scenario(seed: int, severity: int, env: dict, scenario_id: str | None = None) -> Scenario:
    """Rejection-sample a valid scenario; fully determined by (seed, severity, env)."""
    n = env["num_nodes"]
    k = env["num_deliveries"]
    m = round(env["avg_degree"] * n / 2)
    lo, hi = env["edge_length_m"]
    rng = random.Random(seed)
    for _ in range(10_000):
        edges = _random_edges(rng, n, m, lo, hi)
        g = build_graph(n, edges)
        picks = rng.sample(range(n), k + 1)
        start, goals = picks[0], picks[1:]
        _, order, route = best_order(g, start, goals)
        # route is start -> order[0] -> ... ; split at the first delivery
        first = order[0]
        i0 = route.index(first)
        remaining_route = route[i0:]
        route_edges = sorted({norm(a, b) for a, b in zip(remaining_route, remaining_route[1:])})
        if not route_edges:
            continue
        chosen = [rng.choice(route_edges)]
        others = sorted({(u, v) for u, v, _ in edges} - set(chosen))
        chosen += rng.sample(others, severity - 1)
        gb = build_graph(n, edges, chosen)
        if not nx.is_connected(gb):
            continue
        rest = order[1:]
        opt_d, opt_order, opt_route = best_order(gb, first, rest)
        so_route = route_for_order(gb, first, rest)
        so_d = route_length(gb, so_route)
        sid = scenario_id or f"s{severity}-{seed}"
        return Scenario(
            scenario_id=sid, seed=seed, severity=severity, num_nodes=n, edges=edges,
            start=start, destinations=[first, *rest], original_route=route,
            current_node=first, remaining_original_order=list(rest),
            original_remaining_route=remaining_route,
            blocked_edges=[list(e) for e in chosen],
            optimal_order=opt_order, optimal_route=opt_route, optimal_distance=opt_d,
            same_order_route=so_route, same_order_distance=so_d,
            budget=env["budget_multiplier"] * opt_d,
        )
    raise RuntimeError(f"no valid scenario for seed={seed} severity={severity}")


def make_scenarios(split: str, base_seed: int, n_per_severity: int, env: dict, severities=(1, 3)) -> list:
    """Balanced scenario set; seed = base + severity*10000 + index."""
    out = []
    for sev in severities:
        for i in range(n_per_severity):
            out.append(generate_scenario(base_seed + sev * 10_000 + i, sev, env,
                                         scenario_id=f"{split}-s{sev}-{i:03d}"))
    return out
