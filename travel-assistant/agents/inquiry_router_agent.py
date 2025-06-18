import google.generativeai as genai
import os
import re

class InquiryRouterAgent:
    """
    Routes user queries to the appropriate agent (status or analytics) based on intent.
    Uses a hybrid of regex and LLM-based classification for robust, flexible routing.
    """
    def __init__(self):
        """
        Initialize the InquiryRouterAgent and configure Gemini for LLM-based routing.
        """
        genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
        self.model = genai.GenerativeModel('models/gemini-1.5-pro')
    
    def handle(self, input_data):
        
        """
        Analyze the user's query and route it to the correct agent.
        Uses regex for fast detection of flight numbers, and falls back to Gemini LLM for intent classification.
        Args:
            input_data (dict): Dictionary containing the user's query string.
        Returns:
            dict: Routing result indicating which agent should handle the query.
        """
        
        query = input_data["query"]
        
        # Use regex to quickly detect flight numbers (e.g., "AA123").
        # This is fast and avoids unnecessary LLM calls for obvious status queries.
        
        if re.search(r'\b([A-Z]{2}\d{1,4})\b', query, re.IGNORECASE):
            return {"agent": "flight_status"}
        
        # If no flight number is found, use Gemini LLM to classify the query intent.
        # The LLM is only called for ambiguous or analytics-related queries.
        prompt = f"Classify query: '{query}'. Options: flight_status, flight_analytics. Respond ONLY with the category."
        response = self.model.generate_content(prompt)
        
        # The LLM should respond with either 'flight_status' or 'flight_analytics'.
        return {"agent": response.text.strip().lower()} 