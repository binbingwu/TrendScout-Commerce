from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from hotcommerce.models import PipelineWindow


def load_config(path: str | Path) -> dict[str, Any]:
    with Path(path).open("r", encoding="utf-8") as config_file:
        return yaml.safe_load(config_file)


def resolve_window(config: dict[str, Any], window_name: str, top_n: int | None) -> PipelineWindow:
    windows = config.get("windows", {})
    if window_name not in windows:
        allowed = ", ".join(sorted(windows))
        raise ValueError(f"Unknown window '{window_name}'. Expected one of: {allowed}")
    window_config = windows[window_name]
    return PipelineWindow(
        name=window_name,
        days=int(window_config["days"]),
        top_n=int(top_n or window_config["default_top_n"]),
    )
