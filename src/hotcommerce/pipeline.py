from __future__ import annotations

import json
from pathlib import Path

from hotcommerce.models import PipelineWindow
from hotcommerce.reports import render_market_report
from hotcommerce.scoring import merge_candidates, product_to_dict, rank_products
from hotcommerce.sources import SourceAdapter


def run_pipeline(
    *,
    adapters: list[SourceAdapter],
    region: str,
    window: PipelineWindow,
    output_dir: str | Path,
    scoring_weights: dict[str, float],
) -> list:
    candidates = []
    for adapter in adapters:
        candidates.extend(adapter.fetch(region=region, window=window))

    products = merge_candidates(candidates)
    ranked = rank_products(products, scoring_weights)[: window.top_n]
    write_outputs(ranked, window, Path(output_dir))
    return ranked


def write_outputs(products: list, window: PipelineWindow, output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)

    products_path = output_dir / f"products_{window.name}.jsonl"
    rankings_path = output_dir / f"rankings_{window.name}.json"
    reports_path = output_dir / f"reports_{window.name}.md"

    with products_path.open("w", encoding="utf-8") as product_file:
        for product in products:
            product_file.write(json.dumps(product_to_dict(product), ensure_ascii=False) + "\n")

    rankings = [
        {
            "rank": index,
            "product_id": product.product_id,
            "name": product.name,
            "category": product.category,
            "region": product.region,
            "score": product.score,
        }
        for index, product in enumerate(products, start=1)
    ]
    rankings_path.write_text(json.dumps(rankings, indent=2, ensure_ascii=False), encoding="utf-8")

    report = "\n".join(
        render_market_report(product, rank=index, window=window.name)
        for index, product in enumerate(products, start=1)
    )
    reports_path.write_text(report, encoding="utf-8")
