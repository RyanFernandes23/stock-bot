import streamlit as st
from auth import auth_guard, logout
from db import db
from analysis import fetch_stock_data, calculate_technical_indicators, generate_signals, plot_technical_chart
from reports import report_history_section, display_report
from chatbot import chatbot  # Import the chatbot
import json
import os
import pandas as pd
import numpy as np

# Initialize session state
if 'authenticated' not in st.session_state:
    st.session_state['authenticated'] = False
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'current_analysis' not in st.session_state:
    st.session_state.current_analysis = None

# Page configuration
st.set_page_config(
    page_title="Stock Analyst AI",
    page_icon="📈",
    layout="wide"
)

# Authentication guard
auth_guard()

# Main application
st.title(f"📈 Stock Analyst Portal - {st.session_state['role'].capitalize()} View")
st.sidebar.title(f"Welcome, {st.session_state['username']}")

# Logout button
if st.sidebar.button("Logout"):
    logout()
    st.rerun()

# Chatbot UI - Always visible in sidebar
st.sidebar.divider()
st.sidebar.subheader("AI Analyst Assistant")

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat messages
for message in st.session_state.messages:
    with st.sidebar.chat_message(message["role"]):
        st.sidebar.markdown(message["content"])

# Chat input
if prompt := st.sidebar.chat_input("Ask about the analysis..."):
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # Display user message
    with st.sidebar.chat_message("user"):
        st.sidebar.markdown(prompt)
    
    # Prepare context for the chatbot
    context = None
    if st.session_state.current_analysis:
        context = f"Current stock analysis for {st.session_state.current_analysis['ticker']}:\n"
        context += f"Action: {st.session_state.current_analysis['action']}\n"
        context += f"Allocation: {st.session_state.current_analysis['allocation']}%\n"
        context += f"Summary: {st.session_state.current_analysis['summary']}"
    
    # Get chatbot response
    with st.sidebar.chat_message("assistant"):
        message_placeholder = st.sidebar.empty()
        full_response = ""
        
        # Check if user is asking about charts
        if "chart" in prompt.lower() or "graph" in prompt.lower() or "visual" in prompt.lower():
            if st.session_state.current_analysis and st.session_state.current_analysis.get('charts'):
                # Use GPT-4 Vision to analyze the charts
                analysis = chatbot.analyze_charts(
                    st.session_state.current_analysis['charts'], 
                    prompt
                )
                full_response = analysis
            else:
                full_response = "No charts available for analysis. Please generate a stock analysis first."
        else:
            # Use regular chat for other questions
            full_response = chatbot.general_chat(prompt, context)
        
        message_placeholder.markdown(full_response)
    
    # Add assistant response to chat history
    st.session_state.messages.append({"role": "assistant", "content": full_response})

