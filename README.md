# 💵 Global Finance Assistant – Technical Documentation

📌 A voice-enabled multi-agent assistant that delivers spoken market briefings based on user queries.  
**Built with:** CrewAI, LangChain, OpenAI, ChromaDB, Streamlit  

🔗 [Live Demo](https://finance-research-crew.streamlit.app/)

---

## 🔊 Input Flow

Users can provide input in two ways:

- **Voice**  
  Recorded via `audiorecorder`, transcribed using **AssemblyAI API**
- **Text**  
  Entered manually into the Streamlit text input field

> ✅ Both types are unified into a single query string before moving to the next stage.

---

## 🔍 Gemini-Based Query Validation

All inputs go through a **Gemini-powered validation** step to ensure:

- The query is financially relevant  
- It is ethically appropriate  
- It has sufficient clarity and specificity  

### ✅ Prompt Used

```json
You are a compliance officer for a financial assistant.

Evaluate the following query and respond ONLY with JSON like:
{
  "is_finance": true,
  "is_ethical": true,
  "confidence": 42,
  "reason": "Explain the confidence level briefly.",
  "suggestions": [
    "Improved version of the query suggestion 1",
    "Improved version of the query suggestion 2"
  ]
}

Query: {user_query}
```

### ⚠️ If Not Valid
If `is_finance == false` or `is_ethical == false`, the assistant halts and:

- Explains why the query was rejected
- Offers up to 3 suggestions for improvement

---

## 🧠 Multi-Agent Workflow Kickoff
Once validated, the query triggers the multi-agent finance crew, orchestrated by CrewAI.

### Agents Involved
| Agent | Task |
|-------|------|
| Confidence Checker | Validates prompt quality |
| Market Data Researcher | Gathers live market data |
| Filing Scraper | Extracts recent earnings reports |
| Retriever | Retrieves past insights from vector DB |
| Quantitative Analyst | Analyzes risk and EPS surprises |
| Language Narrator | Crafts Bloomberg-style narrative |
| Voice Financier | Converts briefing to audio |

---

## 🔄 Agent Prompts & Tasks

### 1. Confidence Checker
🎯 **Purpose:** Ensure the query is clear, specific, and similar to indexed prompts.

🧩 **Prompt:**
```text
Rate this query on clarity and specificity (1-10):
"{query}"
Respond only with the number.
```

📦 **Output:**
```json
{
  "confidence_score": 0.92,
  "similarity_score": 0.78,
  "route_to_data_agents": true,
  "suggestions": []
}
```

### 2. Market Data Researcher
🎯 **Purpose:** Extract company names or tickers and fetch real-time data.

🧩 **Prompt:**
```text
Extract company names or tickers related to this query:
"{query}"
Respond only with comma-separated symbols or names.
```

📦 **Output Example:**
```json
[
  {
    "ticker": "AAPL",
    "name": "Apple Inc.",
    "price": 194.25,
    "change_percent": 1.25,
    "volume": 98765432,
    "eps_trailing_12m": 5.82
  }
]
```

### 3. Filing Scraper
🎯 **Purpose:** Scrape investor relations pages for recent filings or disclosures.

🧩 **Prompt:**
```text
Extract company names or tickers related to this query:
"{query}"
Respond only with comma-separated symbols or names.
```

📦 **Output Example:**
```json
[
  {
    "company": "AAPL",
    "source": "https://investor.apple.com/releases/",
    "summary": "EPS came in at $5.82, outperforming analyst estimates by 8%. Volume was above average..."
  }
]
```

### 4. Retriever
🎯 **Purpose:** Retrieve semantically similar past insights from the knowledge base.

🧩 **Prompt:** N/A (uses semantic search)

📦 **Output Example:**
```json
[
  {
    "content": "Apple shares rose after Q2 earnings beat...",
    "similarity": 0.85
  },
  {
    "content": "iPhone sales drove revenue growth in Asia...",
    "similarity": 0.78
  }
]
```

### 5. Quantitative Analyst
🎯 **Purpose:** Analyze portfolio exposure, EPS surprise, and sentiment.

🧩 **Prompt:**
```text
Given the following query:
"{query}"

Analyze and summarize:
- Allocation delta
- Earnings surprises
- Risk exposure
- Regional sentiment

Return structured JSON output.
```

📦 **Output Example:**
```json
{
  "allocation_change": "+5%",
  "earnings_surprise": "+8%",
  "risk_exposure": "Moderate",
  "regional_sentiment": "Positive in APAC"
}
```

### 6. Language Narrator
🎯 **Purpose:** Generate a spoken-style market brief.

🧩 **Prompt:**
```text
Write a concise 3-paragraph spoken market briefing:
Query: {query}

Include:
- Exposure change
- Key earnings surprises
- Sentiment summary

Style: Confident, professional, Bloomberg-style tone.
```

📦 **Output Example:**
> "Apple's shares rose 1.25% today, closing at $194.25, following a strong Q2 earnings beat. EPS came in at $5.82, outperforming analyst estimates by 8%. Volume was above average at 98 million shares traded…"

### 7. Voice Broadcaster
🎯 **Purpose:** Convert final narrative into speech.

🧩 **Prompt:** None – acts as wrapper around TTS engine (gTTS / AssemblyAi)

📦 **Output Example:**
```
[AUDIO FILE GENERATED FROM TEXT]
```

---

## 🎙️ Final Output
After all agents complete their tasks:

- The final briefing is displayed in the UI
- An audio file is generated using gTTS or Piper
- Users can listen to the briefing instantly

---

## 🛠️ Tech Stack
| Component | Tools/Tech Used |
|-----------|----------------|
| Agents | CrewAI |
| LLMs | Gemini, OpenAI |
| Tools | yfinance, BeautifulSoup, ChromaDB |
| UI | Streamlit |
| TTS | gTTS / Piper |
| Hosting | Streamlit Community Cloud |

---

## 📈 Performance Benchmarks
| Task | Duration |
|------|----------|
| Confidence Check | 1.2s |
| Market Data Fetch | 3.5s |
| Filing Scraping | 4.8s |
| Quantitative Analysis | 2.1s |
| Narrative Synthesis | 1.8s |
| **Total Flow** | **~13.4s** |

*Sequential execution*

---

## 📢 Live Demo
🔗 [Try the App](https://finance-research-crew.streamlit.app/)

Try it with:
- Voice queries about Apple, Tesla, or global markets
- Text input for regional or sector-specific questions
- Get instant spoken market briefings!
