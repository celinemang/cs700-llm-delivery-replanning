# Pilot report

Model: qwen2.5:14b-instruct (digest 7cdf5a0187d5)
Requests with a result: 48

Parse rate: 48/48 (100%) | mean tokens/request: 798 | mean latency: 25.0s

## Success by cell

| severity | full replanning | local repair |
|---|---|---|
| 1 | 4/12 (33%) | 4/12 (33%) |
| 3 | 1/12 (8%) | 3/12 (25%) |

## Paired success difference D = full - repair, and sample size

Target: 95% CI half-width 0.10 for the paired success difference, per severity.
n = (1.96 * s_D / 0.10)^2, rounded up; floor 30, cap 200 per severity.

| severity | pairs | mean D | s_D | n (formula) | n (bootstrap p90) | planned n |
|---|---|---|---|---|---|---|
| 1 | 12 | +0.00 | 0.74 | 210 | 268 | 200 |
| 3 | 12 | -0.17 | 0.39 | 59 | 94 | 94 |

Planned main-study n per severity: sev1=200, sev3=94 (total scenarios = 294, total requests = 588).

