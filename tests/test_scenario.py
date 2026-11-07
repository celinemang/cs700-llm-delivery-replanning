import networkx as nx

from delivery.config import load_config
from delivery.scenario import (build_graph, generate_scenario, make_scenarios, norm,
                               route_length)

ENV = load_config()["environment"]


def test_deterministic():
    a = generate_scenario(123, 3, ENV).to_dict()
    b = generate_scenario(123, 3, ENV).to_dict()
    assert a == b


def test_structure_and_invariants():
    for sev in (1, 3):
        for seed in range(40):
            s = generate_scenario(seed, sev, ENV)
            assert s.num_nodes == ENV["num_nodes"]
            assert len(s.destinations) == 4 and len(set(s.destinations)) == 4
            assert s.start not in s.destinations
            assert len(s.blocked_edges) == sev
            assert len({tuple(e) for e in s.blocked_edges}) == sev
            g0 = build_graph(s.num_nodes, s.edges)
            gb = build_graph(s.num_nodes, s.edges, s.blocked_edges)
            assert nx.is_connected(g0) and nx.is_connected(gb)
            assert all(w > 0 for _, _, w in s.edges)
            # at least one blocked edge lies on the planned remaining route
            route_edges = {norm(a, b) for a, b in zip(s.original_remaining_route, s.original_remaining_route[1:])}
            assert any(norm(*e) in route_edges for e in s.blocked_edges)
            # blocked edges exist in the original map
            assert all(g0.has_edge(*e) for e in s.blocked_edges)
            # budget = 2 x optimal remaining distance after the blockage
            assert s.budget == 2 * s.optimal_distance
            assert route_length(gb, s.optimal_route) == s.optimal_distance
            assert route_length(gb, s.same_order_route) == s.same_order_distance
            assert s.optimal_distance <= s.same_order_distance
            assert s.optimal_route[0] == s.current_node
            assert s.current_node == s.destinations[0]


def test_initial_plan_is_exact_optimum():
    s = generate_scenario(7, 1, ENV)
    g0 = build_graph(s.num_nodes, s.edges)
    # brute-force check against every order of all 4 destinations
    import itertools
    best = min(
        sum(nx.dijkstra_path_length(g0, a, b, weight="weight")
            for a, b in zip([s.start, *p], p))
        for p in itertools.permutations(s.destinations)
    )
    assert route_length(g0, s.original_route) == best


def test_balanced_sets():
    sc = make_scenarios("t", 5000, 6, ENV)
    assert sum(x.severity == 1 for x in sc) == sum(x.severity == 3 for x in sc) == 6
    assert len({x.scenario_id for x in sc}) == 12
