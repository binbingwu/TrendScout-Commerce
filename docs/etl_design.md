# ETL Design

## 1. Extract

Each source adapter returns `ProductCandidate` records with partial signals.

- Google Trends: keyword interest, region/sub-region trend, breakout terms.
- Reddit: post/comment mentions, community spread, sentiment and pain points.
- TikTok: hashtag/video velocity, creator spread, engagement proxy.
- Amazon: rank, category, brand, price/review metadata, availability proxy.

Adapters should not decide final rankings. They only normalize source-specific facts into the common model.

## 2. Transform

The transform layer:

- Deduplicates products by normalized name plus region.
- Merges partial signals from all sources.
- Standardizes metrics onto comparable 0-1 scales.
- Preserves source URLs for auditability.

## 3. Load

Initial load target is local JSON/Markdown under `data/out`.

Production targets can be added without changing source adapters:

- PostgreSQL for ranked product history.
- Object storage for raw source snapshots.
- Vector database for source snippets and report grounding.
- API service using `specs/openapi.yaml`.

## 4. Report Generation Skill

The report generator should always produce the same sections:

1. Market Snapshot
2. Demand Drivers
3. Audience
4. Competition
5. Risks
6. Future Outlook
7. Recommended Actions

When connecting an LLM, pass only normalized signals, citations/source URLs, and a strict JSON schema. Do not let the model invent rank, region, source, price, or review facts.

## 5. Production Notes

- Keep raw source payloads for replay and debugging.
- Add API rate-limit backoff per adapter.
- Store every scoring version with rankings.
- Backtest weights by category before trusting inventory decisions.
- Treat TikTok and Reddit sentiment as directional, not ground truth.
