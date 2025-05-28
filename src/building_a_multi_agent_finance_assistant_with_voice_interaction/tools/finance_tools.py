from langchain.tools import tool
from langchain_openai import OpenAI
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import OpenAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.document_loaders import TextLoader
import yfinance as yf
import os
import json
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin


CHROMA_PATH = "./chroma"
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
llm = OpenAI(temperature=0, openai_api_key=OPENAI_API_KEY)


class FinanceTools:

    @tool("Prompt Confidence Checker")
    def confidence_checker(query):
        """
        Checks if the query is clear and has historical context in vector DB.
        Returns confidence score and whether to route to data agents.
        """
        print("🔍 Assessing prompt clarity and similarity...")
        embeddings = OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY)
        vectordb = Chroma(persist_directory=CHROMA_PATH, embedding_function=embeddings)

        # Clarity scoring via LLM
        clarity_prompt = (
            f"Rate this query on clarity and specificity from 1-10:\n{query}\n"
            "Respond only with the number."
        )
        clarity_score = float(llm.invoke(clarity_prompt).strip()) / 10

        # Similarity check
        results = vectordb.similarity_search_with_score(query, k=1)
        similarity_score = round(results[0][1], 2) if results else 0.0

        return json.dumps({
            "confidence_score": round(clarity_score, 2),
            "similarity_score": similarity_score,
            "route_to_data_agents": similarity_score < 0.7
        })

    @tool("Global Market Data Researcher")
    def market_data_researcher(query):
        """
        Extracts companies or tickers mentioned in the query and returns real-time financial data.
        Works for global tickers like INFY.NS, 005930.KS, HSBA.L, etc.
        Automatically indexes new findings into ChromaDB.
        """
        print("📈 Fetching live market data...")
        extraction_prompt = (
            f"Extract company names or tickers related to this query:\n{query}\n"
            "Respond only with comma-separated symbols or names."
        )
        response = llm.invoke(extraction_prompt)
        entities = [e.strip() for e in response.strip().split(",")]

        if not entities or entities == ["None"]:
            return json.dumps({"error": "No valid tickers or companies identified."})

        results = []
        for entity in entities:
            try:
                ticker = entity if "." in entity or "-" in entity else yf.Ticker(entity).info['symbol']
                info = yf.Ticker(ticker).info
                history = yf.Ticker(ticker).history(period="1d")

                if history.empty:
                    continue

                current_price = round(history["Close"].iloc[-1], 2)
                previous_close = round(history["Open"].iloc[0], 2)
                change_percent = round(((current_price - previous_close) / previous_close) * 100, 2)
                volume = int(history["Volume"].iloc[-1])
                eps = info.get("epsTrailingTwelveMonths")
                market_cap = info.get("marketCap")

                result = {
                    "ticker": ticker,
                    "name": info.get("shortName", ticker),
                    "price": current_price,
                    "change_percent": change_percent,
                    "previous_close": previous_close,
                    "volume": volume,
                    "eps_trailing_12m": eps,
                    "market_cap": market_cap
                }

                results.append(result)

                # Index into ChromaDB
                FinanceTools._index_into_chroma(json.dumps(result))

            except Exception as e:
                print(f"Error fetching data for {entity}: {str(e)}")

        return json.dumps(results, indent=2)

    @tool("SEC & Global Filing Scraper")
    def filing_scraper(query):
        """
        Scrapes recent earnings reports and SEC filings based on query.
        Supports international IR portals. Automatically indexes findings into ChromaDB.
        """
        print("📄 Searching for recent filings...")
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

                    result = {
                        "company": entity,
                        "source": relevant_links[0],
                        "summary": summary
                    }
                    results.append(result)

                    # Index into ChromaDB
                    FinanceTools._index_into_chroma(json.dumps(result))

            except Exception as e:
                print(f"Error processing {entity}: {str(e)}")

        return json.dumps(results, indent=2)

    @tool("Knowledge Retriever")
    def retriever_tool(query):
        """
        Retrieves top-k relevant documents from the vector database.
        """
        print("🧠 Retrieving past insights from vector DB...")
        embeddings = OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY)
        vectordb = Chroma(persist_directory=CHROMA_PATH, embedding_function=embeddings)
        docs = vectordb.similarity_search(query, k=3)

        matches = [{"content": doc.page_content, "similarity": round(vectordb._similarity_search_with_relevance_scores(query, k=3)[0][1], 2)} for doc in docs]
        return json.dumps(matches, indent=2)

    @tool("Quantitative Analyst")
    def quant_analyst(query):
        """
        Analyzes portfolio risk, allocation changes, and earnings surprises.
        """
        print("📊 Performing quantitative analysis...")
        analysis_prompt = (
            "Given the following query:\n"
            f"{query}\n"
            "Analyze and summarize:\n"
            "- Allocation delta\n- Earnings surprises\n- Risk exposure\n"
            "- Regional sentiment\n"
            "Return structured JSON output."
        )
        response = llm.invoke(analysis_prompt)
        return response.strip()

    @tool("Narrative Generator")
    def language_narrator(query):
        """
        Generates a spoken narrative based on analysis and context.
        """
        print("✍️ Writing market briefing...")
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

    @tool("Voice Broadcaster")
    def voice_financier(text):
        """
        Converts text to speech using a professional finance voice.
        Placeholder until full TTS integration.
        """
        print("🎙️ Converting to audio...")
        return f"[AUDIO FILE GENERATED FROM TEXT]: {text}"

    # ——— HELPER METHODS ———

    @staticmethod
    def _index_into_chroma(content: str):
        """Adds new document chunk to ChromaDB"""
        embeddings = OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY)
        vectordb = Chroma(persist_directory=CHROMA_PATH, embedding_function=embeddings)
        from langchain.schema import Document
        doc = Document(page_content=content, metadata={"source": "auto_indexed"})
        vectordb.add_documents([doc])
        vectordb.persist()