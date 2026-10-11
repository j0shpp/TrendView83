# Top 100 Consumer Staples tickers (NYSE + NASDAQ)
# Sectors: Food, Beverages, Household Products, Personal Care, Tobacco, Retail

CONSUMER_STAPLES_TICKERS = [
    # Food & Beverages - Large Cap
    "KO", "PEP", "MDLZ", "KHC", "GIS", "K", "CPB", "CAG", "SJM", "HRL",
    "TSN", "MKC", "LW", "FLO", "BGS", "THS", "JJSF", "BRBR", "POST",

    # Beverages
    "DEO", "STZ", "BF.A", "BF.B", "SAM", "TAP", "CCEP", "MNST", "CELH", "KDP",

    # Household & Personal Care
    "PG", "CL", "CLX", "CHD", "ENR", "SPB", "EPC", "WDFC", "PBH", "MED",

    # Personal Care / Beauty
    "EL", "UL", "REV", "COTY", "INTER", "HLF", "NUS", "USANA", "BH", "EDGE",

    # Tobacco
    "MO", "PM", "BTI", "UVV", "VGR", "TURN",

    # Food Retail / Grocery
    "WMT", "COST", "KR", "ACI", "SFM", "SMPL", "VLGEA", "INGR", "UNFI", "SPTN",

    # Discount / Dollar Stores
    "DG", "DLTR", "FIVE", "BIG", "OLLI",

    # Pharmacy / Health Retail
    "CVS", "WBA", "CI", "CNC", "HUM", "ELV", "MOH",

    # Agriculture / Ingredients
    "ADM", "BG", "AGRO", "MOS", "CF", "NTR", "FMC", "CTVA", "SMG",

    # Packaging (staples-adjacent)
    "BALL", "AVY", "CCK", "SON", "IP", "PKG", "WRK", "SEE", "AMCR",

    # Additional mid-cap staples
    "HAIN", "BGFV", "UTMD", "LWAY", "FARM", "CALM",

    # International staples (ADRs on US exchanges)
    "NSRGY", "ULVR", "RMS", "LRLCY", "BASFY", "HENKY", "BEI", "CLNX", "DANOY", "RBGPF",
]

# For quick lookup
CONSUMER_STAPLES_SET = set(CONSUMER_STAPLES_TICKERS)


def is_consumer_staple(ticker: str) -> bool:
    """Check if a ticker is in the consumer staples watchlist."""
    return ticker.upper() in CONSUMER_STAPLES_SET


def get_staples_tickers() -> list[str]:
    """Get the full list of consumer staples tickers."""
    return CONSUMER_STAPLES_TICKERS.copy()