from collections import defaultdict
from datetime import datetime, timezone, timedelta
from typing import Optional
from fetchers.reddit import fetch_reddit_mentions
from fetchers.news import fetch_news_mentions
from fetchers.yfinance import fetch_multiple_snapshots
from models import (
    Mention, TrendingTicker, TrendingResponse,
    Sentiment, SourceType
)
from config import settings


def aggregate_mentions(mentions: list[Mention], max_age_hours: int = 24) -> dict[str, list[Mention]]:
    """Group mentions by ticker, filter by age."""
    cutoff = datetime.now(timezone.utc) - timedelta(hours=max_age_hours)
    grouped = defaultdict(list)

    for m in mentions:
        if m.timestamp >= cutoff:
            grouped[m.ticker].append(m)

    return grouped


def calculate_sentiment_score(mentions: list[Mention]) -> tuple[float, Sentiment]:
    """Calculate weighted sentiment score from mentions."""
    if not mentions:
        return 0.0, Sentiment.NEUTRAL

    total_weight = 0.0
    weighted_sum = 0.0

    sentiment_values = {
        Sentiment.BULLISH: 1.0,
        Sentiment.NEUTRAL: 0.0,
        Sentiment.BEARISH: -1.0,
    }

    for m in mentions:
        weight = m.confidence
        weighted_sum += sentiment_values[m.sentiment] * weight
        total_weight += weight

    score = weighted_sum / total_weight if total_weight > 0 else 0.0

    if score > 0.15:
        sentiment = Sentiment.BULLISH
    elif score < -0.15:
        sentiment = Sentiment.BEARISH
    else:
        sentiment = Sentiment.NEUTRAL

    return score, sentiment


async def build_trending_response() -> TrendingResponse:
    """Fetch all sources, aggregate, and build the trending response."""
    # Fetch mentions from all sources
    reddit_mentions = await fetch_reddit_mentions()
    news_mentions = await fetch_news_mentions()
    all_mentions = reddit_mentions + news_mentions

    # Group by ticker
    grouped = aggregate_mentions(all_mentions)

    # Build trending tickers (pre-filter by mention count)
    trending = []
    for ticker, mentions in grouped.items():
        if len(mentions) < 3:  # Minimum mentions to filter noise
            continue

        sentiment_score, sentiment = calculate_sentiment_score(mentions)

        trending.append(TrendingTicker(
            ticker=ticker,
            mention_count=len(mentions),
            sentiment_score=sentiment_score,
            sentiment=sentiment,
            mentions=sorted(mentions, key=lambda m: m.timestamp, reverse=True)[:10],
            rank=0,
        ))

    # Sort by mention count * sentiment strength
    trending.sort(key=lambda t: t.mention_count * (1 + abs(t.sentiment_score)), reverse=True)

    # Assign ranks
    for i, t in enumerate(trending):
        t.rank = i + 1

    # Fetch price snapshots for top tickers - this naturally filters invalid ones
    top_tickers = [t.ticker for t in trending[:25]]
    snapshots = await fetch_multiple_snapshots(top_tickers)

    # Only keep tickers that have valid snapshots
    valid_trending = []
    for t in trending:
        if t.ticker in snapshots:
            t.snapshot = snapshots[t.ticker]
            valid_trending.append(t)
        elif len(valid_trending) < 15:  # Keep some without snapshots if we don't have enough
            valid_trending.append(t)

    return TrendingResponse(
        trending=valid_trending[:20],
        last_updated=datetime.now(timezone.utc),
        total_mentions=len(all_mentions),
    )