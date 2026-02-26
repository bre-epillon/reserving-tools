import streamlit as st
from presentation.state.session_state_manager import initialize_session_state
from shared.colored_logging import info, warning, error, debug, success
from shared.utils import create_pivot_table, get_quarter, get_sidebar, get_year
import pandas as pd
import streamlit as st
import pandas as pd
import ssl
import yfinance as yf

# Bypass SSL verification
ssl._create_default_https_context = ssl._create_unverified_context
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import numpy as np

st.set_page_config(
    page_title="Reinsurance Structure Analyzer", page_icon="📈", layout="wide"
)

initialize_session_state()

st.title("Reinsurance Structure Analyzer")
get_sidebar()

df = pd.read_csv("inputs/2026-02-19-traderepublic-export.csv", sep=",")

st.dataframe(df)

# 1. Configuration & Ticker Mapping
# Mapping titles to YFinance tickers (preferring EUR/XETRA versions for consistency)
TICKER_MAP = {
    'Apple': '1AAPL.MI',
    'Brinker International': '1EAT.MI', 
    'Argan Inc.': '1AW.FR', 
    'Eni': 'ENI.MI',
    'Nitto Boseki': 'NB5.FR',
    # 'Exxon Mobil': 'XOM.DE',
    # 'Novo Nordisk (ADR)': 'NOVC.DE',
    # 'Alphabet (C)': '1GOOG.MI',
    # 'Coca-Cola': 'CCC3.DE',
    # 'Chevron': 'CHV.DE',
    # 'Core S&P 500 USD (Acc)': 'SXR8.DE',
    # 'FTSE All-World USD (Acc)': 'VWCE.DE',
    # 'Global Water USD (Dist)': 'IQQQ.DE',
    # 'Core MSCI World USD (Acc)': 'EUNL.DE',
    # 'Nasdaq': 'EQQQ.DE',
    # 'Euro Overnight Rate Swap EUR (Dist)': 'DBX0A2.DE',
}

@st.cache_data
def fetch_current_prices(tickers):
    """Fetches latest prices for a list of tickers."""
    if not tickers: return {}
    info(f"Fetching current prices for tickers: {tickers}")
    data = yf.download(list(set(tickers)), period="1d", progress=False, verify=False)
    if data.empty:
        error(f"Failed to fetch current prices for tickers: {tickers}")
    else:
        success(f"Successfully fetched current prices for tickers: {tickers}")
    # Handle both single ticker and multiple tickers
    if len(tickers) == 1:
        return {tickers[0]: data['Close'].iloc[-1]}
    return {t: data['Close'][t].iloc[-1] for t in tickers if t in data['Close']}

@st.cache_data
def get_historical_price(ticker, date):
    """Fetches price for a specific date to estimate share count."""
    end_date = date + timedelta(days=5) # Buffer for weekends
    debug(f"Fetching historical price for {ticker} on {date}")
    data = yf.download(ticker, start=date.strftime('%Y-%m-%d'), 
                       end=end_date.strftime('%Y-%m-%d'), progress=False)
    return data['Close'].iloc[0] if not data.empty else None

