import os
import requests
from datetime import datetime, timedelta

def fetch_stock_data(symbol: str, days: int = 30) -> dict:
    """
    Fetch stock data from Alpha Vantage API.
    Returns a dictionary with labels (dates) and prices.
    """
    api_key = os.getenv('ALPHAVANTAGE_API_KEY')
    if not api_key:
        print("Warning: ALPHAVANTAGE_API_KEY not found")
        return {'error': 'API key not configured'}
        
    url = 'https://www.alphavantage.co/query'
    params = {
        'function': 'TIME_SERIES_DAILY',
        'symbol': symbol,
        'apikey': api_key,
        'outputsize': 'compact'
    }
    
    try:
        response = requests.get(url, params=params)
        data = response.json()
        
        if 'Error Message' in data:
            return {'error': data['Error Message']}
        if 'Note' in data:
             # API limit reached
            return {'error': 'API limit reached'}
            
        time_series = data.get('Time Series (Daily)', {})
        
        # Process data
        dates = []
        prices = []
        
        # Sort dates
        sorted_dates = sorted(time_series.keys())
        
        # Filter for last N days
        start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        
        for date in sorted_dates:
            if date >= start_date:
                dates.append(date)
                prices.append(float(time_series[date]['4. close']))
                
        return {
            'labels': dates,
            'prices': prices,
            'symbol': symbol
        }
        
    except Exception as e:
        print(f"Error fetching stock data: {e}")
        return {'error': str(e)}
