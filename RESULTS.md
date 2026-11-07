# Results

Model: `qwen2.5:14b-instruct` (local, via Ollama). Maps: 8 nodes, 4 deliveries,
blockage after the first delivery, travel budget = 2x the exact best remaining
distance. Main study: 294 scenarios (200 at severity 1, 94 at severity 3), each
run under both strategies as a matched pair = 588 planning requests. 100% of
responses parsed; no transport errors. Pilot data were used only for
sample-size planning and are excluded from the confirmatory analysis.

## Success rate (primary outcome)

| | full replanning | local repair | difference (full - repair) |
|---|---|---|---|
| severity 1 (1 blocked) | 67/200 = 34% | 88/200 = 44% | -10 pp (95% CI -18..-3) |
| severity 3 (3 blocked) | 20/94 = 21% | 29/94 = 31% | -10 pp (95% CI -17..-2) |
| overall | 87/294 = 30% | 117/294 = 40% | -10 pp |

## H1 - full replanning vs local repair

**Rejected, and reversed.** Local repair succeeded *more* often than full
replanning. Among the 74 scenarios where the two strategies disagreed, repair
was the sole success 52 times and full replanning only 22 times (exact McNemar
p = 0.0006; Holm-adjusted 0.0013). The pre-registered direction (full > repair)
is contradicted at the 5% level.

Interpretation: for this model, re-deriving the delivery order from scratch
introduces more planning errors than it saves. Keeping the known-good order and
only re-routing (local repair) is the more reliable strategy here.

## H2 - does the gap grow with severity?

**Not supported.** The repair advantage is about the same size at both
severities (-10 pp each). The strategy x severity interaction is essentially
zero (logistic coefficient -0.057, cluster-robust p = 0.82; Holm 0.82). The
estimation-based backup agrees: difference of risk differences (sev3 - sev1)
= +0.01, 95% CI -0.10..+0.11.

## Secondary metrics

- **Travel efficiency (both strategies succeeded, n = 65):** extra distance over
  the exact best route was ~22% for both (full 22.7%, repair 22.2%; paired
  difference +0.5 pp). When a plan works, the two strategies are about equally
  efficient; the strategy effect is on *whether* a plan is valid, not on its length.
- **Tokens:** ~800 tokens/request for both strategies (full 795, repair 808).
- **Failure causes (counts across all failed requests):** invented hallway
  (bad_edge) 285, use of a blocked hallway 128, a declared delivery never
  reached 95, over budget without any rule violation 14, wrong delivery set 11.
  Path-tracing errors remain the dominant failure mode; the budget rule rarely bites.

## Takeaway

On small graphs with a 14B local model, **local plan repair outperforms full
replanning in delivery success**, by about 10 percentage points, independent of
how many hallways are blocked. Both pre-registered hypotheses were rejected -
one significantly in the opposite direction. The result is specific to synthetic
8-node maps and a single local model, and the dominant failure mode is low-level
path tracing rather than high-level strategy, which bounds how far these numbers
generalize.
