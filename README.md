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
