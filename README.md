# **Air Travel Assistant**

---

## **About This Project**

*The Air Travel Assistant is designed to be flexible and easy to extend to any functionalities you wish to add—like extended logging, integrating with additional APIs for more complex queries, and advanced processing of information. For now, it answers all the questions of any user trying to find information about flights, their status, and analytics such as performance, on-time rates, and recommendations. The architecture is built for real-world use, with a focus on clarity and maintainability.*

---

## **How to Get Up and Running**

**1. Download the Code**
- Open your terminal and run:
  ```bash
  git clone [your-repository-url]
  cd air-travel-assistant
  ```

**2. Set Up Your Python Environment**
- Create a virtual environment to keep dependencies isolated:
  ```bash
  python -m venv venv
  source venv/bin/activate  # On Windows: venv\Scripts\activate
  ```

**3. Install All Required Packages**
- With your environment active, install dependencies:
  ```bash
  pip install -r requirements.txt
  ```

**4. Prepare Your API Keys and Environment Variables**
- Copy the example environment file and fill in your keys:
  ```bash
  cp .env.example .env
  # Open .env in your editor and add:
  # AVIATIONSTACK_API_KEY=your_aviationstack_key
  # GEMINI_API_KEY=your_gemini_key
  # GOOGLE_CLOUD_PROJECT=your_gcp_project_id
  # FLASK_SECRET_KEY=your_flask_secret
  ```

**5. Authenticate with Google Cloud**
- Make sure you're logged in and have the right permissions:
  ```bash
  gcloud auth application-default login
  ```

**6. Start the Application**
- Launch the server:
  ```bash
  python main.py
  ```
- Open your browser and go to: `http://localhost:5000`

---

## **My Design Choices (and Why I Made Them)**

> *Every decision here is intentional, based on practical engineering experience. Here's why I built things the way I did:*

### **1. Hybrid Routing (Regex + LLM)**
**Why:** I didn't want to rely solely on a cloud LLM for every query—it's expensive, slow, and unnecessary for simple cases. So, I use regular expressions to instantly catch obvious flight status queries (like "AA123"). Only when the intent is ambiguous or more complex do I call Gemini for classification. This keeps the system fast, cost-effective, and reliable.

### **2. Why I Avoided Logging in the Inquiry Router**
**Why:** For this project, I intentionally left out detailed logging in the inquiry router. The main reason is to keep the routing logic as lightweight and fast as possible—especially since the router is called for every single user query. In a production environment, logging every routing decision can introduce unnecessary overhead, clutter logs with routine operations, and potentially expose sensitive user queries. Instead, I focused on robust error handling and clear code structure. If this were a high-traffic, multi-tenant system or if we needed to audit routing decisions for compliance, I would add targeted, privacy-conscious logging. For this prototype and most real-world use cases, keeping the router lean and focused on performance is the right trade-off.

### **3. Modular Agent Architecture**
**Why:** I split the system into clear, single-responsibility agents: one for routing, one for real-time status, and one for analytics. This makes the codebase easy to extend (add new agents or data sources), test, and debug. If anybody wants to extend this to new features such as price analytics or weather impact in the future, all you need to do is just add a new agent.

### **4. Gemini Summarization for Output**
**Why:** Most users don't want to read raw tables or technical data—they want clear, actionable answers. That's why I use Gemini to summarize both analytics and status results into plain English. This makes the assistant accessible to everyone, not just data nerds.

### **5. Parameterized SQL and Schema Validation**
**Why:** Security and correctness matter. All analytics queries are parameterized and validated using Gemini, which means no SQL injection and no schema mismatches. I only allow queries that make sense for the data I actually have.

### **6. Conversational Memory**
**Why:** I wanted the assistant to feel natural. If you ask about SFO to JFK, then follow up with "What about to ATL?", the system remembers your last intent and fills in the blanks. This is handled with simple, session-based memory—no over-engineering.

