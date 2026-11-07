# Comparing Full Replanning and Local Plan Repair for LLM-Based Delivery Robots Under Route Blockages

Author: Celine Mang (CS700 term project)

This project compares two ways an LLM-based delivery robot can react when a
hallway is blocked, using a small simulated delivery world built from a graph:

- **Full replanning**: may change both the order of the remaining deliveries and the route.
- **Local plan repair**: keeps the order of the remaining deliveries and only changes the paths between them.

The design is a 2x2 factorial: strategy (full replanning / local repair) x
blockage severity (1 / 3 blocked hallways). The study tests high-level planning
only, not physical navigation or robot control.

## Hypotheses

- H1: Full replanning has a higher delivery success rate than local repair.
- H2: This advantage is larger when three hallways are blocked than when one is blocked.

## Metrics

Delivery success (%), extra travel distance vs. an exact best route (%),
tokens per planning request, and the number of movement/strategy rule violations.

## Repository layout

- `proposal/main.tex` - project proposal (LaTeX)

Code, data, and analysis will be added as the project progresses.
