import openai
import os
import json
import base64
import plotly
from dotenv import load_dotenv
from groq import Groq

# Load environment variables
load_dotenv()

class StockAnalystChatbot:
    def __init__(self):
        self.api_key = os.getenv("GROQ_API_KEY")
        
        self.client = Groq(
        api_key= self.api_key,
        )
        self.system_prompt = """
        You are a senior stock market analyst with 20 years of experience in technical analysis. 
        Your task is to help users understand stock charts and technical indicators, and provide 
        insights based on the visualizations. You specialize in interpreting:
        - Price charts with moving averages and Bollinger Bands
        - MACD (Moving Average Convergence Divergence) charts
        - RSI (Relative Strength Index) charts
        
        When analyzing charts, focus on:
        1. Identifying trends and trend reversals
        2. Spotting support and resistance levels
        3. Recognizing chart patterns (head and shoulders, triangles, etc.)
        4. Interpreting indicator crossovers and divergences
        5. Assessing overbought/oversold conditions
        6. Evaluating potential entry and exit points
        
        Provide clear, concise explanations suitable for both novice and experienced investors.
        """
    
    def analyze_charts(self, charts, user_question):
        """Analyze Plotly charts using Groq's Llama model (text-only, send chart JSON)"""
        if not self.api_key:
            return "GROQ API key not configured. Please set GROQ_API_KEY environment variable."
        
        # Prepare the chat messages 
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": user_question}
        ]
        
        # Add chart JSONs to the message
        for chart_type, chart_json in charts.items():
            if chart_json:
                messages.append({
                    "role": "user",
                    "content": f"Here is the {chart_type.replace('_', ' ')} chart in Plotly JSON format: {chart_json}"
                })
        
        try:
            response = self.client.chat.completions.create(
                messages=messages,
                model="llama3-70b-8192",
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Error analyzing charts: {str(e)}"
    
    def general_chat(self, user_question, context=None):
        """Handle general chat questions"""
        if not self.api_key:
            return "GROQ API key not configured. Please set GROQ_API_KEY environment variable."
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": user_question}
        ]
        
        if context:
            messages.insert(1, {"role": "system", "content": f"Context: {context}"})
        
        try:
            response = self.client.chat.completions.create(
            messages= messages,
            model="llama3-70b-8192",
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Error in chatbot: {str(e)}"

# Initialize chatbot
chatbot = StockAnalystChatbot()