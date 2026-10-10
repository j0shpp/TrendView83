import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Reddit (public API - no auth needed for read-only)
    reddit_user_agent: str = "TrendView83/0.1 by u/anonymous"
    reddit_subreddits: list[str] = [
        "wallstreetbets",
        "stocks",
        "investing",
        "SecurityAnalysis",
        "ValueInvesting",
    ]

    # News RSS feeds (no API keys) - updated working URLs
    rss_feeds: list[str] = [
        "https://feeds.marketwatch.com/marketwatch/topstories",
        "https://www.bloomberg.com/feeds/markets/news.rss",
        "https://www.investing.com/rss/news_25.rss",
        "https://finance.yahoo.com/news/rssindex",
        "https://seekingalpha.com/feed.xml",
    ]

    # Scheduler
    fetch_interval_minutes: int = 5

    # CORS
    cors_origins: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()