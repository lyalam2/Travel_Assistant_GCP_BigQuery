from google.cloud import bigquery
import google.generativeai as genai
import os
import json
from typing import Dict, List, Optional, Any

class FlightDataSchema:
    """
    Defines the schema and common query patterns for the flight data table in BigQuery.
    This class is used to provide schema context and SQL templates for analytics queries.
    """
    
    TABLE_NAME = "`ai-travel-assistant-462707.flight_data.flights`"
    
    COLUMNS = {
        'id': {'type': 'INTEGER', 'mode': 'NULLABLE', 'description': 'Unique flight identifier'},
        'year': {'type': 'INTEGER', 'mode': 'NULLABLE', 'description': 'Year of flight'},
        'month': {'type': 'INTEGER', 'mode': 'NULLABLE', 'description': 'Month of flight (1-12)'},
        'day': {'type': 'INTEGER', 'mode': 'NULLABLE', 'description': 'Day of flight (1-31)'},
        'dep_time': {'type': 'FLOAT', 'mode': 'NULLABLE', 'description': 'Actual departure time'},
        'sched_dep_time': {'type': 'INTEGER', 'mode': 'NULLABLE', 'description': 'Scheduled departure time'},
        'dep_delay': {'type': 'FLOAT', 'mode': 'NULLABLE', 'description': 'Departure delay in minutes'},
        'arr_time': {'type': 'FLOAT', 'mode': 'NULLABLE', 'description': 'Actual arrival time'},
        'sched_arr_time': {'type': 'INTEGER', 'mode': 'NULLABLE', 'description': 'Scheduled arrival time'},
        'arr_delay': {'type': 'FLOAT', 'mode': 'NULLABLE', 'description': 'Arrival delay in minutes'},
        'carrier': {'type': 'STRING', 'mode': 'NULLABLE', 'description': 'Airline carrier code'},
        'flight': {'type': 'INTEGER', 'mode': 'NULLABLE', 'description': 'Flight number'},
        'tailnum': {'type': 'STRING', 'mode': 'NULLABLE', 'description': 'Aircraft tail number'},
        'origin': {'type': 'STRING', 'mode': 'NULLABLE', 'description': 'Origin airport code'},
        'dest': {'type': 'STRING', 'mode': 'NULLABLE', 'description': 'Destination airport code'},
        'air_time': {'type': 'FLOAT', 'mode': 'NULLABLE', 'description': 'Flight time in minutes'},
        'distance': {'type': 'INTEGER', 'mode': 'NULLABLE', 'description': 'Distance in miles'},
        'hour': {'type': 'INTEGER', 'mode': 'NULLABLE', 'description': 'Hour of flight (0-23)'},
        'minute': {'type': 'INTEGER', 'mode': 'NULLABLE', 'description': 'Minute of flight (0-59)'},
        'time_hour': {'type': 'TIMESTAMP', 'mode': 'NULLABLE', 'description': 'Timestamp of flight'},
        'name': {'type': 'STRING', 'mode': 'NULLABLE', 'description': 'Airline name'}
    }
    
    # Common query patterns
    QUERY_PATTERNS = {
        'on_time_airlines': """
            SELECT
                carrier,
                name as airline_name,
                COUNT(*) as total_flights,
                AVG(COALESCE(dep_delay, 0)) as avg_dep_delay,
                AVG(COALESCE(arr_delay, 0)) as avg_arr_delay,
                AVG((COALESCE(dep_delay, 0) + COALESCE(arr_delay, 0)) / 2) as avg_overall_delay,
                SUM(CASE WHEN COALESCE(arr_delay, 0) <= 15 THEN 1 ELSE 0 END) / COUNT(*) * 100 as on_time_percentage
            FROM {table}
            WHERE origin = @origin
                AND dest = @destination
                AND carrier IS NOT NULL
                AND name IS NOT NULL
            GROUP BY carrier, name
            HAVING COUNT(*) >= 10
            ORDER BY avg_overall_delay ASC, on_time_percentage DESC
            LIMIT @limit
        """,
        
        'day_of_week_delays': """
            SELECT
                EXTRACT(DAYOFWEEK FROM DATE(year, month, day)) as day_of_week,
                COUNT(*) as total_flights,
                AVG(COALESCE(dep_delay, 0)) as avg_dep_delay,
                AVG(COALESCE(arr_delay, 0)) as avg_arr_delay,
                AVG((COALESCE(dep_delay, 0) + COALESCE(arr_delay, 0)) / 2) as avg_overall_delay,
                SUM(CASE WHEN COALESCE(arr_delay, 0) <= 15 THEN 1 ELSE 0 END) / COUNT(*) * 100 as on_time_percentage
            FROM {table}
            WHERE origin = @origin
                AND dest = @destination
                AND year IS NOT NULL
                AND month IS NOT NULL
                AND day IS NOT NULL
            GROUP BY day_of_week
            HAVING COUNT(*) >= 5
            ORDER BY avg_overall_delay ASC
        """
    }
    
    # Common parameter types
    PARAMETER_TYPES = {
        'origin': 'STRING',
        'destination': 'STRING',
        'year': 'INT64',
        'limit': 'INT64'
    }
    
    @classmethod
    def get_schema_prompt(cls) -> str:
        """
        Generate a schema prompt string for Gemini, including table schema and query patterns.
        Returns:
            str: The formatted schema prompt.
        """
        schema_lines = []
        for col, info in cls.COLUMNS.items():
            schema_lines.append(f"{col} {info['mode']} {info['type']} - {info['description']}")
        
        return f"""
        Table: {cls.TABLE_NAME}
        Schema:
        {chr(10).join(schema_lines)}
        
        Common Query Patterns:
        {json.dumps(cls.QUERY_PATTERNS, indent=2)}
        
        Parameter Types:
        {json.dumps(cls.PARAMETER_TYPES, indent=2)}
        
        Note: All fields are NULLABLE, so always use COALESCE or IS NOT NULL checks when needed.
        """

