import json, sys
from collections import Counter
split = sys.argv[1]
rows = [json.loads(l) for l in open(f"data/{split}/responses.jsonl")]
print(split, "model", rows[0]["model"], "n_requests", len(rows))
for sev in (1, 3):
    for st in ("full_replanning", "local_repair"):
        r = [x for x in rows if x["severity"] == sev and x["strategy"] == st and x["result"]]
        succ = sum(x["result"]["success"] for x in r)
        pars = sum(x["result"]["parsed"] for x in r)
        why = Counter(x["result"]["failure_reason"] for x in r if not x["result"]["success"])
        tok = sum(x["input_tokens"] + x["output_tokens"] for x in r) / max(len(r), 1)
        print(f"sev{sev} {st:16s} n={len(r)} success={succ} parsed={pars} tokens/req={tok:.0f} fails={dict(why)}")