### **7. Structured Error Handling**
**Why:** I've seen too many systems that just throw cryptic errors. Here, every error is returned as a structured JSON object with a code, message, details, and suggestions. This helps both users and developers quickly understand what went wrong and how to fix it.

### **8. Minimal Cloud Usage**
**Why:** Cloud APIs are powerful, but they cost money and introduce latency. I only use them where they add real value (intent classification, summarization, analytics validation). Everything else is handled locally when possible.

### **9. No Over-Engineering**
**Why:** I avoided microservices, heavy frameworks, and unnecessary abstractions. The system is simple, modular, and easy to deploy. If you want to add more features, you can do so without fighting the architecture.

### **10. Security and Privacy**
**Why:** Sensitive data (like API keys and user context) is handled securely. I don't store anything I don't need, and I keep everything as private as possible.

---

## **What This System Can Do**

- **Real-Time Flight Status:** Instantly fetches and summarizes live flight status using the AviationStack API.
- **Historical Flight Analytics:** Surfaces actionable analytics from BigQuery, including on-time performance, delay patterns, and more.
- **Conversational Routing:** Uses a hybrid of LLM-based and rule-based logic to route user queries to the right agent.
- **Contextual Memory:** Remembers user context and query history, enabling natural follow-up questions and personalization.
- **Human-Readable Summaries:** All analytics and status responses are summarized in clear, concise language using Gemini.
- **Structured Error Handling:** Every error is returned as a structured JSON object with actionable suggestions—no cryptic stack traces.

---

## **Example Usage**

### **Flight Status Agent Example**

- _"What's the status of AA123?"_  → Returns a human-readable summary like:

```json
{
  "code": "SUCCESS",
  "message": "Flight status retrieved successfully.",
  "data": "American Airlines flight AA123 from Dallas/Fort Worth (DFW) to Kahului (OGG) has landed. Despite departing 21 minutes late, it arrived 5 ahead of schedule."
}
```

### **Flight Analytics Agent Example**

- _"What is the most on-time airline from JFK to BOS?"_  → Returns a human-readable summary like:

```json
{
  "code": "SUCCESS",
  "message": "Analytics summary generated.",
  "data": "For flights from JFK to BOS, the most on-time airline is JetBlue Airways, with an average overall delay of 5 minutes and 91% of flights arriving on time. Delta Air Lines and American Airlines also operate this route, but with slightly higher average delays.",
  "query_type": "on_time_airlines"
}
```

- _"SFO to ATL?"_  → Follows up using conversational memory and returns:

```json
{
  "code": "SUCCESS",
  "message": "Analytics summary generated.",
  "data": "For flights from SFO to ATL, the most on-time airline is Delta Air Lines, with an average overall delay of 7 minutes and 88% of flights arriving on time. United Airlines and American Airlines also serve this route, but with higher average delays.",
  "query_type": "on_time_airlines"
}
```

---

## **API Details**

- **POST /chat**
    - Request: `{ "query": "your question here" }`
    - Response: Structured JSON with `code`, `message`, `data`, and suggestions.
- **GET /**
    - Returns the web interface.

---

## **Error Handling Philosophy**

Every error is handled with the end user in mind. Instead of cryptic errors, you'll get:
```json
{
  "code": "ERROR_CODE",
  "message": "Clear, actionable message",
  "details": "Technical details for debugging",
  "suggestion": "What to try next"
}
```
This makes both debugging and user support dramatically easier.

---

## **Deployment & Production Notes**

- All SQL queries are parameterized and validated by Gemini to prevent injection and ensure schema compliance.
- Agents are modular—add new analytics or data sources by subclassing and registering new agents.
- The system like I mentioned is readily designed for extensibility: swap out the LLM, add new APIs, or integrate with notification services (e.g., Twilio, SendGrid) as needed.
- For production, set strong secrets and use HTTPS. Monitor API quotas and error logs.


---

## **License**

MIT License. See LICENSE for details.

---

**If you have questions, suggestions, or want to discuss - reach out directly - Arun Yalamati.** 