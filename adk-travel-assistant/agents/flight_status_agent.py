import requests
import os
import re
from datetime import datetime
from typing import Optional, Dict, Any
import google.generativeai as genai

class FlightStatusAgent:
    """
    Handles real-time flight status queries by connecting to the AviationStack API.
    This agent is responsible for fetching, parsing, and summarizing live flight information for a given flight number.
    """
    def __init__(self, user_context: Optional[Dict[str, Any]] = None):
        """
        Initialize the FlightStatusAgent with user context and API configuration.

        Args:
            user_context (dict, optional): Dictionary of user preferences or session data.
        """
        self.api_key = os.getenv('AVIATIONSTACK_API_KEY')
        self.base_url = "http://api.aviationstack.com/v1/flights"
        self.user_context = user_context or {}
        if not self.api_key:
            raise EnvironmentError("AVIATIONSTACK_API_KEY is not set in environment variables.")
        genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
        self.summarizer = genai.GenerativeModel('models/gemini-1.5-pro')

    def handle(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a user query for flight status and return a structured summary.

        Args:
            input_data (dict): Dictionary containing the user's query string.

        Returns:
            dict: Structured response with code, message, and summary data.
        """
        flight_number = self._extract_flight_number(input_data.get("query", ""))
        if not flight_number:
            return self._error_response(
                code="INVALID_INPUT",
                message="Please provide a valid flight number (e.g., AA123).",
                details="No valid flight number found in the query.",
                suggestion="Try entering a flight number in the format AA123."
            )
        try:
            flight_data = self._fetch_flight_data(flight_number)
            if not flight_data:
                return self._error_response(
                    code="NOT_FOUND",
                    message=f"No such flight exists for: {flight_number}.",
                    details="Flight number not found in AviationStack data.",
                    suggestion="Double-check the flight number or try a different airline/date."
                )
            raw_status = self._format_flight_status(flight_number, flight_data)
            # Summarize with Gemini
            summary_prompt = f"Summarize the following flight status for a traveler in 2-3 sentences, focusing on what matters most:\n{raw_status}"
            summary_response = self.summarizer.generate_content(summary_prompt)
            summary = summary_response.text.strip()
            return {"code": "SUCCESS", "message": "Flight status retrieved successfully.", "data": summary}
        except requests.Timeout:
            return self._error_response(
                code="TIMEOUT",
                message="The flight status service is currently slow.",
                details="Request to AviationStack timed out.",
                suggestion="Please try again in a moment."
            )
        except requests.ConnectionError:
            return self._error_response(
                code="NETWORK_ERROR",
                message="Unable to connect to the flight status service.",
                details="Network connection error.",
                suggestion="Check your internet connection and try again."
            )
        except Exception as e:
            return self._error_response(
                code="SYSTEM_ERROR",
                message="An unexpected error occurred.",
                details=str(e),
                suggestion="Please try again later or contact support if the issue persists."
            )

    def _extract_flight_number(self, query: str) -> Optional[str]:
        """
        Extract a flight number from the user's query using a regex pattern.

        Args:
            query (str): The user's query string.

        Returns:
            str or None: The extracted flight number, or None if not found.
        """
        match = re.search(r'\b([A-Z]{2}\d{1,4})\b', query.upper())
        return match.group(1) if match else None

    def _fetch_flight_data(self, flight_number: str) -> Optional[Dict[str, Any]]:
        """
        Fetch flight data from the AviationStack API for a given flight number.

        Args:
            flight_number (str): The flight number to look up.

        Returns:
            dict or None: The flight data dictionary, or None if not found.
        """
        params = {
            'access_key': self.api_key,
            'flight_iata': flight_number
        }
        response = requests.get(self.base_url, params=params, timeout=8)
        response.raise_for_status()
        data = response.json()
        if not data.get('data') or len(data['data']) == 0:
            return None
        return data['data'][0]

    def _format_time(self, timestr: Optional[str]) -> str:
        """
        Format a time string from the API into a human-readable format.

        Args:
            timestr (str or None): The time string from the API.

        Returns:
            str: Formatted time or 'N/A' if not available.
        """
        if not timestr:
            return "N/A"
        try:
            dt = datetime.fromisoformat(timestr.replace('Z', '+00:00'))
            return dt.strftime('%Y-%m-%d %H:%M UTC')
        except Exception:
            return timestr

    def _format_flight_status(self, flight_number: str, flight: Dict[str, Any]) -> str:
        """
        Build a detailed, human-readable status report for a flight.

        Args:
            flight_number (str): The flight number.
            flight (dict): The flight data dictionary.

        Returns:
            str: A formatted status report string.
        """
        airline = flight.get('airline', {}).get('name', 'Unknown Airline')
        status = flight.get('flight_status', 'Unknown').capitalize()
        dep = flight.get('departure', {})
        arr = flight.get('arrival', {})
        dep_airport = dep.get('airport', 'Unknown Departure Airport')
        dep_city = dep.get('city') or dep_airport
        dep_code = dep.get('iata', 'N/A')
        arr_airport = arr.get('airport', 'Unknown Arrival Airport')
        arr_city = arr.get('city') or arr_airport
        arr_code = arr.get('iata', 'N/A')
        sched_dep = self._format_time(dep.get('scheduled'))
        actual_dep = self._format_time(dep.get('actual'))
        sched_arr = self._format_time(arr.get('scheduled'))
        est_arr = self._format_time(arr.get('estimated'))
        gate = dep.get('gate') or 'N/A'
        terminal = dep.get('terminal') or 'N/A'
        delay = dep.get('delay')
        delay_str = f"Departure Delay: {delay} min" if delay else "On time"
        # Personalization: Add user preferred airline/airport if available
        user_airline = self.user_context.get('preferred_airline')
        user_airport = self.user_context.get('preferred_airport')
        personalization = ""
        if user_airline and user_airline.lower() in airline.lower():
            personalization += f"\n[Personalized] This is your preferred airline!"
        if user_airport and (user_airport.lower() in dep_city.lower() or user_airport.lower() in arr_city.lower()):
            personalization += f"\n[Personalized] This route includes your preferred airport!"
        lines = [
            f"Flight Status Report for {flight_number} ({airline})",
            f"Status: {status}",
            f"Route: {dep_city} ({dep_code}) → {arr_city} ({arr_code})",
            f"Scheduled Departure: {sched_dep} | Actual Departure: {actual_dep}",
            f"Scheduled Arrival: {sched_arr} | Estimated Arrival: {est_arr}",
            f"Terminal: {terminal} | Gate: {gate}",
            f"{delay_str}"
        ]
        if personalization:
            lines.append(personalization)
        return "\n".join(lines)

    def _error_response(self, code: str, message: str, details: str, suggestion: str) -> Dict[str, Any]:
        """
        Build a structured error response for the user or frontend.

        Args:
            code (str): Error code.
            message (str): User-facing error message.
            details (str): Technical details for debugging.
            suggestion (str): Suggestion for the user.

        Returns:
            dict: Structured error response.
        """
        return {
            "code": code,
            "message": message,
            "details": details,
            "suggestion": suggestion
        } 