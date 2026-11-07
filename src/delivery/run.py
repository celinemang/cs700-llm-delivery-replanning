"""Run one collection: every scenario under both strategies (matched pair).

    python -m delivery.run --split pilot --n 12 --session 1 [--sessions 3]

Resumable: (scenario_id, strategy) pairs already in responses.jsonl are skipped.
Strategy order inside each pair is randomized with a seed derived from the scenario.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import random
import time
from dataclasses import asdict
from datetime import datetime, timezone

from .config import ROOT, load_config
from .llm import OllamaClient, TransportError
from .prompts import build_prompt
from .scenario import make_scenarios
from .validator import FULL, REPAIR, validate


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--split", required=True, help="pilot | main | smoke")
    ap.add_argument("--n", type=int, default=None,
                    help="scenarios per severity; for 'main' defaults to config main.planned_per_severity")
    ap.add_argument("--session", type=int, default=1)
    ap.add_argument("--sessions", type=int, default=1, help="total sessions the set is divided into")
    ap.add_argument("--base-seed", type=int, default=None)
    args = ap.parse_args(argv)

    cfg = load_config()
    base = args.base_seed if args.base_seed is not None else {
        "pilot": cfg["seeds"]["pilot_base"], "main": cfg["seeds"]["main_base"]}.get(args.split, 5_000_000)
    if args.n is not None:
        n_per = args.n
    elif args.split == "main":
        n_per = {int(k): v for k, v in cfg["main"]["planned_per_severity"].items()}
    else:
        raise SystemExit("--n is required except for --split main")
    scenarios = make_scenarios(args.split, base, n_per, cfg["environment"])
    # interleave severities (handles unequal counts), then deal round-robin to sessions
    from itertools import zip_longest
    by_sev = {s: [x for x in scenarios if x.severity == s] for s in (1, 3)}
    mixed = [x for pair in zip_longest(by_sev[1], by_sev[3]) for x in pair if x is not None]
    assert len(mixed) == len(scenarios)
    mine = [x for i, x in enumerate(mixed) if i % args.sessions == args.session - 1]

    out_dir = ROOT / "data" / args.split
    out_dir.mkdir(parents=True, exist_ok=True)
    resp_path = out_dir / "responses.jsonl"
    done = set()
    if resp_path.exists():
        for line in resp_path.read_text().splitlines():
            r = json.loads(line)
            done.add((r["scenario_id"], r["strategy"]))

    client = OllamaClient(cfg["llm"])
    info = client.model_info()
    meta_path = out_dir / "run_meta.json"
    meta = json.loads(meta_path.read_text()) if meta_path.exists() else {"runs": []}
    meta["runs"].append({"session": args.session, "started": datetime.now(timezone.utc).isoformat(),
                         "model": info, "llm_cfg": cfg["llm"], "env_cfg": cfg["environment"],
                         "base_seed": base, "n_per_severity": args.n})
    meta_path.write_text(json.dumps(meta, indent=2))
    (out_dir / "scenarios.json").write_text(json.dumps([s.to_dict() for s in scenarios]))

    for k, scn in enumerate(mine, 1):
        order = [FULL, REPAIR]
        random.Random(scn.seed * 7919 + 1).shuffle(order)
        for strategy in order:
            if (scn.scenario_id, strategy) in done:
                continue
            system, user = build_prompt(scn, strategy)
            rec = {
                "scenario_id": scn.scenario_id, "severity": scn.severity, "strategy": strategy,
                "pair_position": order.index(strategy), "session": args.session,
                "model": info["name"], "model_digest": info["digest"],
                "prompt_sha256": hashlib.sha256((system + "\n" + user).encode()).hexdigest(),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            try:
                reply = client.generate(system, user)
                res = validate(scn, strategy, reply.text)
                rec.update(raw_response=reply.text, input_tokens=reply.input_tokens,
                           output_tokens=reply.output_tokens, latency_s=round(reply.latency_s, 2),
                           done_reason=reply.done_reason, attempts=reply.attempts,
                           transport_error=None, result=asdict(res))
            except TransportError as e:
                rec.update(raw_response=None, transport_error=str(e), result=None)
            with resp_path.open("a") as f:
                f.write(json.dumps(rec) + "\n")
        print(f"[{k}/{len(mine)}] {scn.scenario_id} done", flush=True)


if __name__ == "__main__":
    main()
