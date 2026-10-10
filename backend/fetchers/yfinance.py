import yfinance as yf
from datetime import datetime, timezone
from typing import Optional
from models import TickerSnapshot

# Minimum market cap in USD (e.g., $100M to filter out tiny/unknown stocks)
MIN_MARKET_CAP = 100_000_000


async def fetch_ticker_snapshot(ticker: str) -> Optional[TickerSnapshot]:
    """Fetch current price/volume data for a ticker using yfinance."""
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
        print(f"yfinance error for {ticker}: {e}")
        return None


async def fetch_multiple_snapshots(tickers: list[str]) -> dict[str, TickerSnapshot]:
    """Fetch snapshots for multiple tickers."""
    snapshots = {}
    for ticker in tickers:
        snap = await fetch_ticker_snapshot(ticker)
        if snap:
            snapshots[ticker] = snap
    return snapshots