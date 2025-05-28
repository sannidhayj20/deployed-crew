from crewai.tools import BaseTool
from typing import Type
from pydantic import BaseModel, Field
from typing import Type,Union,Any,Dict,List
import os
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")

class MyCustomToolInput(BaseModel):
    """Input schema for MyCustomTool."""
    argument: str = Field(..., description="Description of the argument.")

class MyCustomTool(BaseTool):
    name: str = "Name of my tool"
    description: str = (
        "Clear description for what this tool is useful for, your agent will need this information to use it."
    )
    args_schema: Type[BaseModel] = MyCustomToolInput

    def _run(self, argument: str) -> str:
        # Implementation goes here
        return "this is an example of a tool output, ignore it and move along."


from crewai.tools import BaseTool
from typing import Type
from pydantic import BaseModel, Field
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings, OpenAI
import os
import json

CHROMA_PATH = "./chroma"
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")
class ConfidenceCheckerInput(BaseModel):
    """Input schema for ConfidenceChecker."""
    query: Union[str, Dict[str, Any]] = Field(..., description="User query about financial markets.")
class ConfidenceCheckerTool(BaseTool):
    name: str = "confidence_and_similarity_check"
    description: str = (
        "Evaluates prompt clarity and checks similarity against historical prompts in vector DB."
    )
    args_schema: Type[BaseModel] = ConfidenceCheckerInput

    def _run(self, query: Union[str, Dict[str, Any]]) -> str:
        # Load embeddings + FAISS
        embeddings = OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY)
        vectordb = Chroma(persist_directory=CHROMA_PATH, embedding_function=embeddings)

        # LLM-based confidence scoring
        llm = OpenAI(temperature=0, openai_api_key=OPENAI_API_KEY)
        eval_prompt = (
            f"Rate this query on clarity and specificity (1-10):\n"
            f"{query}\n"
            "Respond only with the number."
        )
        try:
            llm_score = float(llm.invoke(eval_prompt).strip()) / 10.0
        except:
            llm_score = 0.5

        # Similarity check
        results = vectordb.similarity_search_with_score(query, k=1)
        similarity_score = round(results[0][1], 2) if results else 0.0

        route_to_data_agents = llm_score > 0.6 or similarity_score > 0.7

        return json.dumps({
            "confidence_score": round(llm_score, 2),
            "similarity_score": similarity_score,
            "route_to_data_agents": route_to_data_agents
        })
    
from crewai.tools import BaseTool
from typing import Type
from pydantic import BaseModel, Field
from langchain_openai import OpenAI
import yfinance as yf
import os
import json

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

class MarketDataResearcherInput(BaseModel):
    """Input schema for MarketDataResearcher."""
    query: str = Field(..., description="User query about market data.")

class MarketDataResearcherTool(BaseTool):
    name: str = "market_data_researcher"
    description: str = (
        "Fetches real-time market data for companies mentioned in the query."
    )
    args_schema: Type[BaseModel] = MarketDataResearcherInput

    def _run(self, query: str) -> str:
        llm = OpenAI(temperature=0, openai_api_key=OPENAI_API_KEY)

        extraction_prompt = (
            f"Extract company names or tickers related to this query:\n{query}\n"
            "Respond only with comma-separated symbols or names."
        )
        response = llm.invoke(extraction_prompt)
        entities = [e.strip() for e in response.strip().split(",")]

        results = []
        for entity in entities:
            try:
                ticker = yf.Ticker(entity)
                info = ticker.info
                history = ticker.history(period="1d")
                if history.empty:
                    continue

                current_price = round(history["Close"].iloc[-1], 2)
                previous_close = round(history["Open"].iloc[0], 2)
                change_percent = round(((current_price - previous_close) / previous_close) * 100, 2)
                volume = int(history["Volume"].iloc[-1])
                eps = info.get("epsTrailingTwelveMonths", None)

                result = {
                    "ticker": info.get("symbol"),
                    "name": info.get("shortName"),
                    "price": current_price,
                    "change_percent": change_percent,
                    "previous_close": previous_close,
                    "volume": volume,
                    "eps_trailing_12m": eps
                }
                results.append(result)

            except Exception as e:
                print(f"Error fetching data for {entity}: {str(e)}")

        return json.dumps(results, indent=2)
    
from crewai.tools import BaseTool
from typing import Type
from pydantic import BaseModel, Field
from langchain_openai import OpenAI
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import os
import json

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

class FilingScraperInput(BaseModel):
    """Input schema for FilingScraper."""
    query: str = Field(..., description="Query containing company names or tickers.")

