from __future__ import annotations

from hotcommerce.models import ProductCandidate


def render_market_report(product: ProductCandidate, rank: int, window: str) -> str:
    signals = product.signals
    brand = product.brand or "Unknown brand"
    return f"""## {rank}. {product.name}

- Product ID: `{product.product_id}`
- Brand: {brand}
- Category: {product.category}
- Region: {product.region}
- Window: {window}
- Hot Score: {product.score}

### Market Snapshot
{product.name} is ranking as a high-potential product candidate in {product.region}, driven by commerce rank {signals.commerce_rank or "n/a"}, search interest {signals.search_interest:.1f}, and social mentions {signals.social_mentions:.0f}.

### Demand Drivers
- Search and social demand indicate visible consumer curiosity.
- Regional fit score is {signals.regional_fit:.2f}, suggesting room for localized merchandising.
- Recent activity score is {signals.recency:.2f}, which supports near-term monitoring.

### Audience
Likely buyers are shoppers already comparing convenience, visible results, price-value, and social proof within the {product.category} category.

### Competition
Expect competition from Amazon-native brands, TikTok-driven private labels, and fast-moving sellers that can refresh creative quickly.

### Risks
- Source APIs can be delayed, rate limited, or incomplete.
- Social virality may not convert if reviews, pricing, or fulfillment are weak.
- Category-level seasonality should be checked before inventory commitments.

### Future Outlook
Near-term outlook is positive if search interest and social velocity continue rising over the next 2-4 weeks. Re-score weekly and watch for review quality, price compression, and creator content saturation.

### Recommended Actions
- Validate top keywords and regional demand before buying inventory.
- Compare marketplace price bands and review distribution.
- Generate 3-5 creative angles based on observed customer pain points.
"""
