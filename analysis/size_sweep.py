"""Calibration sweep on DEV seeds only (8,000,000+), never pilot/main.
Finds a map size where both strategies land off the floor so the strategy
variable is measurable rather than swamped by path-tracing errors."""
import json, sys, copy
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT/"src"))
from delivery.config import load_config
from delivery.scenario import generate_scenario
from delivery.prompts import build_prompt
from delivery.llm import OllamaClient
from delivery.validator import FULL, REPAIR, validate

cfg = load_config(); client = OllamaClient(cfg["llm"])
N = int(sys.argv[1]) if len(sys.argv) > 1 else 8
print("model", client.model_info()["name"])
for nodes in (8, 10, 12):
    env = copy.deepcopy(cfg["environment"]); env["num_nodes"] = nodes
    agg = {}
    for sev in (1, 3):
        succ = {FULL: 0, REPAIR: 0}; tot = {FULL: 0, REPAIR: 0}
        for i in range(N):
            scn = generate_scenario(8_000_000 + nodes*1000 + sev*100 + i, sev, env)
            for st in (FULL, REPAIR):
                sysm, user = build_prompt(scn, st)
                r = validate(scn, st, client.generate(sysm, user).text)
                succ[st] += r.success; tot[st] += 1
        agg[sev] = {st: (succ[st], tot[st]) for st in (FULL, REPAIR)}
    line = f"nodes={nodes}: " + " | ".join(
        f"sev{sev} full {agg[sev][FULL][0]}/{agg[sev][FULL][1]} repair {agg[sev][REPAIR][0]}/{agg[sev][REPAIR][1]}"
        for sev in (1,3))
    print(line, flush=True)