# Analyst View
if st.session_state['role'] == 'analyst':
    st.sidebar.subheader("Analyst Actions")
    
    # Get assigned investors
    investors = db.get_investors_for_analyst(st.session_state['username'])
    if not investors:
        st.info("No investors assigned to you.")
        st.stop()
    
    selected_investor = st.sidebar.selectbox("Select Investor", investors)
    
    if selected_investor:
        st.subheader(f"Analysis for {selected_investor}")
        
        # Stock analysis form
        with st.form("stock_analysis"):
            col1, col2 = st.columns([2, 3])
            with col1:
                ticker = st.text_input("Stock Ticker", "AAPL").upper()
            with col2:
                st.markdown("<small>Select at least 6 months for full analysis</small>", unsafe_allow_html=True)
                period = st.selectbox("Analysis Period", ['1mo', '3mo', '6mo', '1y', '2y'], index=3)  # Default to 1y
            
            submitted = st.form_submit_button("Analyze Stock")
            
            if submitted:
                with st.spinner("Analyzing stock..."):
                    try:
                        # Fetch and process data
                        data = fetch_stock_data(ticker, period)
                        if data.empty:
                            st.error("No data found for this ticker. Please try a different stock symbol.")
                        else:
                            processed_data = calculate_technical_indicators(data)
                            
                            # Check if we have enough data for indicators
                            if processed_data.empty:
                                st.warning(f"Not enough data to calculate all indicators. Got {len(data)} data points.")
                            else:
                                action, allocation = generate_signals(processed_data)
                                
                                # Generate charts
                                price_fig, macd_fig, rsi_fig = plot_technical_chart(processed_data, ticker)
                                
                                # Get RSI value safely
                                rsi_value = processed_data.iloc[-1].get('RSI', np.nan)
                                rsi_display = f"{rsi_value:.2f}" if not pd.isna(rsi_value) else "N/A"
                                
                                # Prepare report
                                analysis_data = {
                                    'price_chart': price_fig.to_json(),
                                    'macd_chart': macd_fig.to_json(),
                                    'rsi_chart': rsi_fig.to_json(),
                                    'summary': f"""
                                        **Technical Analysis Summary:**
                                        - Trend: {'Bullish' if 'Bullish' in action else 'Bearish' if 'Bearish' in action else 'Neutral'}
                                        - MACD: {'Bullish' if 'Buy' in action else 'Bearish' if 'Sell' in action else 'Neutral'}
                                        - RSI: {rsi_display}
                                    """
                                }
                                
                                # Save report
                                report_id = db.save_report(
                                    analyst=st.session_state['username'],
                                    investor=selected_investor,
                                    stock=ticker,
                                    analysis=analysis_data,
                                    action=action,
                                    allocation=allocation
                                )
                                
                                # Store current analysis in session state for chatbot
                                st.session_state.current_analysis = {
                                    'ticker': ticker,
                                    'action': action,
                                    'allocation': allocation * 100,
                                    'summary': analysis_data['summary'],
                                    'charts': {
                                        'price_chart': price_fig.to_json(),
                                        'macd_chart': macd_fig.to_json(),
                                        'rsi_chart': rsi_fig.to_json()
                                    }
                                }
                                
                                st.success("Analysis completed! Report saved.")
                                
                                # Display results
                                st.subheader(f"Analysis for {ticker}")
                                st.plotly_chart(price_fig, use_container_width=True)
                                
                                col1, col2 = st.columns(2)
                                with col1:
                                    st.plotly_chart(macd_fig, use_container_width=True)
                                with col2:
                                    st.plotly_chart(rsi_fig, use_container_width=True)
                                
                                col1, col2 = st.columns(2)
                                col1.metric("Recommended Action", action)
                                col2.metric("Portfolio Allocation", f"{allocation * 100:.2f}%")
                                
                                st.markdown("**Technical Analysis Summary:**")
                                st.markdown(analysis_data['summary'])
                                
                                # Suggest questions for the chatbot
                                st.info("Ask the AI Analyst in the sidebar about this analysis. Try questions like:")
                                st.markdown("- Explain the MACD crossover in this chart")
                                st.markdown("- What does the RSI indicate about this stock?")
                                st.markdown("- Why was a BUY recommendation given?")
                    except Exception as e:
                        st.error(f"Error analyzing stock: {str(e)}")
        
        # Report history section
        st.divider()
        st.subheader(f"Historical Reports for {selected_investor}")
        investor_reports = db.get_reports(selected_investor)
        
        if investor_reports:
            report_titles = [f"{r['stock']} - {r['date']}" for r in investor_reports]
            selected_report = st.selectbox("Select Report", report_titles, key="investor_report")
            
            if selected_report:
                report_index = report_titles.index(selected_report)
                report = investor_reports[report_index]
                display_report(report)
                
                # Set current analysis for chatbot
                try:
                    analysis = json.loads(report['analysis'])
                    st.session_state.current_analysis = {
                        'ticker': report['stock'],
                        'action': report['action'],
                        'allocation': float(report['allocation']) * 100,
                        'summary': analysis['summary'],
                        'charts': {
                            'price_chart': analysis.get('price_chart', ''),
                            'macd_chart': analysis.get('macd_chart', ''),
                            'rsi_chart': analysis.get('rsi_chart', '')
                        }
                    }
                    
                    st.info(f"Now viewing {report['stock']} report from {report['date']}. " 
                            "You can ask about this report in the AI Analyst sidebar.")
                except:
                    st.warning("Could not load report data for chatbot context")
        else:
            st.info("No reports available for this investor")

# Investor View
elif st.session_state['role'] == 'investor':
    st.subheader("Your Portfolio Analysis")
    report_history_section()
    
    # Set current analysis when viewing a report
    if "selected_report" in st.session_state:
        report = st.session_state.selected_report
        try:
            analysis = json.loads(report['analysis'])
            st.session_state.current_analysis = {
                'ticker': report['stock'],
                'action': report['action'],
                'allocation': float(report['allocation']) * 100,
                'summary': analysis['summary'],
                'charts': {
                    'price_chart': analysis.get('price_chart', ''),
                    'macd_chart': analysis.get('macd_chart', ''),
                    'rsi_chart': analysis.get('rsi_chart', '')
                }
            }
        except:
            pass

# Admin initialization (run once)
if os.environ.get('INIT_DB') == 'true':
    db.create_user('analyst1', 'analystpass', 'analyst')
    db.create_user('investor1', 'investorpass', 'investor', 'analyst1')
    db.create_user('investor2', 'investorpass', 'investor', 'analyst1')
    st.success("Initialized sample users")