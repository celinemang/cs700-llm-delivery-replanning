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
    "- Every consecutive pair of nodes in your route MUST be directly connected: the second node must appear "
    "in the first node's neighbor list above. Do not invent hallways.\n"
    "- Blocked hallways cannot be used in either direction.\n"
    "- A delivery is made when the route arrives at that delivery node.\n"
    "- Every remaining delivery must be made exactly once.\n"
    "- The route must start at the robot's current node.\n"
    "- The total length of the route must not exceed the travel budget; shorter is better.\n"
    "Build the route one hop at a time. Before adding a node, check that it is listed as a neighbor "
    "of the current node. Trace and verify the whole route against the neighbor list before answering."
)

WORKED_EXAMPLE = (
    "Worked example (a different, smaller map, just to show the method):\n"
    "  node 0: 1 (5 m), 2 (9 m)\n"
    "  node 1: 0 (5 m), 3 (4 m)\n"
    "  node 2: 0 (9 m), 3 (3 m)\n"
    "  node 3: 1 (4 m), 2 (3 m)\n"
    "Current node 0, must deliver to 3. Route [0, 1, 3] is valid: 0-1 is listed, 1-3 is listed. "
    "Route [0, 3] would be INVALID because 3 is not a neighbor of 0."
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
    adj = {i: [] for i in range(scn.num_nodes)}
    for u, v, w in scn.edges:
        if norm(u, v) not in blocked:
            adj[u].append((v, w))
            adj[v].append((u, w))
    usable = [f"node {i}: " + ", ".join(f"{j} ({w} m)" for j, w in sorted(nb)) for i, nb in adj.items()]
    blocked_txt = ", ".join(f"{u}-{v}" for u, v in sorted(blocked))
    user = "\n\n".join([
        f"Map: {scn.num_nodes} nodes (0 to {scn.num_nodes - 1}). Open hallways, listed as the direct neighbors of each node (with hallway length):\n"
        + "\n".join(usable),
        f"Blocked hallways (cannot be used): {blocked_txt}",
        f"Current state: the robot has just completed a delivery and is now at node {scn.current_node}.",
        "Remaining deliveries in the original plan order: "
        + ", ".join(str(x) for x in scn.remaining_original_order),
        "Original plan for the rest of the trip (made before the blockage), as a route: "
        + " -> ".join(str(x) for x in scn.original_remaining_route),
        f"Travel budget: the total route length must be at most {scn.budget:g} m.",
        RULES_COMMON,
        WORKED_EXAMPLE,
        STRATEGY_RULE[strategy],
        FORMAT,
    ])
    return SYSTEM, user
