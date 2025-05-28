from crewai_tools import tool
from langchain_community.embeddings import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAI
import json
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

CHROMA_PATH = "./chroma"

@tool("confidence_and_similarity_check")
def check_prompt_confidence_and_similarity(query: str) -> str:
    """
    Checks the clarity of the query using an LLM and finds semantic similarity
    in the Chroma vector DB. Returns a confidence score and similarity score.
    """

    # Get OpenAI API key from environment
    openai_api_key = os.getenv("OPENAI_API_KEY")
    if not openai_api_key:
        raise EnvironmentError("Missing OPENAI_API_KEY in environment.")

    # 1. Load vector store
    embedding_model = OpenAIEmbeddings(openai_api_key=openai_api_key)
    vectordb = Chroma(
        persist_directory=CHROMA_PATH,
        embedding_function=embedding_model
    )

    # 2. Semantic similarity search
    results = vectordb.similarity_search_with_score(query, k=1)
    if results:
        _, similarity_score = results[0]
    else:
        similarity_score = 0.0

    # 3. LLM-based prompt clarity scoring
    llm = OpenAI(temperature=0, openai_api_key=openai_api_key)
    clarity_prompt = (
        f"Rate the clarity and specificity of the following market query on a scale from 1 to 10:\n"
        f"{query}\n"
        "Respond with a single number only."
    )
    response = llm.invoke(clarity_prompt)
    try:
        confidence_score = float(response.strip()) / 10.0
    except ValueError:
        confidence_score = 0.5

    # 4. Routing logic
    route_to_data_agents = confidence_score > 0.6 or similarity_score > 0.7

    return json.dumps({
        "confidence_score": round(confidence_score, 2),
        "similarity_score": round(similarity_score, 2),
        "route_to_data_agents": route_to_data_agents
    })