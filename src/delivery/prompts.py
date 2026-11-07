"""Prompt templates. Both strategies get identical information; only the
strategy rule paragraph differs. Frozen after the pilot (see config.yaml)."""
from __future__ import annotations

from .scenario import norm
from .validator import FULL, REPAIR

SYSTEM = (
    "You are the high-level route planner of a delivery robot in a building. "
    "You answer with a single JSON object and nothing else."
)

RULES_COMMON = (
    "Rules:\n"
    "- The robot moves along hallways only, one hallway per step, from one node to a directly connected node.\n"
    "- Blocked hallways cannot be used in either direction.\n"
    "- A delivery is made when the route arrives at that delivery node.\n"
    "- Every remaining delivery must be made exactly once.\n"
    "- The route must start at the robot's current node.\n"
    "- The total length of the route must not exceed the travel budget; shorter is better."
)

STRATEGY_RULE = {
    FULL: (
        "Strategy: FULL REPLANNING. You may change both the order of the remaining deliveries "
        "and the route."
    ),
    REPAIR: (
        "Strategy: LOCAL REPAIR. You must keep the remaining deliveries in exactly the same order "
        "as in the original plan. You may only change the paths between consecutive deliveries."
    ),
}

FORMAT = (
    "Output format: a JSON object with two keys.\n"
    '  "deliveries": the remaining delivery nodes in the order you will deliver them\n'
    '  "route": the full list of nodes the robot visits, starting at the current node\n'
    'Example: {"deliveries": [4, 9, 2], "route": [7, 3, 4, 8, 9, 5, 2]}'
)


def build_prompt(scn, strategy: str) -> tuple[str, str]:
    blocked = {norm(*e) for e in scn.blocked_edges}
    usable = [f"{u}-{v}: {w} m" for u, v, w in scn.edges if norm(u, v) not in blocked]
    blocked_txt = ", ".join(f"{u}-{v}" for u, v in sorted(blocked))
    user = "\n\n".join([
        f"Map: {scn.num_nodes} nodes (0 to {scn.num_nodes - 1}). Open hallways (undirected, with length):\n"
        + "\n".join(usable),
        f"Blocked hallways (cannot be used): {blocked_txt}",
        f"Current state: the robot has just completed a delivery and is now at node {scn.current_node}.",
        "Remaining deliveries in the original plan order: "
        + ", ".join(str(x) for x in scn.remaining_original_order),
        "Original plan for the rest of the trip (made before the blockage), as a route: "
        + " -> ".join(str(x) for x in scn.original_remaining_route),
        f"Travel budget: the total route length must be at most {scn.budget:g} m.",
        RULES_COMMON,
        STRATEGY_RULE[strategy],
        FORMAT,
    ])
    return SYSTEM, user
