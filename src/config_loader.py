"""Load YAML config for personas, scenarios, rules/weights."""
import yaml
from pathlib import Path

CONFIG_DIR = Path(__file__).resolve().parent.parent / "config"


def load_yaml(name: str) -> dict:
    path = CONFIG_DIR / f"{name}.yaml"
    if not path.exists():
        return {}
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def get_personas() -> dict:
    return load_yaml("personas").get("personas", {})


def get_scenarios() -> dict:
    return load_yaml("scenarios")


def get_rules_weights() -> dict:
    return load_yaml("rules_weights")


def get_score_threshold() -> float:
    rw = get_rules_weights()
    return float(rw.get("score_threshold", 70))
