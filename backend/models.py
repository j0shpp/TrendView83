from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
from enum import Enum


class Sentiment(str, Enum):
    BULLISH = "bullish"
    BEARISH = "bearish"
    NEUTRAL = "neutral"


class SourceType(str, Enum):
    REDDIT = "reddit"
    NEWS = "news"
    STOCKTWITS = "stocktwits"


class Mention(BaseModel):
    ticker: str
    source: SourceType
    source_id: str  # Reddit post ID or news article URL
    title: str
    excerpt: str
    sentiment: Sentiment
    confidence: float = Field(ge=0.0, le=1.0)
    timestamp: datetime
    url: str


class TickerSnapshot(BaseModel):
    ticker: str
    price: float
    change: float
    change_percent: float
    volume: int
    market_cap: Optional[int] = None
    last_updated: datetime


class TrendingTicker(BaseModel):
    ticker: str
    mention_count: int
    sentiment_score: float  # -1 to 1
    sentiment: Sentiment
    mentions: list[Mention]
    snapshot: Optional[TickerSnapshot] = None
    rank: int
    is_staple: bool = False


class StapleSnapshot(BaseModel):
    ticker: str
    price: Optional[float] = None
    change: Optional[float] = None
    change_percent: Optional[float] = None
    volume: Optional[int] = None
    market_cap: Optional[int] = None


class TrendingResponse(BaseModel):
    trending: list[TrendingTicker]
    last_updated: datetime
    total_mentions: int
    staples: list[StapleSnapshot] = []