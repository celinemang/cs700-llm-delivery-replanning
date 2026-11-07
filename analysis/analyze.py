"""Analysis for the pilot and the main study.

Pilot mode  (python -m analysis.analyze pilot):
  - success rates per cell, parse rate, token use, latency
  - paired success difference D_i = full - repair within each severity
  - s_D and the sample-size estimate n = (1.96 s_D / 0.10)^2 (ceil), with a
    bootstrap check, per the proposal
Main mode   (python -m analysis.analyze main):
  - McNemar exact test for H1 (pooled paired successes)
  - logistic regression: success ~ strategy * severity, cluster-robust SE, for H2
  - Holm correction over the two confirmatory tests
  - stratified paired bootstrap CIs for success differences and the interaction
"""
from __future__ import annotations

import json
import math
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
FULL, REPAIR = "full_replanning", "local_repair"
RNG = np.random.default_rng(20261107)


def load(split: str):
    rows = [json.loads(l) for l in (ROOT / "data" / split / "responses.jsonl").read_text().splitlines()]
    return [r for r in rows if r.get("result")]


def pairs(rows):
    """Return {severity: [(full_success, repair_success), ...]} over scenarios with both strategies."""
    by = defaultdict(dict)
    for r in rows:
        by[r["scenario_id"]][r["strategy"]] = r
    out = defaultdict(list)
    for sid, d in by.items():
        if FULL in d and REPAIR in d:
            sev = d[FULL]["severity"]
            out[sev].append((int(d[FULL]["result"]["success"]), int(d[REPAIR]["result"]["success"])))
    return out


def rate(rows, sev, strat):
    r = [x for x in rows if x["severity"] == sev and x["strategy"] == strat]
    s = sum(x["result"]["success"] for x in r)
    return s, len(r)


def pilot_report(rows) -> str:
    L = ["# Pilot report", "", f"Model: {rows[0]['model']} (digest {rows[0].get('model_digest','?')[:12]})",
         f"Requests with a result: {len(rows)}", ""]
    parsed = sum(x["result"]["parsed"] for x in rows)
    toks = np.mean([x["input_tokens"] + x["output_tokens"] for x in rows])
    lat = np.mean([x.get("latency_s", 0) for x in rows])
    L += [f"Parse rate: {parsed}/{len(rows)} ({parsed/len(rows):.0%}) | mean tokens/request: {toks:.0f} | mean latency: {lat:.1f}s", "",
          "## Success by cell", "", "| severity | full replanning | local repair |", "|---|---|---|"]
    for sev in (1, 3):
        fs, fn = rate(rows, sev, FULL); rs, rn = rate(rows, sev, REPAIR)
        L.append(f"| {sev} | {fs}/{fn} ({fs/fn:.0%}) | {rs}/{rn} ({rs/rn:.0%}) |")
    L += ["", "## Paired success difference D = full - repair, and sample size", "",
          "Target: 95% CI half-width 0.10 for the paired success difference, per severity.",
          "n = (1.96 * s_D / 0.10)^2, rounded up; floor 30, cap 200 per severity.", "",
          "| severity | pairs | mean D | s_D | n (formula) | n (bootstrap p90) | planned n |", "|---|---|---|---|---|---|---|"]
    pr = pairs(rows)
    plan = {}
    for sev in (1, 3):
        D = np.array([f - r for f, r in pr[sev]], float)
        sd = D.std(ddof=1) if len(D) > 1 else 0.0
        n_formula = math.ceil((1.96 * sd / 0.10) ** 2) if sd > 0 else 30
        # bootstrap: resample pairs, recompute n needed; take a cautious p90
        boots = []
        for _ in range(2000):
            samp = D[RNG.integers(0, len(D), len(D))]
            s = samp.std(ddof=1)
            boots.append((1.96 * s / 0.10) ** 2 if s > 0 else 0)
        n_boot = math.ceil(np.percentile(boots, 90)) if np.any(boots) else 30
        planned = int(min(200, max(30, n_boot)))
        plan[sev] = planned
        L.append(f"| {sev} | {len(D)} | {D.mean():+.2f} | {sd:.2f} | {n_formula} | {n_boot} | {planned} |")
    L += ["", f"Planned main-study n per severity: sev1={plan[1]}, sev3={plan[3]} "
             f"(total scenarios = {plan[1]+plan[3]}, total requests = {2*(plan[1]+plan[3])}).", ""]
    if all(np.array([f - r for f, r in pr[sev]]).std() == 0 for sev in (1, 3)):
        L.append("WARNING: zero variance in D for at least one severity. Per the proposal, do NOT treat "
                 "this as proof of precision; revisit task difficulty and use a cautious variance bound.")
    return "\n".join(L) + "\n"


