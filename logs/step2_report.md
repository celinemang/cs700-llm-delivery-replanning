# Step 2 diagnostics (oracle solvers, no LLM)

500 scenarios per severity, seeds 900000+ (disjoint from pilot/main).

| severity | same-order within 2x budget | order change helps (opt order != original) | ratio same-order/optimal: mean | p90 | max | optimal remaining dist mean (m) |
|---|---|---|---|---|---|---|
| 1 | 100.0% | 41.4% | 1.049 | 1.185 | 1.789 | 180.7 |
| 3 | 100.0% | 48.2% | 1.068 | 1.230 | 1.724 | 192.5 |

## Reading

- Invariants (connected before/after blockage, >=1 blocked edge on the planned remaining route, balanced severities, budget = 2x optimal, exact solver) are enforced by `tests/` (22 tests pass).
- The order-preserving shortest path **never** exceeds the 2x budget (max ratio 1.79). So local repair is not structurally disadvantaged: any success-rate gap between strategies in the main study comes from LLM planning errors, not from the repair rule itself.
- Reordering strictly helps in only 41-48% of scenarios and by about 5-7% distance on average. With a loose 2x budget, a strong model may reach near-100% success under both strategies (ceiling effect). The pilot (step 5) must show whether this happens; any change to difficulty (e.g., budget multiplier) must be made before freezing and logged in `logs/deviation_log.md`.
