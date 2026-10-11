from collections import defaultdict
from datetime import datetime, timezone, timedelta
from typing import Optional
from fetchers.reddit import fetch_reddit_mentions
from fetchers.news import fetch_news_mentions
from fetchers.stocktwits import fetch_stocktwits_mentions
from fetchers.yfinance import fetch_multiple_snapshots
from models import (
    Mention, TrendingTicker, TrendingResponse,
    Sentiment, SourceType
)
from config import settings
from data.consumer_staples import is_consumer_staple, get_staples_tickers


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
    stocktwits_mentions = await fetch_stocktwits_mentions()
    all_mentions = reddit_mentions + news_mentions + stocktwits_mentions

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
            is_staple=is_consumer_staple(ticker),
        ))

    # Sort by mention count * sentiment strength
    trending.sort(key=lambda t: t.mention_count * (1 + abs(t.sentiment_score)), reverse=True)

    # Assign ranks
    for i, t in enumerate(trending):
        t.rank = i + 1

    # Fetch price snapshots for top tickers - this naturally filters invalid ones
    top_tickers = [t.ticker for t in trending[:25]]
    snapshots = await fetch_multiple_snapshots(top_tickers)

    # Also fetch staples price data (for dedicated staples view) - limit to top 20 to avoid rate limits
    staples_tickers = get_staples_tickers()
    staples_price_tickers = staples_tickers[:20]  # Only fetch prices for top 20
    print(f"Fetching price data for {len(staples_price_tickers)} staples tickers...")
    staples_snapshots = await fetch_multiple_snapshots(staples_price_tickers)
    print(f"Got {len(staples_snapshots)} staples snapshots")

    # Only keep tickers that have valid snapshots
    valid_trending = []
    for t in trending:
        if t.ticker in snapshots:
            t.snapshot = snapshots[t.ticker]
            valid_trending.append(t)
        elif len(valid_trending) < 15:  # Keep some without snapshots if we don't have enough
            valid_trending.append(t)

    # Add staples data to response (include all tickers, with prices where available)
    staples_data = []
    for ticker in staples_tickers:
        if ticker in staples_snapshots:
            snap = staples_snapshots[ticker]
            staples_data.append({
                "ticker": ticker,
                "price": snap.price,
                "change": snap.change,
                "change_percent": snap.change_percent,
                "volume": snap.volume,
                "market_cap": snap.market_cap,
            })
        else:
            # Include ticker without price data
            staples_data.append({
                "ticker": ticker,
                "price": None,
                "change": None,
                "change_percent": None,
                "volume": None,
                "market_cap": None,
            })

    return TrendingResponse(
        trending=valid_trending[:20],
        last_updated=datetime.now(timezone.utc),
        total_mentions=len(all_mentions),
        staples=staples_data,
    )