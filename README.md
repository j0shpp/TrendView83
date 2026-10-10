# TrendView83

Trending US stocks discovered from social media buzz — Reddit (r/wallstreetbets, r/stocks, r/investing), financial news RSS, and real-time price data via yfinance. No API keys required.

## Stack
- **Frontend**: React + Vite + Tailwind CSS
- **Backend**: FastAPI (Python) — aggregates Reddit posts, news RSS, and stock data
- **Data**: Reddit public API (no auth), RSS feeds, yfinance for US market data

## Features
- Live trending tickers from social sentiment
- Price/volume snapshots for mentioned tickers
- Sentiment tagging (bullish/bearish/neutral)
- Auto-refresh every 5 minutes
- Click any row for detailed mentions view

## Quick Start

### Prerequisites
- Python 3.12+
- Node.js 18+
- `python3-venv` package (Ubuntu/Debian: `sudo apt install python3.12-venv`)

### Backend
```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

### Frontend (separate terminal)
```bash
cd frontend
npm install
npm run dev
```

### Or use the startup script
```bash
chmod +x start.sh
./start.sh
```

## API Endpoints
- `GET /api/trending` — List trending tickers with sentiment and price data
- `GET /api/trending/{TICKER}` — Detailed view for a specific ticker
- `POST /api/refresh` — Manually trigger data refresh
- `GET /health` — Health check

## Data Sources
- **Reddit**: r/wallstreetbets, r/stocks, r/investing, r/SecurityAnalysis, r/ValueInvesting (public API, read-only)
- **News RSS**: MarketWatch, Bloomberg, Investing.com, Yahoo Finance, Seeking Alpha
- **Prices**: yfinance (Yahoo Finance) — real-time quotes, volume, market cap

## Architecture
```
backend/
├── main.py              # FastAPI app with lifespan & scheduler
├── config.py            # Settings via pydantic-settings
├── models.py            # Pydantic models (Mention, TrendingTicker, etc.)
├── aggregator.py        # Core logic: fetch → group → sentiment → rank
└── fetchers/
    ├── reddit.py        # Reddit post fetching + ticker extraction
    ├── news.py          # RSS feed parsing + ticker extraction
    └── yfinance.py      # Price/volume data with market cap filter

frontend/
├── src/App.jsx          # Main dashboard with sortable table + detail modal
├── src/main.jsx         # React entry point
└── index.html           # HTML template
```

## Configuration
Copy `backend/.env.example` to `backend/.env` to customize:
- Subreddits to monitor
- RSS feeds
- Fetch interval
- CORS origins

## Notes
- Reddit uses read-only public API (no auth needed)
- yfinance has rate limits; price data may be delayed during high load
- Minimum 3 mentions required for a ticker to appear as "trending"
- Market cap filter ($100M+) removes noise tickers
- Sentiment is keyword-based (simple but effective for MVP)

## License
MIT