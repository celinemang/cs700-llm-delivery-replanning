"""Output parser and plan validator.

Expected model output: a JSON object
    {"deliveries": [d1, d2, d3], "route": [n0, n1, ..., nk]}
`deliveries` is the declared order of the remaining deliveries; `route` is the
node-by-node walk starting at the robot's current node.

Violation counting (each counts 1):
  bad_edge        a hop between two nodes that share no hallway (or unknown node)
  blocked_edge    a hop over a blocked hallway
  bad_start       route does not start at the current node
  bad_deliveries  declared deliveries are not a permutation of the remaining goals
  order_violation (local repair only) declared order differs from the original order
  not_delivered   route does not visit the declared deliveries in the declared order
Success = parsed, zero violations, and route length <= travel budget.
Exceeding the budget is a failure but not a rule violation.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field

from .scenario import build_graph, norm, route_length

FULL = "full_replanning"
REPAIR = "local_repair"


@dataclass
class Result:
    parsed: bool
    success: bool
    violations: int = 0
    violation_types: list = field(default_factory=list)
    distance: int | None = None
    within_budget: bool | None = None
    extra_pct: float | None = None  # vs exact best remaining route; set only when success
    failure_reason: str = ""


def parse_output(text: str):
    """Extract the plan JSON; returns dict or None. Strict about types."""
    if not isinstance(text, str):
        return None
    s = text.strip()
    s = re.sub(r"^```(?:json)?\s*|\s*```$", "", s)
    i, j = s.find("{"), s.rfind("}")
    if i < 0 or j <= i:
        return None
    try:
        obj = json.loads(s[i:j + 1])
    except json.JSONDecodeError:
        return None
    if not isinstance(obj, dict):
        return None
    for key in ("deliveries", "route"):
        v = obj.get(key)
        if not isinstance(v, list) or not v:
            return None
        if any(isinstance(x, bool) or not isinstance(x, int) for x in v):
            return None
    return {"deliveries": obj["deliveries"], "route": obj["route"]}


def validate(scn, strategy: str, text: str) -> Result:
    plan = parse_output(text)
    if plan is None:
        return Result(parsed=False, success=False, failure_reason="unparseable")
    g = build_graph(scn.num_nodes, scn.edges, scn.blocked_edges)
    full = build_graph(scn.num_nodes, scn.edges)
    blocked = {norm(*e) for e in scn.blocked_edges}
    route, deliveries = plan["route"], plan["deliveries"]
    types: list = []

    if route[0] != scn.current_node:
        types.append("bad_start")
    for a, b in zip(route, route[1:]):
        ok_nodes = 0 <= a < scn.num_nodes and 0 <= b < scn.num_nodes
        if not ok_nodes or not full.has_edge(a, b):
            types.append("bad_edge")
        elif norm(a, b) in blocked:
            types.append("blocked_edge")
    if sorted(deliveries) != sorted(scn.remaining_original_order):
        types.append("bad_deliveries")
    elif strategy == REPAIR and deliveries != scn.remaining_original_order:
        types.append("order_violation")
    # subsequence check: route must visit declared deliveries in declared order
    pos = 0
    for node in route:
        if pos < len(deliveries) and node == deliveries[pos]:
            pos += 1
    if pos < len(deliveries):
        types.append("not_delivered")

    res = Result(parsed=True, success=False, violations=len(types), violation_types=types)
    if types:
        res.failure_reason = "rule_violation"
        return res
    res.distance = route_length(g, route)
    res.within_budget = res.distance <= scn.budget
    if not res.within_budget:
        res.failure_reason = "over_budget"
        return res
    res.success = True
    res.extra_pct = 100.0 * (res.distance - scn.optimal_distance) / scn.optimal_distance
    return res