def mcnemar_exact(pairs_list):
    """H1: among discordant pairs, is full more often the sole success? b=full-only, c=repair-only."""
    from scipy.stats import binomtest
    b = sum(1 for f, r in pairs_list if f == 1 and r == 0)
    c = sum(1 for f, r in pairs_list if f == 0 and r == 1)
    p = binomtest(b, b + c, 0.5).pvalue if (b + c) else 1.0
    return b, c, p


def holm(pvals: dict) -> dict:
    items = sorted(pvals.items(), key=lambda kv: kv[1])
    m = len(items); out = {}; prev = 0
    for i, (k, p) in enumerate(items):
        adj = max(prev, min(1.0, (m - i) * p)); out[k] = adj; prev = adj
    return out


def main_report(rows) -> str:
    import pandas as pd
    import statsmodels.formula.api as smf

    pr = pairs(rows)
    L = ["# Main study analysis", "", f"Model: {rows[0]['model']}", ""]
    # H1 McNemar pooled
    allp = pr[1] + pr[3]
    b, c, p1 = mcnemar_exact(allp)
    # H2 logistic with interaction, cluster-robust by scenario
    recs = []
    for r in rows:
        recs.append(dict(success=int(r["result"]["success"]),
                         strat=1 if r["strategy"] == FULL else 0,
                         sev=1 if r["severity"] == 3 else 0,
                         scenario=r["scenario_id"]))
    df = pd.DataFrame(recs)
    m = smf.logit("success ~ strat * sev", data=df).fit(disp=0, cov_type="cluster",
                                                         cov_kwds={"groups": df["scenario"]})
    inter_p = m.pvalues["strat:sev"]
    adj = holm({"H1_mcnemar": p1, "H2_interaction": inter_p})

    # risk differences (full - repair) per severity + stratified paired bootstrap CI
    def rd(ps):
        a = np.array(ps); return (a[:, 0] - a[:, 1]).mean() if len(a) else float("nan")
    rd1, rd3 = rd(pr[1]), rd(pr[3])
    boots_rd1, boots_rd3, boots_int = [], [], []
    for _ in range(10000):
        s1 = [pr[1][i] for i in RNG.integers(0, len(pr[1]), len(pr[1]))]
        s3 = [pr[3][i] for i in RNG.integers(0, len(pr[3]), len(pr[3]))]
        r1, r3 = rd(s1), rd(s3)
        boots_rd1.append(r1); boots_rd3.append(r3); boots_int.append(r3 - r1)

    def ci(b):
        return np.percentile(b, 2.5), np.percentile(b, 97.5)
    L += ["## H1: full replanning vs local repair (success)",
          f"- McNemar exact: full-only wins b={b}, repair-only wins c={c}, p={p1:.4f} (Holm {adj['H1_mcnemar']:.4f})",
          f"- Risk difference (full - repair): sev1 {rd1:+.2f} CI{ci(boots_rd1)[0]:+.2f}..{ci(boots_rd1)[1]:+.2f} | "
          f"sev3 {rd3:+.2f} CI{ci(boots_rd3)[0]:+.2f}..{ci(boots_rd3)[1]:+.2f}", "",
          "## H2: does the advantage grow with severity (interaction)",
          f"- Logistic strat:sev coef {m.params['strat:sev']:+.3f}, p={inter_p:.4f} (Holm {adj['H2_interaction']:.4f})",
          f"- Interaction as difference of risk differences (sev3 - sev1): "
          f"{rd3-rd1:+.2f} CI{ci(boots_int)[0]:+.2f}..{ci(boots_int)[1]:+.2f}  [estimation-based backup]", "",
          "## Logistic model", "```", str(m.summary()), "```", ""]
    return "\n".join(L) + "\n"


if __name__ == "__main__":
    split = sys.argv[1] if len(sys.argv) > 1 else "pilot"
    rows = load(split)
    report = pilot_report(rows) if split == "pilot" else main_report(rows)
    (ROOT / "logs" / f"{split}_analysis.md").write_text(report)
    print(report)