class FilingScraperTool(BaseTool):
    name: str = "filing_scraper"
    description: str = (
        "Scrapes recent earnings reports and filings based on query."
    )
    args_schema: Type[BaseModel] = FilingScraperInput

    def _run(self, query: str) -> str:
        llm = OpenAI(temperature=0, openai_api_key=OPENAI_API_KEY)

        extraction_prompt = (
            f"Extract company names or tickers related to this query:\n{query}\n"
            "Respond only with comma-separated symbols or names."
        )
        response = llm.invoke(extraction_prompt)
        entities = [e.strip() for e in response.strip().split(",")]

        results = []

        for entity in entities:
            try:
                ir_url = f"https://www.google.com/search?q= {entity} investor relations latest earnings report OR filing"
                headers = {"User-Agent": "Mozilla/5.0"}
                resp = requests.get(ir_url, headers=headers)
                soup = BeautifulSoup(resp.text, 'html.parser')
                links = [a['href'] for a in soup.find_all('a', href=True)]
                relevant_links = [urljoin(ir_url, link) for link in links if 'ir' in link or 'news' in link]

                if relevant_links:
                    content = BeautifulSoup(requests.get(relevant_links[0], headers=headers).text, 'html.parser').get_text()
                    summary_prompt = (
                        "Summarize this earnings report or disclosure excerpt.\n"
                        "Highlight EPS surprise, revenue change, guidance updates, and tone.\n"
                        "---\n"
                        f"{content[:3000]}"
                    )
                    summary = llm.invoke(summary_prompt).strip()
                    results.append({
                        "company": entity,
                        "source": relevant_links[0],
                        "summary": summary
                    })

            except Exception as e:
                print(f"Error processing {entity}: {str(e)}")

        return json.dumps(results, indent=2)
    
from crewai.tools import BaseTool
from typing import Type
from pydantic import BaseModel, Field
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings
import os
import json

CHROMA_PATH = "./chroma"

class RetrieverToolInput(BaseModel):
    """Input schema for RetrieverTool."""
    query: str = Field(..., description="User query to search in vector store.")

class RetrieverTool(BaseTool):
    name: str = "retriever_tool"
    description: str = (
        "Retrieves top-k similar documents from the vector database."
    )
    args_schema: Type[BaseModel] = RetrieverToolInput

    def _run(self, query: str) -> str:
        embeddings = OpenAIEmbeddings()
        vectordb = Chroma(persist_directory=CHROMA_PATH, embedding_function=embeddings)
        docs = vectordb.similarity_search(query, k=3)

        matches = [{"content": doc.page_content, "similarity": 0.85} for doc in docs]
        return json.dumps(matches, indent=2)
    
from crewai.tools import BaseTool
from typing import Type
from pydantic import BaseModel, Field
from langchain_openai import OpenAI
import os
import json

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

class QuantitativeAnalystInput(BaseModel):
    """Input schema for QuantitativeAnalyst."""
    query: str = Field(..., description="Query for risk allocation and surprises.")

class QuantitativeAnalystTool(BaseTool):
    name: str = "quant_analyst"
    description: str = (
        "Analyzes portfolio risk, allocation changes, and earnings surprises."
    )
    args_schema: Type[BaseModel] = QuantitativeAnalystInput

    def _run(self, query: str) -> str:
        llm = OpenAI(temperature=0, openai_api_key=OPENAI_API_KEY)
        analysis_prompt = (
            "Given the following query:\n"
            f"{query}\n"
            "Analyze and summarize:\n"
            "- Allocation delta\n"
            "- Earnings surprises\n"
            "- Risk exposure\n"
            "- Regional sentiment\n"
            "Return structured JSON output."
        )
        response = llm.invoke(analysis_prompt)
        return response.strip()
    
from crewai.tools import BaseTool
from typing import Type
from pydantic import BaseModel, Field
from langchain_openai import OpenAI
import os
import json

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

class LanguageNarratorInput(BaseModel):
    """Input schema for LanguageNarrator."""
    query: str = Field(..., description="Query to generate spoken briefing from.")

class LanguageNarratorTool(BaseTool):
    name: str = "language_narrator"
    description: str = (
        "Generates a spoken narrative based on analysis and context."
    )
    args_schema: Type[BaseModel] = LanguageNarratorInput

    def _run(self, query: str) -> str:
        llm = OpenAI(temperature=0.7, openai_api_key=OPENAI_API_KEY)
        narrative_prompt = (
            "Write a concise 3-paragraph spoken market briefing:\n"
            f"Query: {query}\n"
            "Include:\n"
            "- Exposure change\n"
            "- Key earnings surprises\n"
            "- Sentiment summary\n"
            "Style: Confident, professional, Bloomberg-style tone."
        )
        response = llm.invoke(narrative_prompt)
        return response.strip()
    
from crewai.tools import BaseTool
from typing import Type
from pydantic import BaseModel, Field

class VoiceBroadcasterInput(BaseModel):
    """Input schema for VoiceBroadcaster."""
    text: str = Field(..., description="Text to be converted into speech.")

class VoiceBroadcasterTool(BaseTool):
    name: str = "voice_financier"
    description: str = (
        "Converts text to speech using a professional finance voice."
    )
    args_schema: Type[BaseModel] = VoiceBroadcasterInput

    def _run(self, text: str) -> str:
        # Placeholder – use Piper, Coqui, or Bark API later
        return f"[AUDIO FILE GENERATED FROM TEXT]: {text}"