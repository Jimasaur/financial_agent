def extract_ticker(query: str) -> str | None:
    """
    Simple heuristic to extract a stock ticker from a query.
    In a real app, this would use an LLM or a mapping database.
    """
    query = query.lower()
    
    # Common mapping
    mapping = {
        'apple': 'AAPL',
        'microsoft': 'MSFT',
        'google': 'GOOGL',
        'alphabet': 'GOOGL',
        'amazon': 'AMZN',
        'tesla': 'TSLA',
        'meta': 'META',
        'facebook': 'META',
        'nvidia': 'NVDA',
        'netflix': 'NFLX',
        'amd': 'AMD',
        'intel': 'INTC',
        'coinbase': 'COIN',
        'uber': 'UBER',
        'airbnb': 'ABNB',
        'palantir': 'PLTR',
        'snowflake': 'SNOW',
        'salesforce': 'CRM',
        'adobe': 'ADBE',
        'oracle': 'ORCL',
        'ibm': 'IBM',
        'disney': 'DIS',
        'nike': 'NKE',
        'starbucks': 'SBUX',
        'mcdonalds': 'MCD',
        'cocacola': 'KO',
        'pepsi': 'PEP',
        'walmart': 'WMT',
        'target': 'TGT',
        'costco': 'COST',
        'homedepot': 'HD',
        'lowes': 'LOW',
        'bank of america': 'BAC',
        'jpmorgan': 'JPM',
        'goldman sachs': 'GS',
        'morgan stanley': 'MS',
        'wells fargo': 'WFC',
        'citigroup': 'C',
        'visa': 'V',
        'mastercard': 'MA',
        'paypal': 'PYPL',
        'block': 'SQ',
        'square': 'SQ'
    }
    
    for name, ticker in mapping.items():
        if name in query:
            return ticker
            
    # Check for explicit tickers like $TSLA
    words = query.split()
    for word in words:
        if word.startswith('$'):
            return word[1:].upper()
            
    return None
