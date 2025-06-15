import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from ta.trend import MACD
from ta.momentum import RSIIndicator
from ta.volatility import BollingerBands
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fetch_stock_data(ticker, period='1y'):
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period=period)
        
        if hist.empty:
            logger.warning(f"No data found for ticker: {ticker}")
            return pd.DataFrame()
        
        hist.index = pd.to_datetime(hist.index)
        
        if len(hist) < 5:
            logger.warning(f"Insufficient data for {ticker}: Only {len(hist)} rows")
            return pd.DataFrame()
            
        return hist
    except Exception as e:
        logger.error(f"Error fetching data for {ticker}: {str(e)}")
        return pd.DataFrame()

def calculate_technical_indicators(data):
    if data.empty:
        return pd.DataFrame()
    
    df = data.copy()
    
    try:
        # Always calculate RSI and Bollinger Bands
        if len(df) >= 14:
            rsi = RSIIndicator(df['Close'])
            df['RSI'] = rsi.rsi()
        else:
            df['RSI'] = np.nan
            
        if len(df) >= 20:
            bb = BollingerBands(df['Close'])
            df['BB_Upper'] = bb.bollinger_hband()
            df['BB_Lower'] = bb.bollinger_lband()
        else:
            df['BB_Upper'] = np.nan
            df['BB_Lower'] = np.nan
        
        # Moving averages
        if len(df) >= 50:
            df['SMA_50'] = df['Close'].rolling(window=50).mean()
        else:
            df['SMA_50'] = np.nan
            
        if len(df) >= 200:
            df['SMA_200'] = df['Close'].rolling(window=200).mean()
        else:
            # Use longest possible moving average
            window = min(len(df), 100)
            df['SMA_Long'] = df['Close'].rolling(window=window).mean()
        
        # MACD
        if len(df) >= 26:
            macd = MACD(df['Close'])
            df['MACD'] = macd.macd()
            df['Signal_Line'] = macd.macd_signal()
        else:
            df['MACD'] = np.nan
            df['Signal_Line'] = np.nan
            
        return df.dropna()
    
    except Exception as e:
        logger.error(f"Error calculating indicators: {str(e)}")
        return pd.DataFrame()

def generate_signals(data):
    if data.empty:
        return "NO DATA", 0.0
    
    try:
        if len(data) == 0:
            return "INSUFFICIENT DATA", 0.0
            
        latest = data.iloc[-1]
        
        # Initialize signals with defaults
        trend_signal = "NEUTRAL"
        macd_signal = "NEUTRAL"
        rsi_signal = "NEUTRAL"
        
        # Trend signal
        if not pd.isna(latest.get('SMA_50', np.nan)) and not pd.isna(latest.get('SMA_200', np.nan)):
            trend_signal = "Bullish" if latest['SMA_50'] > latest['SMA_200'] else "Bearish"
        elif not pd.isna(latest.get('SMA_Long', np.nan)):
            if latest['Close'] > latest['SMA_Long']:
                trend_signal = "Bullish"
            else:
                trend_signal = "Bearish"
        
        # MACD signal
        if not pd.isna(latest.get('MACD', np.nan)) and not pd.isna(latest.get('Signal_Line', np.nan)):
            macd_signal = "Buy" if latest['MACD'] > latest['Signal_Line'] else "Sell"
        
        # RSI signal
        if not pd.isna(latest.get('RSI', np.nan)):
            if latest['RSI'] > 70:
                rsi_signal = "Overbought"
            elif latest['RSI'] < 30:
                rsi_signal = "Oversold"
        
        # Combine signals with priority logic
        if trend_signal == "Bullish" and macd_signal == "Buy" and rsi_signal == "Oversold":
            action = "STRONG BUY"
            allocation = 0.15
        elif trend_signal == "Bearish" and macd_signal == "Sell" and rsi_signal == "Overbought":
            action = "STRONG SELL"
            allocation = 0.25
        elif trend_signal == "Bullish" and macd_signal == "Buy":
            action = "BUY"
            allocation = 0.10
        elif trend_signal == "Bearish" and macd_signal == "Sell":
            action = "SELL"
            allocation = 0.15
        else:
            action = "HOLD"
            allocation = 0.0
            
        return action, allocation
    
    except Exception as e:
        logger.error(f"Error generating signals: {str(e)}")
        return "ERROR", 0.0

