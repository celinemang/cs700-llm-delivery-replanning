"""Structural diagnostics of the scenario generator (no LLM). Uses a seed range
disjoint from pilot/main so it never touches confirmatory data."""
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from delivery.config import load_config
from delivery.scenario import make_scenarios

cfg = load_config()
N = 500
sc = make_scenarios("diag", 900_000, N, cfg["environment"])
lines = ["# Step 2 diagnostics (oracle solvers, no LLM)", "",
         f"{N} scenarios per severity, seeds 900000+ (disjoint from pilot/main).", "",
         "| severity | same-order within 2x budget | order change helps (opt order != original) | ratio same-order/optimal: mean | p90 | max | optimal remaining dist mean (m) |",
         "|---|---|---|---|---|---|---|"]
for sev in (1, 3):
    s = [x for x in sc if x.severity == sev]
    within = np.mean([x.same_order_within_budget for x in s])
    helps = np.mean([x.optimal_order != x.remaining_original_order for x in s])
    ratio = np.array([x.same_order_distance / x.optimal_distance for x in s])
    od = np.mean([x.optimal_distance for x in s])
    lines.append(f"| {sev} | {within:.1%} | {helps:.1%} | {ratio.mean():.3f} | {np.percentile(ratio,90):.3f} | {ratio.max():.3f} | {od:.1f} |")
out = ROOT / "logs" / "step2_report.md"
out.write_text("\n".join(lines) + "\n")
print("\n".join(lines))
