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

## Headline result

Both pre-registered hypotheses were rejected. Local repair had a **higher**
success rate than full replanning (40% vs 30% overall; a +10 percentage-point
gap, McNemar p = 0.0006), and that gap did **not** grow with blockage severity
(no interaction, p = 0.82). See [logs/main_analysis.md](logs/main_analysis.md)
and [RESULTS.md](RESULTS.md).

## Repository layout

- `proposal/main.tex` - project proposal (LaTeX)
- `config.yaml` - frozen experiment parameters (map size, severities, model, sample sizes)
- `src/delivery/` - scenario generator, exact solver, prompts, LLM client, validator, runner
- `tests/` - unit tests for the generator and validator
- `analysis/` - diagnostics, calibration sweep, and the confirmatory analysis
- `data/pilot`, `data/main` - raw responses, per-scenario definitions, and run metadata
- `logs/` - deviation log, freeze record, pilot and main analysis reports
- `RESULTS.md` - plain-language summary of the findings

## Model

The planner is a local model served by [Ollama](https://ollama.com)
(`qwen2.5:14b-instruct`), so the study needs no API key and incurs no API cost.
The exact model name and digest are recorded in `data/*/run_meta.json`.

## Setup

```bash
# 1. install and start the local model server
brew install ollama
ollama serve &
ollama pull qwen2.5:14b-instruct

# 2. Python environment
python3.12 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python -m pytest
```

## Reproduce

```bash
# pilot (sample-size planning)
PYTHONPATH=src .venv/bin/python -m delivery.run --split pilot --n 12 --sessions 3 --session 1
PYTHONPATH=src .venv/bin/python analysis/analyze.py pilot

# main study (294 scenarios, 588 requests; resumable)
PYTHONPATH=src .venv/bin/python -m delivery.run --split main --sessions 3 --session 1
PYTHONPATH=src .venv/bin/python analysis/analyze.py main
```

Experiment parameters live in `config.yaml` (frozen after the pilot); every
change after freezing is recorded in `logs/deviation_log.md`.