class FlightAnalyticsAgent:
    """
    Handles analytics queries by generating, validating, and executing SQL against BigQuery.
    Summarizes results using Gemini and maintains conversational memory for context-aware analytics.
    """
    def __init__(self):
        """
        Initialize the analytics agent, configure Gemini, and set up BigQuery client and memory.
        """
        genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
        self.model = genai.GenerativeModel('models/gemini-1.5-pro')
        self.summarizer = self.model
        self.bq_client = bigquery.Client(project=os.getenv('GOOGLE_CLOUD_PROJECT'))
        self.schema = FlightDataSchema()
        
        # Initialize memory for conversation context
        self.memory = {
            'last_query_type': None,
            'last_origin': None,
            'last_destination': None,
            'last_year': None,
            'last_limit': None
        }
    
    def _validate_and_structure_sql(self, query: str) -> dict:
        """
        Use Gemini to validate and structure the SQL query for analytics.
        Returns a dictionary with validated SQL and parameters.
        Args:
            query (str): The user's analytics query.
        Returns:
            dict: Structured SQL, parameters, query type, and extracted values.
        """
        prompt = f"""
        Given this user query: "{query}"
        
        {self.schema.get_schema_prompt()}
        
        Generate a JSON response with:
        1. A valid BigQuery SQL query
        2. A list of parameters needed
        3. The query type (e.g., 'on_time_airlines', 'day_of_week_delays', 'general_analytics')
        4. Any extracted values (airports, year, limit)

        Rules:
        1. SQL must be parameterized
        2. Add LIMIT 50
        3. Handle NULLs
        4. Never include price-related queries
        5. Use proper BigQuery syntax
        6. Include proper error handling
        7. Use the provided schema and query patterns when applicable

        Return ONLY the JSON, no other text.
        """
        
        try:
            response = self.model.generate_content(prompt)
            result = json.loads(response.text.strip())
            
            # Validate the response structure
            required_keys = ['sql', 'parameters', 'query_type', 'extracted_values']
            if not all(key in result for key in required_keys):
                raise ValueError("Invalid response structure from Gemini")
                
            return result
            
        except Exception as e:
            return {
                'error': f"Failed to validate query: {str(e)}",
                'sql': None,
                'parameters': [],
                'query_type': 'error',
                'extracted_values': {}
            }
    
    def handle(self, input_data):
        """
        Process a user analytics query, generate and execute SQL, and return a summary.
        Args:
            input_data (dict): Dictionary containing the user's query string.
        Returns:
            dict: Structured response with code, message, summary, and query type.
        """
        query = input_data["query"]
        
        # First, validate and structure the SQL
        validation_result = self._validate_and_structure_sql(query)
        
        if 'error' in validation_result:
            return {
                "code": "VALIDATION_ERROR",
                "message": validation_result['error'],
                "details": "Failed to validate query structure",
                "suggestion": "Please rephrase your analytics question."
            }
        
        # Update memory with extracted values
        self._update_memory(validation_result['extracted_values'])
        
        try:
            # Execute BigQuery with parameters
            query_job = self.bq_client.query(
                validation_result['sql'],
                job_config=bigquery.QueryJobConfig(
                    query_parameters=validation_result['parameters']
                )
            )
            
            results = query_job.result()
            if results.total_rows == 0:
                return {
                    "code": "NOT_FOUND",
                    "message": "No matching records found.",
                    "details": "",
                    "suggestion": "Try a different query."
                }
            
            rows = [dict(row) for row in results]
            table = self._format_results(rows)
            
            # Summarize with Gemini
            summary_prompt = f"""
            Summarize these flight analytics results in 2-3 sentences for a human traveler.
            Query type: {validation_result['query_type']}
            Results:
            {table}
            """
            summary_response = self.summarizer.generate_content(summary_prompt)
            summary = summary_response.text.strip()
            
            return {
                "code": "SUCCESS",
                "message": "Analytics summary generated.",
                "data": summary,
                "query_type": validation_result['query_type']
            }
            
        except Exception as e:
            return {
                "code": "SYSTEM_ERROR",
                "message": "Analytics error.",
                "details": str(e),
                "suggestion": "Please try again later."
            }
    
    def _update_memory(self, extracted_values: dict):
        """
        Update the agent's conversational memory with extracted values from the query.
        Args:
            extracted_values (dict): Dictionary of values extracted from the user's query.
        """
        if 'origin' in extracted_values:
            self.memory['last_origin'] = extracted_values['origin']
        if 'destination' in extracted_values:
            self.memory['last_destination'] = extracted_values['destination']
        if 'year' in extracted_values:
            self.memory['last_year'] = extracted_values['year']
        if 'limit' in extracted_values:
            self.memory['last_limit'] = extracted_values['limit']
    
    def _format_results(self, data):
        """
        Format the analytics query results as a readable table for summarization.
        Args:
            data (list): List of result rows (dicts).
        Returns:
            str: Formatted table string or message if no results.
        """
        if not data: 
            return "No results found"
        
        columns = list(data[0].keys())
        output = " | ".join(columns) + "\n"
        output += "-" * 50 + "\n"
        
        for row in data[:5]:
            output += " | ".join(str(row.get(col, '')) for col in columns) + "\n"
        
        if len(data) > 5:
            output += f"\nShowing 5 of {len(data)} records"
        
        return output 
    
    