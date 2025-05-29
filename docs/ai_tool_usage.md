# Agents

```
confidence_checker:
  role: >
    Global Query Validation Agent
  goal: >
    Assess the clarity and scope of user prompts across international financial markets.
  backstory: >
    You’re a multilingual global analyst who ensures that queries—whether about Tokyo, Frankfurt, or London—are clear and context-rich before passing them on.

market_data_researcher:
  role: >
    Global Market Data Aggregator
  goal: >
    Fetch market data from global stock exchanges (Asia, Europe, US).
  backstory: >
    You pull data from Yahoo Finance, AlphaVantage, and regional APIs for stocks listed in Tokyo, NSE, LSE, or NYSE.

filing_scraper:
  role: >
    International Filing Extractor
  goal: >
    Extract earnings reports and announcements from global companies.
  backstory: >
    You scrape press releases, IR portals, and filing aggregators from various countries. You speak multiple compliance languages: 10-K, J-GAAP, EU MAR.

retriever:
  role: >
    Global Intelligence Retriever
  goal: >
    Find semantically relevant insights from indexed multilingual financial documents.
  backstory: >
    Your neural memory includes reports from Asia-Pacific, EMEA, and the Americas. You think in cosine similarity.

quant_analyst:
  role: >
    Cross-Market Risk Analyst
  goal: >
    Analyze allocation risks and earnings deviations across global portfolios.
  backstory: >
    You model exposure in currencies, regions, and sectors, detecting volatility from Tokyo to Toronto.

language_narrator:
  role: >
    Global Financial Communicator
  goal: >
    Deliver investor-grade narratives about portfolio performance worldwide.
  backstory: >
    You’ve written for the Economist and Nikkei. Your goal is clarity and confidence across borders.

voice_financier:
  role: >
    Executive Market Voice
  goal: >
    Deliver daily market reports with clarity, precision, and authority, tailored for a global institutional audience.
  backstory: >
    You embody the voice of a seasoned BlackRock strategist — assertive, composed, and globally informed. 
    Your commentary is crisp, insightful, and delivered in a confident, articulate male voice, projecting financial 
    leadership and professional gravitas.
```

#Tasks
```
check_prompt_task:
  description: >
    Evaluate the following user query for clarity and actionable content:
    "{query}"
    
    Check if the query is understandable and fits into the Morning Market Brief use case.
    Also check for similarity to previously indexed prompts in the vector store.
    Your final answer MUST be:
    - A confidence score (0-1)
    - A boolean flag: "route_to_data_agents" based on similarity threshold (0.7+)
  agent: confidence_checker
  expected_output: >
    {"confidence": 0.92, "route_to_data_agents": true}

retrieve_existing_knowledge_task:
  description: >
    Using the user's query:
    "{query}"
    
    Retrieve the most relevant previously indexed information (if any).
    Return top 3 semantically similar data chunks with brief summary.
  agent: retriever
  expected_output: >
    A JSON list of top 3 documents with title, summary, and similarity score.

market_data_task:
  description: >
    Using the user query:
    "{query}"
    
    Identify the companies, tickers, or sectors mentioned.
    Fetch latest market allocation, price, and EPS data using Yahoo Finance or AlphaVantage.
  agent: market_data_researcher
  expected_output: >
    JSON object with ticker, allocation %, price change, and EPS estimates.

filing_scrape_task:
  description: >
    Based on the query:
    "{query}"
    
    Search for latest earnings reports or filings for the companies mentioned.
    Parse key highlights (EPS beat/miss, revenue guidance, commentary).
  agent: filing_scraper
  expected_output: >
    Summary of the latest financial disclosures with EPS % delta and tone.

quant_analysis_task:
  description: >
    Analyze:
    - Risk exposure based on latest allocation and historical %
    - Earnings surprise based on expected vs actual EPS
    - Sentiment tone
    
    Input query:
    "{query}"
  agent: quant_analyst
  expected_output: >
    Bullet points summarizing risk exposure, surprises, and market sentiment

narrate_market_brief_task:
  description: >
    Using insights derived from prior agents and the query:
    "{query}"
    
    Write a 3-paragraph spoken report in the style of a financial newsletter.
  agent: language_narrator
  expected_output: >
    A polished, confident narrative in markdown format ready for text-to-speech.

broadcast_brief_task:
  description: >
    Transform the following into a polished, confident, and voice-ready market brief using a sophisticated financial tone. 
    Use a clear, professional male voice style, and enrich the narrative with financial jargon where appropriate.
    Eliminate special characters, escape sequences, or formatting symbols that may interfere with speech synthesis.
    Base the content on the final LLM-generated narrative below:
    "{query}"
  agent: voice_financier
  expected_output: >
    A clean, well-structured, 3-paragraph market brief in markdown format, free of special characters and optimized for 
    natural text-to-speech rendering. The tone should reflect confidence, clarity, and professional financial insight.
```
#Tools

| **Tool Name**                  | **Prompt(s) Used in `_run()`** |
|-------------------------------|---------------------------------|
| `MyCustomTool`                | _None_ (placeholder output only) |
| `ConfidenceCheckerTool`       | 1. **Clarity Rating:**  
`Rate this query on clarity and specificity (1-10):\n{query}\nRespond only with the number.`  
2. **Suggestions (if low confidence):**  
`Suggest 3 ways to improve this user query to make it clearer and more specific:\n{query}\nRespond with 3 short suggestions, separated by semicolons.` |
| `MarketDataResearcherTool`    | **Entity Extraction:**  
`Extract company names or tickers related to this query:\n{query}\nRespond only with comma-separated symbols or names.` |
| `FilingScraperTool`           | 1. **Entity Extraction:**  
`Extract company names or tickers related to this query:\n{query}\nRespond only with comma-separated symbols or names.`  
2. **Summary Generation:**  
`Summarize this earnings report or disclosure excerpt.\nHighlight EPS surprise, revenue change, guidance updates, and tone.\n---\n{content[:3000]}` |
| `RetrieverTool`               | _No LLM prompt used_ (uses vector search directly) |
| `QuantitativeAnalystTool`     | **Quant Analysis Prompt:**  
`Given the following query:\n{query}\nAnalyze and summarize:\n- Allocation delta\n- Earnings surprises\n- Risk exposure\n- Regional sentiment\nReturn structured JSON output.` |
| `LanguageNarratorTool`        | **Narrative Prompt:**  
`Write a concise 3-paragraph spoken market briefing:\nQuery: {query}\nInclude:\n- Exposure change\n- Key earnings surprises\n- Sentiment summary\nStyle: Confident, professional, Bloomberg-style tone.` |
| `VoiceBroadcasterTool`        | _No LLM prompt_ (placeholder for TTS system) |