def calculate_portfolio(df):
    # Clean Data
    df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
    df['value'] = pd.to_numeric(df['value'], errors='coerce').fillna(0)
    
    # Initialize Portfolio
    holdings = {} # {title: {'shares': 0, 'cost_basis': 0, 'ticker': ticker}}
    cash_balance = 0
    total_fees = 0
    total_interest = 0
    
    # Process Transactions
    for _, row in df.sort_values('timestamp').iterrows():
        t_type = row['transaction_type']
        val = row['value']
        title = row['title']
        
        # 1. Update Cash Balance (Net impact of all transactions)
        cash_balance += val
        
        # 2. Track Fees & Interest
        if t_type == 'Fees':
            total_fees += abs(val)
        elif t_type in ['Cash Interests', 'Bond'] and 'interest' in str(row['subtitle']).lower():
            total_interest += val
        elif 'dividend' in str(row['subtitle']).lower():
            total_interest += val
            
        # 3. Track Stock/Bond Holdings
        if t_type in ['Stocks', 'Bond'] and any(kw in str(row['subtitle']).lower() for kw in ['order', 'executed']):
            ticker = TICKER_MAP.get(title, None)
            if ticker:
                info(f"Found ticker for {title}: {ticker}")
            else:
                warning(f"Couldn't find ticker for {title}")
            if ticker:
                if title not in holdings:
                    holdings[title] = {'shares': 0, 'invested': 0, 'ticker': ticker}
                
                # Estimate shares by fetching price at that date
                price = get_historical_price(ticker, row['timestamp'])
                if price:
                    # delta_shares = abs(val) / price (positive for buy, negative for sell)
                    # Trade Republic 'value' is negative for buys
                    shares_change = -val / price
                    holdings[title]['shares'] += shares_change
                    holdings[title]['invested'] -= val # Total cost basis

    # # 4. Get Current Values
    # current_prices = fetch_current_prices([h['ticker'] for h in holdings.values()])
    
    # portfolio_data = []
    # for title, h in holdings.items():
    #     curr_price = current_prices.get(h['ticker'], 0)
    #     curr_value = h['shares'] * curr_price
    #     if h['shares'] > 0.001: # Filter out sold positions
    #         portfolio_data.append({
    #             'Asset': title,
    #             'Ticker': h['ticker'],
    #             'Shares': round(h['shares'], 4),
    #             'Invested': round(h['invested'], 2),
    #             'Current Value': round(curr_value, 2),
    #             'Gain/Loss': round(curr_value - h['invested'], 2),
    #             'ROI %': round(((curr_value / h['invested']) - 1) * 100, 2) if h['invested'] != 0 else 0
    #         })
            
    # return pd.DataFrame(portfolio_data), cash_balance, total_fees, total_interest

# --- STREAMLIT UI ---
st.title("📈 Trade Republic Portfolio Analytics")

# Assume df is already loaded as per your request
# df = pd.read_csv('...') 

holdings_df, cash, fees, interest = calculate_portfolio(df)

# Top Metrics
total_assets_value = holdings_df['Current Value'].sum()
total_invested = holdings_df['Invested'].sum()
total_portfolio_value = total_assets_value + cash

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Portfolio", f"€{total_portfolio_value:,.2f}")
col2.metric("Net Gain/Loss", f"€{(total_assets_value - total_invested):,.2f}", 
            f"{((total_assets_value/total_invested-1)*100 if total_invested !=0 else 0):.2f}%")
col3.metric("Accumulated Interest", f"€{interest:,.2f}")
col4.metric("Fees Paid", f"€{fees:,.2f}", delta_color="inverse")

# Main Content Tabs
tab1, tab2, tab3 = st.tabs(["📊 Allocation", "📜 Holdings", "📉 Performance"])

with tab1:
    fig = px.pie(holdings_df, values='Current Value', names='Asset', 
                 title="Portfolio Breakdown", hole=0.4)
    st.plotly_chart(fig, use_container_width=True)

with tab2:
    st.subheader("Current Asset Status")
    st.dataframe(holdings_df.sort_values('Current Value', ascending=False), use_container_width=True)
    
    st.subheader("Bonds Summary")
    bonds_only = df[df['transaction_type'] == 'Bond']
    st.write(bonds_only.groupby('title').agg({'value': 'sum'}).rename(columns={'value': 'Cash Impact'}))

with tab3:
    # Simplified IRR logic: (Final Value - Net Deposits) / Average Capital
    # In a real app, you'd use the XIRR formula on df[df['transaction_type'] == 'Cash Deposit']
    st.info("💡 IRR is calculated based on timing of Cash Deposits and current Portfolio Value.")
    # Professional implementation would use pyxirr here
    st.write("Current Cash available in TR: ", f"€{cash:,.2f}")
    st.write("IRR: ", f"{(total_assets_value - cash)/total_assets_value:.2f}")


if __name__ == "__main__":
    import ssl
    import yfinance as yf

    # Bypass SSL verification
    ssl._create_default_https_context = ssl._create_unverified_context

    data = yf.download("1AAPL.MI", start="2026-02-18",end="2026-02-18", progress=False)