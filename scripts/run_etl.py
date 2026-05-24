from __future__ import annotations

import argparse
from pathlib import Path

from hotcommerce.config import load_config, resolve_window
from hotcommerce.pipeline import run_pipeline
from hotcommerce.sources import build_adapters


def main() -> None:
    parser = argparse.ArgumentParser(description="Run hotcommerce ETL.")
    parser.add_argument("--config", default="config/sources.yaml")
    parser.add_argument("--window", choices=["month", "year"], default="month")
    parser.add_argument("--top-n", type=int, default=None)
    parser.add_argument("--region", default=None)
    args = parser.parse_args()

    config = load_config(args.config)
    window = resolve_window(config, args.window, args.top_n)
    region = args.region or config["project"]["default_region"]
    output_dir = Path(config["project"]["output_dir"])
    adapters = build_adapters(config)

    products = run_pipeline(
        adapters=adapters,
        region=region,
        window=window,
        output_dir=output_dir,
        scoring_weights=config["scoring"],
    )

    print(f"Ranked {len(products)} products for {region}/{window.name}.")
    print(f"Outputs written to {output_dir.resolve()}.")


if __name__ == "__main__":
    main()
