# Air Travel Assistant: Setup & Usage Guide

---

## 1. How to Set Up and Run This Project

**Step 1: Clone the repository**
```
git clone <your-repo-url>
cd air-travel-assistant
```

**Step 2: Set up your Python environment**
```
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

**Step 3: Configure environment variables**
- Copy `.env.example` to `.env` and fill in your API keys and secrets:
  - `GEMINI_API_KEY`
  - `AVIATIONSTACK_API_KEY`
  - `GOOGLE_CLOUD_PROJECT`
  - `FLASK_SECRET_KEY`

**Step 4: Authenticate with Google Cloud**
```
gcloud auth application-default login
```

**Step 5: Run the application**
```
python main.py
```
- Open your browser and go to: `http://localhost:5000`

---

## 2. Brief Explanation of Design Choices - As to why!!???

- **Hybrid Routing (LLM + Regex):** I chose a hybrid approach for routing queries because it balances cost, speed, and reliability. Regex handles obvious cases (like flight numbers) instantly and locally, reducing unnecessary cloud LLM calls and keeping latency and costs low. The LLM is only used for ambiguous or complex queries, ensuring flexibility without overusing cloud resources.
- **Summarizing Instead of Raw Output:** I chose to generate human-readable summaries (using Gemini) rather than just outputting raw analytics tables or status data. This is because most users—especially find it easy to have clear, actionable insights, not just numbers or database rows. Summaries help users quickly understand what matters (e.g., "Delta is the most on-time airline on this route" or "Your flight is on time and departs from Gate 12"). This approach also makes the system more accessible to non-technical users and reduces cognitive load, while still allowing access to detailed data if needed.
- **Selective Use of Cloud/LLM:** I intentionally limited LLM and cloud API usage to only where it adds real value—such as intent classification, SQL validation, and summarization. This keeps the system efficient, cost-effective, and responsive, while still leveraging advanced AI where it matters most.
- **Not Implementing Price Analytics:** I did not include price-based analytics because the current data schema does not support it, and integrating price data would require new data sources and schema changes. I focused on features that could be robustly supported by the available data.
- **No User Accounts/Profiles (Yet):** User personalization is session-based for now. Full user accounts would require additional authentication, storage, and compliance work, which can be added as a future extension.
- **No Over-Engineering:** I avoided adding features like complex orchestration, microservices, or heavy frontend frameworks to keep the system maintainable and easy to deploy for most users. The architecture is intentionally simple but modular, so it can be extended as needed.
- **Security and Privacy:** All sensitive operations (like API keys and user context) are handled securely, and only the minimum necessary data is stored in memory or logs.
- **Why Only What's Necessary:** Every design choice was made to maximize reliability, minimize cost, and keep the system easy to understand and extend. If a feature or dependency wasn't strictly needed, I left it out to avoid unnecessary complexity.
- **Modular Agents:** Each core function (routing, status, analytics) is handled by a dedicated agent class. This makes the system easy to extend and maintain.
- **Safe Analytics:** All SQL queries are parameterized and validated by Gemini, reducing the risk of SQL injection and schema errors.
- **Conversational Memory:** The system remembers user context (like last route or analytics intent), so follow-up queries feel natural.
- **Structured Error Handling:** Every error is returned as a structured JSON object with a code, message, details, and suggestions. This is both user- and developer-friendly.
- **Human-Readable Summaries:** All analytics and status responses are summarized using Gemini, so users get clear, actionable information.
- **Frontend/Backend Separation:** The backend always returns structured JSON, making it easy to integrate with any frontend or API consumer.

---

## 3. Sample Inputs and Outputs

Below are two real examples—one for each agent path. 

These are actual queries and the kind of responses you can expect.

### A. Flight Status Agent Path

**Sample Input:**
```
What's the status of AA123?
```

**Sample Output:**
```json
{
  "code": "SUCCESS",
  "message": "Flight status retrieved successfully.",
  "data": "Flight Status Report for AA123 (American Airlines)\nStatus: On Time\nRoute: Dallas (DFW) → New York (JFK)\nScheduled Departure: 2024-06-10 08:00 UTC | Actual Departure: 2024-06-10 08:05 UTC\nScheduled Arrival: 2024-06-10 11:00 UTC | Estimated Arrival: 2024-06-10 10:55 UTC\nTerminal: B | Gate: 12\nOn time"
}
```

---

### B. Flight Analytics Agent Path

**Sample Input:**
```
Show me the most on-time airlines from SFO to JFK in 2023
```

**Sample Output:**
```json
{
  "code": "SUCCESS",
  "message": "",
  "data": "In 2023, the most on-time airlines from SFO to JFK were:\n1. Delta Air Lines: Average delay 3 min, 92% on time\n2. Alaska Airlines: Average delay 5 min, 89% on time\n3. American Airlines: Average delay 7 min, 85% on time\nDelta Air Lines had the best on-time performance for this route.",
  "query_type": "on_time_airlines"
}
```

---

**If you have any questions or run into issues, please open an issue or reach out directly.** 