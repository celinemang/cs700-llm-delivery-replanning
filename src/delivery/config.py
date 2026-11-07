from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]


def load_config(path: Path | None = None) -> dict:
    return yaml.safe_load((path or ROOT / "config.yaml").read_text())
