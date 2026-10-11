import httpx
import re
from datetime import datetime, timezone
from typing import Optional
from config import settings
from models import Mention, SourceType, Sentiment


TICKER_PATTERN = re.compile(r"\$([A-Z]{1,5})\b")

# Headers to avoid Cloudflare challenge
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json",
    "Accept-Language": "en-US,en;q=0.9",
}


async def fetch_stocktwits_mentions() -> list[Mention]:
    """Fetch trending messages from StockTwits API (no auth required)."""
    mentions = []

    # StockTwits trending symbols endpoint
    url = "https://api.stocktwits.com/api/2/trending/symbols.json"

    async with httpx.AsyncClient(timeout=15.0, headers=HEADERS) as client:
        try:
            resp = await client.get(url)
            resp.raise_for_status()
            data = resp.json()

            for symbol_data in data.get("symbols", [])[:30]:  # Reduced limit
                symbol = symbol_data.get("symbol", "")
                if not symbol:
                    continue

                # Get messages for this symbol
                messages = await fetch_symbol_messages(client, symbol)
                mentions.extend(messages)

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 403:
                print("StockTwits API returned 403 Forbidden - Cloudflare protection active")
            else:
                print(f"StockTwits fetch HTTP error: {e.response.status_code}")
        except Exception as e:
            print(f"StockTwits fetch error: {e}")

    return mentions


async def fetch_symbol_messages(client: httpx.AsyncClient, symbol: str) -> list[Mention]:
    """Fetch recent messages for a symbol from StockTwits."""
    mentions = []
    url = f"https://api.stocktwits.com/api/2/streams/symbol/{symbol}.json"

    try:
        resp = await client.get(url, params={"limit": 30})
        resp.raise_for_status()
        data = resp.json()

        for msg in data.get("messages", []):
            text = msg.get("body", "")
            created_at = msg.get("created_at", "")
            message_id = msg.get("id", "")

            # Extract sentiment from message
            sentiment, confidence = analyze_sentiment(text)

            # Parse timestamp
            try:
                timestamp = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
            except Exception:
                timestamp = datetime.now(timezone.utc)

            mention = Mention(
                ticker=symbol,
                source=SourceType.STOCKTWITS,
                source_id=f"stocktwits_{message_id}",
                title=f"StockTwits: ${symbol}",
                excerpt=text[:300],
                sentiment=sentiment,
                confidence=confidence,
                timestamp=timestamp,
                url=f"https://stocktwits.com/symbol/{symbol}",
            )
            mentions.append(mention)

    except Exception as e:
        print(f"StockTwits error for {symbol}: {e}")

    return mentions


def analyze_sentiment(text: str) -> tuple[Sentiment, float]:
    """Simple keyword-based sentiment analysis."""
    text_lower = text.lower()

    bullish_keywords = [
        "bullish", "moon", "rocket", "buy", "long", "calls", "gains",
        "profit", "up", "rise", "surge", "rally", "breakout", "strong",
        "beat", "exceed", "upgrade", "target", "undervalued", "cheap",
        "dip", "accumulate", "bull", "green", "pump", "squeeze",
        "🚀", "📈", "💰", "💎", "🙌", "hodl", "to the moon",
    ]
    bearish_keywords = [
        "bearish", "crash", "dump", "sell", "short", "puts", "loss",
        "down", "fall", "drop", "plunge", "correction", "weak",
        "miss", "downgrade", "overvalued", "expensive", "top",
        "bear", "red", "bagholder", "rug", "bankrupt", "dilution",
        "📉", "💸", "🧻", "🚨", "bear market", "crash",
    ]

    bullish_score = sum(1 for kw in bullish_keywords if kw in text_lower)
    bearish_score = sum(1 for kw in bearish_keywords if kw in text_lower)

    if bullish_score > bearish_score:
        conf = min(0.5 + (bullish_score - bearish_score) * 0.1, 0.95)
        return Sentiment.BULLISH, conf
    elif bearish_score > bullish_score:
        conf = min(0.5 + (bearish_score - bullish_score) * 0.1, 0.95)
        return Sentiment.BEARISH, conf
    return Sentiment.NEUTRAL, 0.5