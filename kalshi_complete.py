#!/usr/bin/env python3
"""
Kalshi API Complete Implementation
Paste your API key in .env file and run!
"""

import requests
import os
import json
import time
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
API_KEY = os.getenv('KALSHI_API_KEY')
BASE_URL = "https://api.elections.kalshi.com/trade-api/v2"

class KalshiClient:
    def __init__(self, api_key=None):
        self.api_key = api_key
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Kalshi-Complete-Guide/1.0',
            'Accept': 'application/json'
        })
    
    def get(self, endpoint, params=None):
        """Make GET request to Kalshi API"""
        try:
            response = self.session.get(
                f"{BASE_URL}{endpoint}", 
                params=params,
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"❌ API Error: {e}")
            return None

    def get_markets(self, limit=100, status='open', series_ticker=None):
        """Get all markets with optional filtering"""
        params = {
            'limit': limit,
            'status': status
        }
        if series_ticker:
            params['series_ticker'] = series_ticker
        
        all_markets = []
        cursor = None
        
        while True:
            if cursor:
                params['cursor'] = cursor
            
            data = self.get('/markets', params)
            if not data:
                break
                
            markets = data.get('markets', [])
            all_markets.extend(markets)
            
            cursor = data.get('cursor')
            if not cursor or len(markets) < limit:
                break
        
        return all_markets
    
    def get_market(self, ticker):
        """Get single market details"""
        data = self.get(f'/markets/{ticker}')
        return data.get('market') if data else None
    
    def get_orderbook(self, ticker, depth=10):
        """Get market orderbook"""
        params = {'depth': depth}
        data = self.get(f'/markets/{ticker}/orderbook', params)
        return data.get('orderbook') if data else None
    
    def get_trades(self, ticker=None, limit=100):
        """Get recent trades"""
        params = {'limit': limit}
        if ticker:
            params['ticker'] = ticker
        
        data = self.get('/markets/trades', params)
        return data.get('trades', []) if data else []
    
    def get_series(self, ticker=None):
        """Get series information"""
        if ticker:
            data = self.get(f'/series/{ticker}')
            return data.get('series') if data else None
        else:
            data = self.get('/series')
            return data.get('series', []) if data else []

def display_welcome():
    """Display welcome message"""
    print("🎯 Kalshi API Complete Implementation")
    print("=" * 50)
    print(f"API Key: {'✅ Loaded' if API_KEY else '❌ Missing'}")
    print(f"Base URL: {BASE_URL}")
    print("=" * 50)

def run_quick_start():
    """Run the quick start example"""
    print("\n🚀 QUICK START - Fetching Markets...")
    
    client = KalshiClient()
    markets = client.get_markets(limit=5)
    
    if markets:
        print(f"✅ Found {len(markets)} markets:")
        for i, market in enumerate(markets, 1):
            print(f"\n{i}. {market['title']}")
            print(f"   Ticker: {market['ticker']}")
            print(f"   YES: {market['yes_price']}¢ | NO: {market['no_price']}¢")
            print(f"   Volume: {market['volume']:,}")
    else:
        print("❌ No markets found")

def run_market_analysis():
    """Run market analysis example"""
    print("\n📊 MARKET ANALYSIS - Deep Dive...")
    
    client = KalshiClient()
    markets = client.get_markets(limit=10)
    
    if not markets:
        print("❌ No markets available for analysis")
        return
    
    # Pick first market for detailed analysis
    market = markets[0]
    ticker = market['ticker']
    
    print(f"\nAnalyzing: {market['title']}")
    print(f"Ticker: {ticker}")
    
    # Get orderbook
    orderbook = client.get_orderbook(ticker, depth=5)
    if orderbook:
        print(f"\n📈 Orderbook:")
        print(f"YES Bid: {orderbook['yes_bid']}¢")
        print(f"NO Bid: {orderbook['no_bid']}¢")
        
        if 'bids' in orderbook:
            print("\nTop Bids:")
            for bid in orderbook['bids'][:3]:
                print(f"  {bid['price']}¢ - {bid['count']} contracts")
    
    # Get recent trades
    trades = client.get_trades(ticker, limit=10)
    if trades:
        print(f"\n💰 Recent Trades:")
        for trade in trades[:5]:
            time_str = datetime.fromisoformat(trade['created_time'].replace('Z', '+00:00')).strftime('%H:%M:%S')
            print(f"  {time_str}: {trade['taker_side'].upper()} {trade['count']} @ {trade['price']}¢")

def run_visualization():
    """Create simple visualization"""
    print("\n📈 CREATING VISUALIZATION...")
    
    client = KalshiClient()
    markets = client.get_markets(limit=15)
    
    if len(markets) < 3:
        print("❌ Not enough markets for visualization")
        return
    
    # Extract data
    titles = [m['title'][:40] + '...' if len(m['title']) > 40 else m['title'] for m in markets]
    yes_prices = [m['yes_price'] for m in markets]
    
    # Create plot
    plt.figure(figsize=(12, 8))
    plt.barh(range(len(titles)), yes_prices, color=['green' if p >= 50 else 'red' for p in yes_prices])
    plt.yticks(range(len(titles)), titles)
    plt.xlabel('YES Probability (%)')
    plt.title('Kalshi Market Probabilities')
    plt.grid(axis='x', alpha=0.3)
    
    # Add percentage labels
    for i, price in enumerate(yes_prices):
        plt.text(price + 1, i, f'{price}%', va='center')
    
    plt.tight_layout()
    plt.savefig('market_probabilities.png', dpi=150, bbox_inches='tight')
    print("✅ Visualization saved as 'market_probabilities.png'")

def run_series_explorer():
    """Explore available series"""
    print("\n🗂️  SERIES EXPLORER...")
    
    client = KalshiClient()
    series = client.get_series()
    
    if series:
        print(f"✅ Found {len(series)} series:")
        categories = {}
        
        for s in series[:10]:  # Show first 10
            cat = s.get('category', 'Unknown')
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(s['title'])
        
        for category, titles in categories.items():
            print(f"\n📁 {category}:")
            for title in titles:
                print(f"  - {title}")
    else:
        print("❌ No series found")

def main():
    """Main execution function"""
    display_welcome()
    
    if not API_KEY:
        print("\n⚠️  Please add your KALSHI_API_KEY to the .env file")
        print("Example: KALSHI_API_KEY=your_api_key_here")
        return
    
    try:
        # Run all examples
        run_quick_start()
        run_market_analysis()
        run_series_explorer()
        run_visualization()
        
        print("\n🎉 All examples completed successfully!")
        print("\nNext steps:")
        print("1. Check 'market_probabilities.png' for the visualization")
        print("2. Modify the code to explore different markets")
        print("3. Add your own analysis functions")
        print("4. Check the complete documentation for advanced features")
        
    except Exception as e:
        print(f"\n❌ Error running examples: {e}")
        print("Make sure your API key is valid and you have internet connection")

if __name__ == "__main__":
    main()
