from __future__ import annotations

from collections import defaultdict
from dataclasses import asdict
from math import log1p

from hotcommerce.models import ProductCandidate, ProductSignals


DEFAULT_WEIGHTS = {
    "commerce_rank_score": 0.30,
    "search_trend_score": 0.25,
    "social_velocity_score": 0.20,
    "sentiment_score": 0.10,
    "regional_fit_score": 0.10,
    "recency_score": 0.05,
}


def merge_candidates(candidates: list[ProductCandidate]) -> list[ProductCandidate]:
    grouped: dict[str, list[ProductCandidate]] = defaultdict(list)
    for candidate in candidates:
        grouped[candidate.product_id].append(candidate)

    merged: list[ProductCandidate] = []
    for product_id, items in grouped.items():
        base = items[0]
        signals = ProductSignals(
            commerce_rank=min(
                (item.signals.commerce_rank for item in items if item.signals.commerce_rank),
                default=None,
            ),
            search_interest=max(item.signals.search_interest for item in items),
            social_mentions=sum(item.signals.social_mentions for item in items),
            social_velocity=max(item.signals.social_velocity for item in items),
            sentiment=_average([item.signals.sentiment for item in items if item.signals.sentiment]),
            regional_fit=max(item.signals.regional_fit for item in items),
            recency=max(item.signals.recency for item in items),
        )
        source_urls = sorted({url for item in items for url in item.source_urls})
        merged.append(
            ProductCandidate(
                product_id=product_id,
                name=base.name,
                brand=base.brand or next((item.brand for item in items if item.brand), None),
                category=base.category,
                region=base.region,
                source_urls=source_urls,
                signals=signals,
            )
        )
    return merged


def rank_products(
    products: list[ProductCandidate],
    weights: dict[str, float] | None = None,
) -> list[ProductCandidate]:
    weights = weights or DEFAULT_WEIGHTS
    max_mentions = max((product.signals.social_mentions for product in products), default=1.0)
    max_mentions = max(max_mentions, 1.0)

    for product in products:
        s = product.signals
        commerce_rank_score = 0.0 if s.commerce_rank is None else 1 / (1 + (s.commerce_rank - 1) / 20)
        search_trend_score = _clamp(s.search_interest / 100)
        social_volume_score = log1p(s.social_mentions) / log1p(max_mentions)
        social_velocity_score = _clamp((social_volume_score * 0.45) + (s.social_velocity / 2 * 0.55))
        sentiment_score = _clamp((s.sentiment + 1) / 2)

        product.score = round(
            100
            * (
                weights["commerce_rank_score"] * commerce_rank_score
                + weights["search_trend_score"] * search_trend_score
                + weights["social_velocity_score"] * social_velocity_score
                + weights["sentiment_score"] * sentiment_score
                + weights["regional_fit_score"] * _clamp(s.regional_fit)
                + weights["recency_score"] * _clamp(s.recency)
            ),
            2,
        )

    return sorted(products, key=lambda product: product.score, reverse=True)


def product_to_dict(product: ProductCandidate) -> dict:
    payload = asdict(product)
    payload["observed_at"] = product.observed_at.isoformat()
    return payload


def _average(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def _clamp(value: float, minimum: float = 0.0, maximum: float = 1.0) -> float:
    return max(minimum, min(maximum, value))
