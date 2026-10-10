from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from config import settings
from models import TrendingResponse
from aggregator import build_trending_response


# In-memory cache
trending_cache: TrendingResponse | None = None
scheduler = AsyncIOScheduler()


async def refresh_trending():
    """Background job to refresh trending data."""
    global trending_cache
    try:
        trending_cache = await build_trending_response()
        print(f"Refreshed trending: {len(trending_cache.trending)} tickers, {trending_cache.total_mentions} mentions")
    except Exception as e:
        print(f"Refresh error: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await refresh_trending()  # Initial fetch
    scheduler.add_job(refresh_trending, "interval", minutes=settings.fetch_interval_minutes)
    scheduler.start()
    yield
    # Shutdown
    scheduler.shutdown()


app = FastAPI(
    title="TrendView83 API",
    description="Trending US stocks from social media sentiment",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/trending", response_model=TrendingResponse)
async def get_trending():
    """Get current trending tickers with sentiment and price data."""
    if trending_cache is None:
        await refresh_trending()
    return trending_cache


@app.get("/api/trending/{ticker}")
async def get_ticker_detail(ticker: str):
    """Get detailed data for a specific ticker."""
    if trending_cache is None:
        await refresh_trending()

    for t in trending_cache.trending:
        if t.ticker.upper() == ticker.upper():
            return t

    return {"error": "Ticker not in trending list"}


@app.post("/api/refresh")
async def manual_refresh():
    """Manually trigger a refresh."""
    await refresh_trending()
    return {"status": "refreshed", "count": len(trending_cache.trending) if trending_cache else 0}


@app.get("/health")
async def health():
    return {"status": "ok", "cached": trending_cache is not None}