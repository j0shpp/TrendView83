import asyncio
import yfinance as yf
from datetime import datetime, timezone
from typing import Optional
from models import TickerSnapshot

# Minimum market cap in USD (e.g., $100M to filter out tiny/unknown stocks)
MIN_MARKET_CAP = 100_000_000

# Retry configuration - more conservative
MAX_RETRIES = 1
BASE_DELAY = 5.0
BATCH_DELAY = 3.0  # Longer delay between batches


async def fetch_ticker_snapshot(ticker: str) -> Optional[TickerSnapshot]:
    """Fetch current price/volume data for a ticker using yfinance with retries."""
    for attempt in range(MAX_RETRIES):
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            hist = stock.history(period="1d", interval="1m")

            if hist.empty:
                return None

            last = hist.iloc[-1]
            prev_close = info.get("previousClose", last["Close"])
            market_cap = info.get("marketCap")

            # Filter out tiny market cap stocks
            if market_cap is not None and market_cap < MIN_MARKET_CAP:
                return None

            return TickerSnapshot(
                ticker=ticker,
                price=float(last["Close"]),
                change=float(last["Close"] - prev_close),
                change_percent=float((last["Close"] - prev_close) / prev_close * 100) if prev_close else 0.0,
                volume=int(last["Volume"]),
                market_cap=market_cap,
                last_updated=datetime.now(timezone.utc),
            )
        except Exception as e:
            if attempt < MAX_RETRIES - 1:
                delay = BASE_DELAY * (2 ** attempt)
                print(f"yfinance error for {ticker} (attempt {attempt + 1}/{MAX_RETRIES}): {e}. Retrying in {delay}s...")
                await asyncio.sleep(delay)
            else:
                print(f"yfinance error for {ticker} after {MAX_RETRIES} attempts: {e}")
                return None


async def fetch_multiple_snapshots(tickers: list[str]) -> dict[str, TickerSnapshot]:
    """Fetch snapshots for multiple tickers with concurrency limit and batching."""
    semaphore = asyncio.Semaphore(2)  # Very conservative concurrent requests
    batch_size = 3  # Very small batches

    async def fetch_with_semaphore(ticker: str):
        async with semaphore:
            return await fetch_ticker_snapshot(ticker)

    snapshots = {}
    for i in range(0, len(tickers), batch_size):
        batch = tickers[i:i + batch_size]
        results = await asyncio.gather(*[fetch_with_semaphore(t) for t in batch], return_exceptions=True)

        for ticker, result in zip(batch, results):
            if isinstance(result, TickerSnapshot):
                snapshots[ticker] = result
            elif isinstance(result, Exception):
                print(f"yfinance error for {ticker}: {result}")

        # Delay between batches to avoid rate limiting
        if i + batch_size < len(tickers):
            await asyncio.sleep(BATCH_DELAY)

    return snapshots