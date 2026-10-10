import re
import praw
import httpx
from datetime import datetime, timezone
from typing import Optional
from config import settings
from models import Mention, SourceType, Sentiment


TICKER_PATTERN = re.compile(r"\b[A-Z]{1,5}\b")

# Common false positives to filter out - EXTENDED
BLACKLIST = {
    # Common English words
    "THE", "AND", "FOR", "YOU", "ARE", "BUT", "NOT", "WITH", "THIS", "THAT",
    "FROM", "HAVE", "HAS", "HAD", "WILL", "WOULD", "COULD", "SHOULD", "THAN",
    "THEN", "WHEN", "WHERE", "WHAT", "WHICH", "WHO", "WHY", "HOW", "ALL",
    "ANY", "SOME", "ONE", "TWO", "NEW", "OLD", "BIG", "SMALL", "HIGH", "LOW",
    # Financial/trading terms
    "BUY", "SELL", "HOLD", "LONG", "SHORT", "CALL", "PUT", "STOCK", "MARKET",
    "PRICE", "VOLUME", "GAIN", "LOSS", "PROFIT", "RISK", "PORTFOLIO", "TRADE",
    # Time
    "DAY", "WEEK", "MONTH", "YEAR", "TODAY", "TOMORROW", "YESTERDAY", "NOW",
    "TIME", "MONEY", "CASH", "FUND", "ETF", "INDEX", "SECTOR", "INDUSTRY",
    "COMPANY", "BUSINESS", "EARNINGS", "REVENUE", "EPS", "PE", "DIVIDEND",
    "YOY", "QOQ", "TTM", "FY", "Q1", "Q2", "Q3", "Q4", "GDP", "CPI", "PPI",
    # Regulatory/Exchanges
    "FED", "SEC", "IPO", "SPAC", "REIT", "MLP", "ADR", "OTC", "NYSE",
    "NASDAQ", "AMEX", "TSX", "LSE", "HKEX", "SSE", "SZSE", "TSE", "ASX",
    # Titles/Orgs
    "CEO", "CFO", "CTO", "COO", "IRS", "FDA", "DOJ", "FTC", "CFPB", "OCC",
    # Tech/Crypto
    "AI", "ML", "API", "UI", "UX", "IOT", "SAAS", "PAAS", "IAAS", "CRM",
    "ERP", "HR", "IT", "DEVOPS", "CI", "CD", "KPI", "ROI", "ROE", "ROA",
    # Currencies
    "USD", "EUR", "GBP", "JPY", "CNY", "CAD", "AUD", "CHF", "INR", "BRL",
    "BTC", "ETH", "SOL", "ADA", "DOT", "AVAX", "MATIC", "LINK", "UNI",
    "DOGE", "SHIB", "XRP", "LTC", "BCH", "ETC", "XLM", "ATOM", "NEAR",
    # Common words that look like tickers (2-4 letter words)
    "TO", "IN", "OF", "A", "IS", "AS", "AT", "ON", "IT", "BY", "OR", "IF",
    "BE", "DO", "GO", "SO", "UP", "OUT", "OFF", "OVER", "UNDER", "THEN",
    "THAN", "THEY", "THEM", "THEIR", "THERE", "WHERE", "WHEN", "WHAT",
    "WHO", "WHICH", "WHY", "HOW", "CAN", "WILL", "JUST", "NOW", "GET",
    "GOT", "MADE", "MAKE", "SAID", "SAY", "SEE", "SAW", "THINK", "THOUGHT",
    "KNOW", "KNEW", "TAKE", "TOOK", "COME", "CAME", "WANT", "WANTED",
    "USE", "USED", "FIND", "FOUND", "GIVE", "GAVE", "TELL", "TOLD",
    "WORK", "WORKED", "CALL", "CALLED", "TRY", "TRIED", "ASK", "ASKED",
    "NEED", "NEEDED", "FEEL", "FELT", "BECOME", "BECAME", "LEAVE", "LEFT",
    "PUT", "PUTS", "SET", "SETS", "LET", "LETS", "RUN", "RAN", "MOVE",
    "MOVED", "LIVE", "LIVED", "BELIEVE", "BELIEVED", "BRING", "BROUGHT",
    "WRITE", "WROTE", "SIT", "SAT", "STAND", "STOOD", "LOSE", "LOST",
    "PAY", "PAID", "MEET", "MET", "INCLUDE", "INCLUDED", "CONTINUE",
    "CONTINUED", "SET", "SETS", "LEARN", "LEARNED", "CHANGE", "CHANGED",
    "LEAD", "LED", "UNDERSTAND", "UNDERSTOOD", "WATCH", "WATCHED",
    "FOLLOW", "FOLLOWED", "STOP", "STOPPED", "CREATE", "CREATED",
    "SPEAK", "SPOKE", "READ", "READ", "ALLOW", "ALLOWED", "ADD", "ADDED",
    "SPEND", "SPENT", "GROW", "GREW", "OPEN", "OPENED", "WALK", "WALKED",
    "WIN", "WON", "OFFER", "OFFERED", "REMEMBER", "REMEMBERED",
    "LOVE", "LOVED", "CONSIDER", "CONSIDERED", "APPEAR", "APPEARED",
    "BUY", "BOUGHT", "WAIT", "WAITED", "SERVE", "SERVED", "DIE", "DIED",
    "SEND", "SENT", "EXPECT", "EXPECTED", "BUILD", "BUILT", "STAY", "STAYED",
    "FALL", "FELL", "CUT", "CUT", "REACH", "REACHED", "KILL", "KILLED",
    "REMAIN", "REMAINED", "LET", "LET", "POINTS", "POINT", "POINTS",
    "DAVID", "GURA", "TELLS", "HOSTS", "SAYS", "WHILE", "ITS", "WINS",
    "TRUE", "FALSE", "YES", "NO", "OK", "OKAY", "SURE", "REAL", "FAKE",
    "GOOD", "BAD", "BEST", "WORST", "BETTER", "WORSE", "MORE", "LESS",
    "MOST", "LEAST", "VERY", "TOO", "SO", "SUCH", "OWN", "OTHER",
    "ANOTHER", "EACH", "EVERY", "ALL", "BOTH", "FEW", "MANY", "MUCH",
    "SOME", "ANY", "NONE", "ONE", "TWO", "THREE", "FOUR", "FIVE",
    "FIRST", "LAST", "NEXT", "PREVIOUS", "LATER", "EARLY", "LATE",
    "LONG", "SHORT", "HIGH", "LOW", "LARGE", "SMALL", "BIG", "LITTLE",
    "OLD", "NEW", "YOUNG", "DIFFERENT", "SAME", "RIGHT", "WRONG",
    "TRUE", "FALSE", "REAL", "FAKE", "HARD", "EASY", "SIMPLE",
    "COMPLEX", "FREE", "BUSY", "CLEAN", "DIRTY", "FULL", "EMPTY",
    "HOT", "COLD", "WARM", "COOL", "FAST", "SLOW", "QUICK", "SPEED",
    "STRONG", "WEAK", "HEAVY", "LIGHT", "DEEP", "SHALLOW", "WIDE",
    "NARROW", "THICK", "THIN", "ROUGH", "SMOOTH", "SOFT", "HARD",
    "LOUD", "QUIET", "BRIGHT", "DARK", "CLEAR", "CLOUDY", "SUNNY",
    "RAINY", "WINDY", "CALM", "STORMY", "WET", "DRY", "CLEAN", "DIRTY",
    # Two-letter common words
    "AM", "PM", "BE", "DO", "GO", "HE", "SHE", "IT", "WE",
    "US", "ME", "MY", "YOUR", "HIS", "HER", "ITS", "OUR", "THEIR",
    "NO", "NOT", "YES", "YEAH", "NAH", "OK", "HI", "BYE", "HEY",
    "OH", "AH", "UH", "UM", "ER", "WOW", "HA", "HEH", "LOL", "OMG",
    "TBH", "IMO", "IMHO", "FYI", "BTW", "ASAP", "DIY", "FAQ", "TBD",
    "ETA", "TBA", "TBC", "TBD", "AKA", "I.E.", "E.G.", "ETC", "VS",
    "MR", "MRS", "MS", "DR", "PROF", "SR", "JR", "PH.D", "M.D.",
    "B.A.", "M.A.", "PH.D", "B.S.", "M.S.", "M.B.A.", "J.D.",
    "CEO", "CFO", "CTO", "COO", "VP", "SVP", "EVP", "DIR", "MGR",
    "HR", "IT", "PR", "R&D", "QA", "QC", "UI", "UX", "API", "SDK",
    "IDE", "OS", "DB", "SQL", "NOSQL", "AWS", "GCP", "AZURE", "K8S",
    "DOCKER", "KUBERNETES", "CI/CD", "DEVOPS", "AGILE", "SCRUM",
    "KANBAN", "JIRA", "GIT", "GITHUB", "GITLAB", "BITBUCKET",
    "NPM", "YARN", "PNPM", "WEBPACK", "VITE", "ROLLUP", "ESLINT",
    "TYPESCRIPT", "JAVASCRIPT", "PYTHON", "JAVA", "GO", "RUST",
    "CSHARP", "DOTNET", "REACT", "VUE", "ANGULAR", "SVELTE",
    "NEXTJS", "NUXT", "ASTRO", "REMIX", "GATSBY", "DOCS",
    "README", "CHANGELOG", "LICENSE", "CONTRIBUTING", "CODEOWNERS",
    "ISSUE", "PR", "MERGE", "REBASE", "COMMIT", "PUSH", "PULL",
    "FETCH", "CLONE", "FORK", "BRANCH", "TAG", "RELEASE", "VERSION",
    "MAJOR", "MINOR", "PATCH", "ALPHA", "BETA", "RC", "STABLE",
    "LTS", "NIGHTLY", "CANARY", "DEV", "PROD", "STAGING", "TEST",
    "QA", "UAT", "SMOKE", "REGRESSION", "UNIT", "INTEGRATION",
    "E2E", "MOCK", "STUB", "SPY", "FIXTURE", "SETUP", "TEARDOWN",
    "BEFORE", "AFTER", "EACH", "ALL", "DESCRIBE", "IT", "EXPECT",
    "TO", "BE", "EQUAL", "TRUE", "FALSE", "NULL", "UNDEFINED",
    "THROW", "CATCH", "FINALLY", "TRY", "ASYNC", "AWAIT", "PROMISE",
    "THEN", "CATCH", "FINALLY", "MAP", "FILTER", "REDUCE", "FIND",
    "SOME", "EVERY", "INCLUDES", "INDEXOF", "PUSH", "POP", "SHIFT",
    "UNSHIFT", "SPLICE", "SLICE", "CONCAT", "JOIN", "SPLIT",
    "REPLACE", "TRIM", "TOLOWERCASE", "TOUPPERCASE", "SUBSTRING",
    "SUBSTR", "CHARAT", "CHARCODEAT", "PARSEINT", "PARSEFLOAT",
    "ISNAN", "ISFINITE", "JSON", "STRINGIFY", "PARSE", "OBJECT",
    "ARRAY", "FUNCTION", "CLASS", "EXTENDS", "IMPLEMENTS", "INTERFACE",
    "TYPE", "ENUM", "UNION", "INTERSECTION", "TYPEOF", "INSTANCEOF",
    "NEW", "THIS", "SUPER", "STATIC", "PUBLIC", "PRIVATE", "PROTECTED",
    "READONLY", "OPTIONAL", "REQUIRED", "DEFAULT", "GET", "SET",
    "CONSTRUCTOR", "DESTRUCTOR", "SUPER", "THIS", "THAT", "THESE",
    "THOSE", "HERE", "THERE", "WHERE", "WHEN", "WHY", "HOW",
    "IF", "ELSE", "ELSEIF", "SWITCH", "CASE", "DEFAULT", "BREAK",
    "CONTINUE", "RETURN", "YIELD", "THROW", "TRY", "CATCH", "FINALLY",
    "FOR", "WHILE", "DO", "FOREACH", "IN", "OF", "LET", "CONST",
    "VAR", "FUNCTION", "ARROW", "ASYNC", "AWAIT", "GENERATOR",
    "YIELD", "ITERATOR", "SYMBOL", "MAP", "SET", "WEAKMAP", "WEAKSET",
    "PROXY", "REFLECT", "PROMISE", "ASYNC", "AWAIT", "THEN", "CATCH",
    # More common words that appear as false tickers
    "AN", "ABOUT", "CHINA", "MAY", "INTO", "LINES", "ALSO", "TRUMP",
    "BANK", "YORK", "STILL", "HOME", "DOWN", "WANTS", "CHIEF",
    "LEGAL", "DEAL", "FUEL", "WAR", "KEEPS", "ABOUT", "OVER",
    "UNDER", "AGAIN", "AGAINST", "AFTER", "BEFORE", "BETWEEN",
    "DURING", "SINCE", "UNTIL", "UPON", "WITHIN", "WITHOUT",
    "THROUGH", "THROUGHOUT", "ACROSS", "BEHIND", "BELOW", "BENEATH",
    "BESIDE", "BESIDES", "BEYOND", "BUT", "EXCEPT", "LIKE", "NEAR",
    "OPPOSITE", "OUTSIDE", "PAST", "PER", "PLUS", "MINUS", "TIMES",
    "VIA", "VIS", "VERSUS", "V", "VS", "ETC", "I.E.", "E.G.",
}


