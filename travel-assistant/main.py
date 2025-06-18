from flask import Flask, render_template, request, jsonify, session
from agents.inquiry_router_agent import InquiryRouterAgent
from agents.flight_status_agent import FlightStatusAgent
from agents.flight_analytics_agent import FlightAnalyticsAgent
import os
from dotenv import load_dotenv
import re

# Load environment variables from .env file for local development
load_dotenv()

# Initialize the Flask app
app = Flask(__name__)
# Set a secret key for session management (should be strong in production)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'default_secret_key')

# Instantiate the main router agent (handles all incoming queries)
router_agent = InquiryRouterAgent()

# Regex to extract route information (origin and destination airport codes) from user queries
ROUTE_REGEX = re.compile(r'from\s+([A-Z]{3})\s+to\s+([A-Z]{3})', re.IGNORECASE)

@app.route('/')
def home():
    """
    Render the main web interface for the Air Travel Assistant.
    """
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    """
    Handle chat POST requests: route the user query to the appropriate agent and return the response.
    Maintains conversational memory in the session for context-aware queries.
    """
    user_query = request.json['query']
    user_context = session.get('user_context', {})
    memory = session.get('memory', {})

    # Try to extract route (origin/dest) from the current query
    route_match = ROUTE_REGEX.search(user_query)
    if route_match:
        origin, dest = route_match.group(1).upper(), route_match.group(2).upper()
        memory['origin'] = origin
        memory['dest'] = dest
    # If no route in the current query, use the last known route from memory (enables follow-up queries)
    elif 'origin' in memory and 'dest' in memory:
        user_query += f" from {memory['origin']} to {memory['dest']}"

    # Track if the user is asking for analytics (for conversational memory)
    if 'analytics' in user_query.lower() or 'show me' in user_query.lower():
        memory['last_intent'] = 'analytics'
    session['memory'] = memory

    # Route the query to the correct agent based on intent (status or analytics)
    routing_result = router_agent.handle({"query": user_query})
    if routing_result["agent"] == "flight_status":
        # Status agent handles real-time flight status queries
        status_agent = FlightStatusAgent(user_context=user_context)
        response = status_agent.handle({"query": user_query})
    else:
        # Analytics agent handles historical/statistical queries
        analytics_agent = FlightAnalyticsAgent()
        response = analytics_agent.handle({"query": user_query})

    # Placeholder for future subscription/notification features (e.g., SMS/email alerts)
    if request.json.get('subscribe'):
        response['subscription'] = 'Subscription feature coming soon!'
    return jsonify(response)

if __name__ == '__main__':
    """
    Run the Flask development server for the Air Travel Assistant.
    In production, use a WSGI server like Gunicorn and set debug=False.
    """
    app.run(host='0.0.0.0', port=5050, debug=True)