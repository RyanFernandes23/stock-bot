import openai
import os
import json
import base64
import plotly
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class StockAnalystChatbot:
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        openai.api_key = self.api_key
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
        """Analyze Plotly charts using OpenAI's GPT-4 with Vision"""
        if not self.api_key:
            return "OpenAI API key not configured. Please set OPENAI_API_KEY environment variable."
        
        # Prepare the chat messages
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": user_question}
        ]
        
        # Add chart images to the message
        for chart_type, chart_json in charts.items():
            if chart_json:
                fig = plotly.io.from_json(chart_json)
                img_bytes = fig.to_image(format="png")
                img_base64 = base64.b64encode(img_bytes).decode("utf-8")
                
                messages.append({
                    "role": "user",
                    "content": [
                        {"type": "text", "text": f"Here is the {chart_type.replace('_', ' ')} chart:"},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{img_base64}"
                            }
                        }
                    ]
                })
        
        try:
            response = openai.chat.completions.create(
                model="gpt-4-turbo",
                messages=messages,
                max_tokens=1000
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Error analyzing charts: {str(e)}"
    
    def general_chat(self, user_question, context=None):
        """Handle general chat questions"""
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": user_question}
        ]
        
        if context:
            messages.insert(1, {"role": "system", "content": f"Context: {context}"})
        
        try:
            response = openai.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=messages,
                max_tokens=500
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Error in chatbot: {str(e)}"

# Initialize chatbot
chatbot = StockAnalystChatbot()