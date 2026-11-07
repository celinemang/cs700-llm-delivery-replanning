import json

import pytest

from delivery.config import load_config
from delivery.prompts import build_prompt
from delivery.scenario import generate_scenario, norm
from delivery.validator import FULL, REPAIR, parse_output, validate

ENV = load_config()["environment"]


def resp(deliveries, route):
    return json.dumps({"deliveries": deliveries, "route": route})


@pytest.fixture(scope="module")
def scn():
    # pick a scenario where reordering strictly helps and fixed order still fits the budget
    for seed in range(500):
        s = generate_scenario(seed, 3, ENV)
        if s.optimal_order != s.remaining_original_order and s.same_order_within_budget:
            return s
    raise AssertionError("no suitable scenario")


def test_oracle_full_succeeds(scn):
    r = validate(scn, FULL, resp(scn.optimal_order, scn.optimal_route))
    assert r.success and r.violations == 0 and r.extra_pct == 0.0


def test_oracle_repair_succeeds_with_same_order(scn):
    r = validate(scn, REPAIR, resp(scn.remaining_original_order, scn.same_order_route))
    assert r.success and r.extra_pct >= 0


def test_repair_rejects_reordering(scn):
    r = validate(scn, REPAIR, resp(scn.optimal_order, scn.optimal_route))
    assert not r.success and "order_violation" in r.violation_types


def test_blocked_edge_detected(scn):
    a, b = scn.blocked_edges[0]
    route = [scn.current_node]
    # original remaining route uses a blocked edge
    r = validate(scn, FULL, resp(scn.remaining_original_order, scn.original_remaining_route))
    assert not r.success and "blocked_edge" in r.violation_types
    assert r.violations == sum(norm(x, y) in {norm(*e) for e in scn.blocked_edges}
                               for x, y in zip(scn.original_remaining_route, scn.original_remaining_route[1:]))


def test_bad_edge_bad_start_missing_delivery(scn):
    route = list(scn.optimal_route)
    assert "bad_start" in validate(scn, FULL, resp(scn.optimal_order, route[1:])).violation_types
    teleport = [route[0], route[-1]]
    assert "bad_edge" in validate(scn, FULL, resp(scn.optimal_order, teleport)).violation_types
    assert "not_delivered" in validate(scn, FULL, resp(scn.optimal_order, route[:-1])).violation_types
    assert "bad_deliveries" in validate(scn, FULL, resp(scn.optimal_order[:-1], route)).violation_types


def test_wrong_declared_order_not_delivered(scn):
    rev = list(reversed(scn.optimal_order))
    if rev != scn.optimal_order:
        r = validate(scn, FULL, resp(rev, scn.optimal_route))
        assert not r.success


def test_over_budget_is_failure_not_violation(scn):
    # pad the optimal route with a detour back and forth until it exceeds the budget
    route = list(scn.optimal_route)
    nxt = route[1]
    detour = route[:1]
    while True:
        detour += [nxt, route[0]]
        padded = detour + route[1:]
        r = validate(scn, FULL, resp(scn.optimal_order, padded))
        if r.distance > scn.budget:
            break
    assert not r.success and r.violations == 0 and r.failure_reason == "over_budget"


@pytest.mark.parametrize("text", ["", "no json", "{\"route\": [1]}", "[1,2]",
                                  '{"deliveries": [1.5], "route": [1]}',
                                  '{"deliveries": [true], "route": [1]}',
                                  '{"deliveries": [], "route": [1]}'])
def test_unparseable(text, scn):
    r = validate(scn, FULL, text)
    assert not r.parsed and not r.success


def test_parse_handles_code_fence():
    assert parse_output('```json\n{"deliveries": [1], "route": [0, 1]}\n```') == {"deliveries": [1], "route": [0, 1]}


def test_prompts_same_info_except_rule(scn):
    _, pf = build_prompt(scn, FULL)
    _, pr = build_prompt(scn, REPAIR)
    assert pf != pr
    lf = set(pf.splitlines()); lr = set(pr.splitlines())
    diff = lf ^ lr
    assert len(diff) == 2 and all("Strategy:" in x for x in diff)
    for e in scn.blocked_edges:
        assert f"{min(e)}-{max(e)}" in pf
    assert f"node {scn.current_node}" in pf and f"{scn.budget:g}" in pf
