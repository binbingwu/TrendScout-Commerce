from __future__ import annotations

from abc import ABC, abstractmethod
from hashlib import sha1
from random import Random
from typing import Iterable

from hotcommerce.models import PipelineWindow, ProductCandidate, ProductSignals


class SourceAdapter(ABC):
    name: str

    @abstractmethod
    def fetch(self, *, region: str, window: PipelineWindow) -> Iterable[ProductCandidate]:
        """Return product candidates with source-specific signals."""


class MockCommerceAdapter(SourceAdapter):
    name = "amazon"

    def fetch(self, *, region: str, window: PipelineWindow) -> Iterable[ProductCandidate]:
        names = [
            ("Portable Ice Maker", "home", "FrostPeak"),
            ("Red Light Therapy Mask", "beauty", "GlowLab"),
            ("Mini Projector", "electronics", "Beamly"),
            ("Walking Pad", "fitness", "StrideCo"),
            ("Cordless Spin Scrubber", "home", "CleanArc"),
            ("Silicone Air Fryer Liners", "kitchen", "CrispEase"),
            ("Pet Grooming Vacuum", "pet", "PawNova"),
            ("Magnetic Power Bank", "electronics", "VoltDock"),
        ]
        for rank, (name, category, brand) in enumerate(names, start=1):
            yield ProductCandidate(
                product_id=stable_id(name, region),
                name=name,
                brand=brand,
                category=category,
                region=region,
                source_urls=[f"https://amazon.example/{stable_id(name, region)}"],
                signals=ProductSignals(commerce_rank=rank, regional_fit=0.55 + rank / 25),
            )


class MockTrendAdapter(SourceAdapter):
    name = "google_trends"

    def fetch(self, *, region: str, window: PipelineWindow) -> Iterable[ProductCandidate]:
        products = [
            ("Red Light Therapy Mask", "beauty"),
            ("Walking Pad", "fitness"),
            ("Portable Ice Maker", "home"),
            ("Mini Projector", "electronics"),
            ("Travel Steam Iron", "home"),
        ]
        random = Random(f"{region}:{window.name}:trends")
        for name, category in products:
            yield ProductCandidate(
                product_id=stable_id(name, region),
                name=name,
                category=category,
                region=region,
                signals=ProductSignals(
                    search_interest=random.uniform(45, 100),
                    regional_fit=random.uniform(0.45, 0.95),
                    recency=random.uniform(0.4, 1.0),
                ),
            )


class MockSocialAdapter(SourceAdapter):
    def __init__(self, name: str) -> None:
        self.name = name

    def fetch(self, *, region: str, window: PipelineWindow) -> Iterable[ProductCandidate]:
        products = [
            ("Cordless Spin Scrubber", "home"),
            ("Red Light Therapy Mask", "beauty"),
            ("Magnetic Power Bank", "electronics"),
            ("Pet Grooming Vacuum", "pet"),
            ("Mini Projector", "electronics"),
        ]
        random = Random(f"{region}:{window.name}:{self.name}")
        for name, category in products:
            yield ProductCandidate(
                product_id=stable_id(name, region),
                name=name,
                category=category,
                region=region,
                source_urls=[f"https://{self.name}.example/search?q={name.replace(' ', '+')}"],
                signals=ProductSignals(
                    social_mentions=random.randint(100, 5000),
                    social_velocity=random.uniform(0.2, 1.8),
                    sentiment=random.uniform(0.0, 0.8),
                    recency=random.uniform(0.5, 1.0),
                ),
            )


def build_adapters(config: dict) -> list[SourceAdapter]:
    adapters: list[SourceAdapter] = []
    sources = config.get("sources", {})
    if sources.get("amazon", {}).get("enabled"):
        adapters.append(MockCommerceAdapter())
    if sources.get("google_trends", {}).get("enabled"):
        adapters.append(MockTrendAdapter())
    if sources.get("reddit", {}).get("enabled"):
        adapters.append(MockSocialAdapter("reddit"))
    if sources.get("tiktok", {}).get("enabled"):
        adapters.append(MockSocialAdapter("tiktok"))
    return adapters


def stable_id(name: str, region: str) -> str:
    return sha1(f"{region}:{name}".lower().encode("utf-8")).hexdigest()[:16]