def plot_technical_chart(data, ticker):
    price_fig = go.Figure()
    macd_fig = go.Figure()
    rsi_fig = go.Figure()
    
    if data.empty:
        price_fig.add_annotation(text="No data available", showarrow=False, font_size=20)
        macd_fig.add_annotation(text="No data available", showarrow=False, font_size=20)
        rsi_fig.add_annotation(text="No data available", showarrow=False, font_size=20)
        return price_fig, macd_fig, rsi_fig
    
    try:
        # Price Chart
        price_fig = go.Figure()
        price_fig.add_trace(go.Scatter(x=data.index, y=data['Close'], name='Price', line=dict(color='blue')))
        
        # Add moving averages if available
        if 'SMA_50' in data and not data['SMA_50'].isnull().all():
            price_fig.add_trace(go.Scatter(
                x=data.index, 
                y=data['SMA_50'], 
                name='50-Day SMA', 
                line=dict(color='orange', dash='dash')
            ))
            
        if 'SMA_200' in data and not data['SMA_200'].isnull().all():
            price_fig.add_trace(go.Scatter(
                x=data.index, 
                y=data['SMA_200'], 
                name='200-Day SMA', 
                line=dict(color='purple', dash='dash')
            ))
        elif 'SMA_Long' in data and not data['SMA_Long'].isnull().all():
            price_fig.add_trace(go.Scatter(
                x=data.index, 
                y=data['SMA_Long'], 
                name=f'{len(data)}-Day SMA', 
                line=dict(color='green', dash='dash')
            ))
            
        # Add Bollinger Bands if available
        if 'BB_Upper' in data and not data['BB_Upper'].isnull().all() and \
           'BB_Lower' in data and not data['BB_Lower'].isnull().all():
            price_fig.add_trace(go.Scatter(
                x=data.index, 
                y=data['BB_Upper'], 
                name='Upper Band', 
                line=dict(color='rgba(255,0,0,0.3)'),
                fill=None
            ))
            price_fig.add_trace(go.Scatter(
                x=data.index, 
                y=data['BB_Lower'], 
                name='Lower Band', 
                line=dict(color='rgba(0,255,0,0.3)'),
                fill='tonexty'
            ))
        
        price_fig.update_layout(
            title=f'{ticker} Price Analysis',
            xaxis_title='Date',
            yaxis_title='Price',
            hovermode='x unified'
        )
        
        # MACD Chart
        if 'MACD' in data and not data['MACD'].isnull().all() and \
           'Signal_Line' in data and not data['Signal_Line'].isnull().all():
            macd_fig.add_trace(go.Scatter(
                x=data.index, 
                y=data['MACD'], 
                name='MACD', 
                line=dict(color='blue')
            ))
            macd_fig.add_trace(go.Scatter(
                x=data.index, 
                y=data['Signal_Line'], 
                name='Signal Line', 
                line=dict(color='orange')
            ))
            macd_fig.update_layout(title='MACD')
        
        # RSI Chart
        if 'RSI' in data and not data['RSI'].isnull().all():
            rsi_fig.add_trace(go.Scatter(
                x=data.index, 
                y=data['RSI'], 
                name='RSI', 
                line=dict(color='purple')
            ))
            rsi_fig.add_hline(y=30, line_dash="dash", line_color="green")
            rsi_fig.add_hline(y=70, line_dash="dash", line_color="red")
            rsi_fig.update_layout(
                title='RSI', 
                yaxis_range=[0,100],
                hovermode='x unified'
            )
            
        return price_fig, macd_fig, rsi_fig
    
    except Exception as e:
        logger.error(f"Error plotting charts: {str(e)}")
        return price_fig, macd_fig, rsi_fig