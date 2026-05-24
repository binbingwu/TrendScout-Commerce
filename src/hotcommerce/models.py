from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass(slots=True)
class ProductSignals:
    commerce_rank: float | None = None
    search_interest: float = 0.0
    social_mentions: float = 0.0
    social_velocity: float = 0.0
    sentiment: float = 0.0
    regional_fit: float = 0.0
    recency: float = 0.0


@dataclass(slots=True)
class ProductCandidate:
    product_id: str
    name: str
    category: str
    region: str
    brand: str | None = None
    source_urls: list[str] = field(default_factory=list)
    signals: ProductSignals = field(default_factory=ProductSignals)
    score: float = 0.0
    observed_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass(frozen=True, slots=True)
class PipelineWindow:
    name: str
    days: int
    top_n: int
