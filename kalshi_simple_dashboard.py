import streamlit as st
import requests
import pandas as pd
from datetime import datetime
import time
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()
API_KEY = os.getenv('KALSHI_API_KEY')

BASE_URL = "https://api.elections.kalshi.com/trade-api/v2"

class SimpleKalshiClient:
    def __init__(self):
        self.session = requests.Session()
        self.last_request = 0
    
    def safe_request(self, endpoint, params=None):
        """Rate-limited safe request"""
        try:
            # Rate limiting
            current_time = time.time()
            if current_time - self.last_request < 0.5:  # 0.5 second delay
                time.sleep(0.5 - (current_time - self.last_request))
            
            response = self.session.get(
                f"{BASE_URL}{endpoint}",
                params=params,
                timeout=30
            )
            
            if response.status_code == 429:
                st.warning("Rate limited, waiting 3 seconds...")
                time.sleep(3)
                return self.safe_request(endpoint, params)
            
            response.raise_for_status()
            self.last_request = time.time()
            return response.json()
            
        except Exception as e:
            st.error(f"API Error: {e}")
            return None
    
    def get_markets(self, limit=25):
        """Get markets"""
        params = {'limit': min(limit, 100), 'status': 'open'}
        data = self.safe_request('/markets', params)
        return data.get('markets', []) if data else []
    
    def get_orderbook(self, ticker):
        """Get orderbook"""
        data = self.safe_request(f'/markets/{ticker}/orderbook')
        return data.get('orderbook') if data else None
    
    def get_trades(self, limit=10):
        """Get recent trades"""
        params = {'limit': min(limit, 50)}
        data = self.safe_request('/markets/trades', params)
        return data.get('trades', []) if data else []

def create_simple_chart(data, chart_type="bar"):
    """Create simple charts using Streamlit native charts"""
    if not data:
        return None
    
    if chart_type == "bar":
        # Simple probability bar chart
        chart_data = pd.DataFrame({
            'Market': [d['title'][:30] + '...' for d in data[:10]],
            'Probability': [d.get('yes_price', 0) for d in data[:10]]
        })
        
        st.bar_chart(chart_data.set_index('Market')['Probability'])
        
    elif chart_type == "volume":
        # Volume chart
        chart_data = pd.DataFrame({
            'Market': [d['title'][:30] + '...' for d in data[:10]],
            'Volume': [d.get('volume', 0) for d in data[:10]]
        })
        
        st.bar_chart(chart_data.set_index('Market')['Volume'])

def main():
    """Main Streamlit app - simplified version"""
    st.set_page_config(
        page_title="Kalshi Markets",
        page_icon="🎯",
        layout="wide"
    )
    
    st.title("🎯 Kalshi Market Dashboard")
    
    # Initialize client
    client = SimpleKalshiClient()
    
    # Sidebar
    with st.sidebar:
        st.header("⚙️ Controls")
        refresh = st.button("🔄 Refresh")
        limit = st.slider("Markets to show", 5, 50, 20)
        
        if st.button("📊 Toggle View"):
            if 'view_mode' not in st.session_state:
                st.session_state.view_mode = 'cards'
            else:
                st.session_state.view_mode = 'table' if st.session_state.view_mode == 'cards' else 'cards'
    
    # Main content
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Status", "🟢 Connected" if API_KEY else "🔴 No Key")
    
    with col2:
        markets = client.get_markets(limit=limit)
        st.metric("Markets Found", len(markets))
    
    with col3:
        st.metric("Last Update", datetime.now().strftime("%H:%M:%S"))
    
    if not markets:
        st.warning("No markets found. Check connection and API key.")
        return
    
    # Charts section
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📈 Market Probabilities")
        create_simple_chart(markets, "bar")
    
    with col2:
        st.subheader("📊 Trading Volume")
        create_simple_chart(markets, "volume")
    
    # Market cards/table
    st.header("🎯 Market Details")
    
    # View mode
    view_mode = st.session_state.get('view_mode', 'cards')
    
    if view_mode == 'cards':
        # Card view
        cols_per_row = 3
        for i in range(0, len(markets), cols_per_row):
            cols = st.columns(cols_per_row)
            for j, col in enumerate(cols):
                if i + j < len(markets):
                    market = markets[i + j]
                    with col:
                        # Create a nice card
                        prob = market.get('yes_price', 0)
                        volume = market.get('volume', 0)
                        
                        # Color based on probability
                        color = "🟢" if prob >= 50 else "🔴"
                        
                        st.markdown(f"""
                        <div style="
                            border: 1px solid #ddd;
                            border-radius: 10px;
                            padding: 15px;
                            margin: 5px;
                            background-color: {'#e8f5e8' if prob >= 50 else '#ffe8e8'};
                        ">
                            <h4>{color} {market.get('title', 'Unknown')[:50]}...</h4>
                            <p><strong>YES:</strong> {prob}¢ | <strong>NO:</strong> {market.get('no_price', 0)}¢</p>
                            <p><strong>Volume:</strong> {volume:,}</p>
                            <p><strong>Probability:</strong> {prob}%</p>
                        </div>
                        """, unsafe_allow_html=True)
    else:
        # Table view
        table_data = []
        for market in markets:
            table_data.append({
                'Market': market.get('title', 'Unknown')[:60],
                'YES Price': f"{market.get('yes_price', 0)}¢",
                'NO Price': f"{market.get('no_price', 0)}¢",
                'Volume': f"{market.get('volume', 0):,}",
                'Probability': f"{market.get('yes_price', 0)}%"
            })
        
        df = pd.DataFrame(table_data)
        st.dataframe(df, use_container_width=True)
    
    # Individual market analysis
    st.header("🔍 Deep Dive")
    
    selected_market = st.selectbox(
        "Choose a market for detailed analysis:",
        options=[m.get('title', 'Unknown') for m in markets[:20]]
    )
    
    if selected_market:
        market_data = next((m for m in markets if m.get('title') == selected_market), None)
        if market_data:
            ticker = market_data.get('ticker')
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("Market Info")
                st.write(f"**Ticker:** {ticker}")
                st.write(f"**Status:** {market_data.get('status', 'Unknown')}")
                st.write(f"**YES:** {market_data.get('yes_price', 0)}¢")
                st.write(f"**NO:** {market_data.get('no_price', 0)}¢")
                st.write(f"**Volume:** {market_data.get('volume', 0):,}")
            
            with col2:
                st.subheader("Orderbook")
                orderbook = client.get_orderbook(ticker)
                if orderbook:
                    yes_bid = orderbook.get('yes_bid', 'N/A')
                    no_bid = orderbook.get('no_bid', 'N/A')
                    st.write(f"**YES Bid:** {yes_bid}¢")
                    st.write(f"**NO Bid:** {no_bid}¢")
                    
                    if 'bids' in orderbook and orderbook['bids']:
                        st.write("**Bid Levels:**")
                        for bid in orderbook['bids'][:3]:
                            st.write(f"- {bid.get('price')}¢: {bid.get('count')} contracts")
                else:
                    st.write("No orderbook data available")
    
    # Recent trades
    st.header("🔄 Recent Activity")
    trades = client.get_trades(limit=10)
    if trades:
        trade_info = []
        for trade in trades:
            trade_info.append({
                'Time': trade.get('created_time', '')[:19].replace('T', ' '),
                'Side': trade.get('taker_side', 'Unknown').upper(),
                'Price': f"{trade.get('price', 0)}¢",
                'Count': trade.get('count', 0)
            })
        
        trade_df = pd.DataFrame(trade_info)
        st.dataframe(trade_df, use_container_width=True)

if __name__ == "__main__":
    main()
