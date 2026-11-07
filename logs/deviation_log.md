# Deviation log

Dated record of every change to the pre-registered design, with its effect on the results.

| Date | Change | Reason | Effect on results |
|------|--------|--------|-------------------|
| 2026-11-07 | Changed prompt: added explicit "only move to a listed neighbor / verify each hop" rule and a small worked example on a separate illustrative map. | Pilot-phase calibration on dev seeds (7,000,000+): the local model produced near-valid routes but invented 1-2 nonexistent hallways, failing both strategies equally (~5% success). | Prompt still differs between strategies by exactly one line (the strategy rule), enforced by a test. Adds ~200 tokens/request. Applied before freezing. |
| 2026-11-07 | Reduced map size from 20 to 8 nodes (num_deliveries, degree, severities, budget rule unchanged). | Calibration sweep on dev seeds (8,000,000+): 20 and 12 nodes left both strategies on the floor (path-tracing errors swamped the strategy effect); 8 nodes put both strategies in the measurable 20-80% band. The study targets high-level planning (order vs route), so a smaller map isolates the strategy variable instead of testing adjacency-list memorization. | Keeps the 2x2 design, metrics, and exact solvers intact. Limits external validity to small maps (already a stated limitation). Applied before freezing. |
| 2026-11-07 | Selected model qwen2.5:14b-instruct (local, via Ollama) over qwen2.5:7b-instruct. | 7B reached ~5% success on dev seeds; 14B is the largest that fits 16 GB RAM and reached the measurable band at 8 nodes. Free, no API key, fully reproducible (digest logged). | Single-model limitation already stated in the proposal. Exact tag + digest recorded in data/*/run_meta.json. |
