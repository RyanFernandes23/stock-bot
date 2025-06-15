import streamlit as st
from db import db
import json
import plotly.io

def display_report(report):
    st.subheader(f"Report for {report['stock']}")
    st.caption(f"Generated on {report['date']} by {report['analyst']}")
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Recommended Action", report['action'])
    with col2:
        st.metric("Portfolio Allocation", f"{float(report['allocation']) * 100:.2f}%")
    
    try:
        analysis = json.loads(report['analysis'])
    except:
        st.error("Failed to parse analysis data")
        return
    
    st.subheader("Technical Analysis")
    
    if 'price_chart' in analysis:
        try:
            price_fig = plotly.io.from_json(analysis['price_chart'])
            st.plotly_chart(price_fig, use_container_width=True)
        except Exception as e:
            st.error(f"Error loading price chart: {e}")
    
    if 'macd_chart' in analysis:
        try:
            macd_fig = plotly.io.from_json(analysis['macd_chart'])
            st.plotly_chart(macd_fig, use_container_width=True)
        except Exception as e:
            st.error(f"Error loading MACD chart: {e}")
    
    if 'rsi_chart' in analysis:
        try:
            rsi_fig = plotly.io.from_json(analysis['rsi_chart'])
            st.plotly_chart(rsi_fig, use_container_width=True)
        except Exception as e:
            st.error(f"Error loading RSI chart: {e}")
    
    if 'summary' in analysis:
        st.write(analysis['summary'])
    else:
        st.warning("No summary available in the report")
        
    # Store in session state for chatbot
    st.session_state.selected_report = report

def report_history_section():
    st.subheader("Historical Reports")
    reports = db.get_reports(st.session_state['username'])
    
    if not reports:
        st.info("No reports found")
        return
    
    report_titles = [f"{r['stock']} - {r['date']}" for r in reports]
    selected_report = st.selectbox("Select Report", report_titles)
    
    if selected_report:
        report_index = report_titles.index(selected_report)
        display_report(reports[report_index])