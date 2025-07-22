def get_fmp_asset(prof: list) -> str:
    """
    Get asset type according to FMP available types.
    """
    types = {
        "isEtf": "ETF",
        "isAdr": "ADR",
        "isFund": "FUND",
    }

    return next((value for key, value in types.items() if prof.get(key)), "EQUITY")


def yf_to_mcal_exchange(yf_exchange: str) -> str | None:
    """
    Map yfinance exchange to pandas market calendar exchange.
    """
    YFINANCE_TO_PANDAS = {
        # Argentina
        "BUE": "XBUE",
        # Austria
        "VIE": "XWBO",
        # Australia
        "ASX": "XASX",
        # Belgium
        "BRU": "XBRU",
        # Brazil
        "SAO": "B3",
        # Canada
        "TOR": "XTSE",
        "VAN": "TSXV",
        # Switzerland
        "EBS": "SIX",
        # China
        "SHH": "XSHG",
        # Colombia
        "BVC": "XBOG",
        # Czech Republic
        "PRA": "XPRA",
        # Germany
        "DUS": "XDUS",
        "FRA": "XFRA",
        "GER": "XETR",
        "HAM": "XHAM",
        "STU": "XSWX",
        # Estonia
        "TAL": "XTAE",
        # Finland
        "HEL": "XHEL",
        # France
        "PAR": "XPAR",
        # UK
        "LSE": "XLON",
        # Hong Kong
        "HKG": "XHKG",
        # Hungary
        "BUD": "XBUD",
        # Indonesia
        "JKT": "XIDX",
        # Ireland
        "ISE": "XDUB",
        # Israel
        "TLV": "TASE",
        # India
        "BSE": "BSE",
        "NSI": "NSE",
        # Iceland
        "ICE": "ICE",
        # Italy
        "MIL": "XMIL",
        # Japan
        "JPX": "XJPX",
        # Mexico
        "MEX": "XMEX",
        # Malaysia
        "KLS": "XKLS",
        # Netherlands
        "AMS": "XAMS",
        # Norway
        "OSL": "XOSL",
        # New Zealand
        "NZE": "XNZE",
        # Philippines
        "PHS": "XPHS",
        # Portugal
        "LIS": "XLIS",
        # Saudi Arabia
        "SAU": "XSAU",
        # Sweden
        "STO": "XSTO",
        # Singapore
        "SES": "XSES",
        # Turkey
        "IST": "XIST",
        # Taiwan
        "TAI": "XTAI",
        # United States
        "NMS": "NASDAQ",
        "NYQ": "NYSE",
        # South Africa
        "JNB": "XJSE",
    }
    return YFINANCE_TO_PANDAS.get(yf_exchange)