def get_reddit_client() -> praw.Reddit:
    """Create a read-only Reddit client (no auth needed for public data)."""
    return praw.Reddit(
        client_id="",
        client_secret="",
        user_agent=settings.reddit_user_agent,
        check_for_async=False,
    )


def extract_tickers(text: str) -> list[str]:
    """Extract potential tickers from text, filter blacklist."""
    candidates = TICKER_PATTERN.findall(text.upper())
    # Filter: at least 2 chars, not in blacklist, not all same char, not common false positives
    filtered = []
    for c in candidates:
        if c in BLACKLIST:
            continue
        if len(c) < 2 or len(c) > 5:
            continue
        # Skip if all same character (e.g., "AAA", "BBB")
        if len(set(c)) == 1:
            continue
        # Skip common short words
        if c in {"TO", "IN", "OF", "AS", "AT", "ON", "IT", "BY", "OR", "IF", "BE", "DO", "GO", "SO", "UP", "AM", "PM", "NO", "OK", "HI", "BY", "ME", "US", "WE", "HE", "SHE", "IT", "MY", "YOUR", "HIS", "HER", "ITS", "OUR", "THEIR"}:
            continue
        filtered.append(c)
    return filtered


def analyze_sentiment(text: str) -> tuple[Sentiment, float]:
    """Simple keyword-based sentiment analysis."""
    text_lower = text.lower()

    bullish_keywords = [
        "bullish", "moon", "rocket", "buy", "long", "calls", "gains",
        "profit", "up", "rise", "surge", "rally", "breakout", "strong",
        "beat", "exceed", "upgrade", "target", "undervalued", "cheap",
        "dip", "accumulate", "bull", "green", "pump", "squeeze",
    ]
    bearish_keywords = [
        "bearish", "crash", "dump", "sell", "short", "puts", "loss",
        "down", "fall", "drop", "plunge", "correction", "weak",
        "miss", "downgrade", "overvalued", "expensive", "top",
        "bear", "red", "bagholder", "rug", "bankrupt", "dilution",
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


async def fetch_reddit_mentions() -> list[Mention]:
    """Fetch recent posts from configured subreddits and extract tickers."""
    mentions = []
    reddit = get_reddit_client()

    try:
        # Set read-only mode explicitly
        reddit.read_only = True

        for sub_name in settings.reddit_subreddits:
            subreddit = reddit.subreddit(sub_name)
            # Get hot + new posts (limit to avoid rate limits)
            for post in subreddit.hot(limit=25):
                await process_reddit_post(post, mentions)
            for post in subreddit.new(limit=15):
                await process_reddit_post(post, mentions)
    except Exception as e:
        print(f"Reddit fetch error: {e}")

    return mentions


async def process_reddit_post(post, mentions: list[Mention]):
    """Extract tickers from a Reddit post and create mentions."""
    text = f"{post.title} {post.selftext}"
    tickers = extract_tickers(text)

    if not tickers:
        return

    sentiment, confidence = analyze_sentiment(text)

    for ticker in set(tickers):  # Dedupe per post
        mention = Mention(
            ticker=ticker,
            source=SourceType.REDDIT,
            source_id=post.id,
            title=post.title[:200],
            excerpt=(post.selftext[:300] if post.selftext else "") or post.title[:300],
            sentiment=sentiment,
            confidence=confidence,
            timestamp=datetime.fromtimestamp(post.created_utc, tz=timezone.utc),
            url=f"https://reddit.com{post.permalink}",
        )
        mentions.append(mention)