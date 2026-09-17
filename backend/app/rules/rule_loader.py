"""Load the reviewed policy file without making YAML a mandatory dependency."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def default_rule_path() -> Path:
    return Path(__file__).resolve().parents[3] / "docs" / "02_RECOMMENDATION_RULES.yaml"


def load_rules(path: str | Path | None = None) -> dict[str, Any]:
    """Load policy YAML.

    The checked-in policy intentionally uses JSON, a valid YAML 1.2 subset, so
    a fresh prototype checkout works with the Python standard library. Projects
    that install PyYAML may use ordinary YAML without changing this interface.
    """
    policy_path = Path(path) if path else default_rule_path()
    text = policy_path.read_text(encoding="utf-8")
    try:
        import yaml  # type: ignore[import-not-found]
    except ImportError:
        policy = json.loads(text)
    else:
        policy = yaml.safe_load(text)
    if not isinstance(policy, dict) or not isinstance(policy.get("version"), str):
        raise ValueError("Recommendation policy must contain a string version")
    if not isinstance(policy.get("rules"), list):
        raise ValueError("Recommendation policy must contain a rules list")
    return policy
