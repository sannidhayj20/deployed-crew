# crew.py

from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, task, crew
from crewai_tools import SerperDevTool, ScrapeWebsiteTool,WebsiteSearchTool
from tools.custom_tool import ConfidenceCheckerTool,MarketDataResearcherTool,FilingScraperTool,RetrieverTool,QuantitativeAnalystTool,LanguageNarratorTool,VoiceBroadcasterTool
import os
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")

@CrewBase
class BuildingAMultiAgentFinanceAssistantWithVoiceInteractionCrew:
    """Class to define the multi-agent finance assistant crew with voice interaction"""


    @agent
    def confidence_checker(self) -> Agent:
        return Agent(
            config=self.agents_config['confidence_checker'],
            tools=[ConfidenceCheckerTool()],  # Confidence tool is self-contained
        )

    @agent
    def market_data_researcher(self) -> Agent:
        return Agent(
            config=self.agents_config['market_data_researcher'],
            tools=[MarketDataResearcherTool(), ScrapeWebsiteTool(),WebsiteSearchTool()],  # Search + scrape for global stocks
        )

    @agent
    def filing_scraper(self) -> Agent:
        return Agent(
            config=self.agents_config['filing_scraper'],
            tools=[ScrapeWebsiteTool(),WebsiteSearchTool(),FilingScraperTool()],  # For IR portals and disclosures
        )

    @agent
    def retriever(self) -> Agent:
        return Agent(
            config=self.agents_config['retriever'],
            tools=[RetrieverTool()],  # Will use ChromaDB internally later
        )

    @agent
    def quant_analyst(self) -> Agent:
        return Agent(
            config=self.agents_config['quant_analyst'],
            tools=[QuantitativeAnalystTool(),ScrapeWebsiteTool(),WebsiteSearchTool()],  # Math/logic handled via LLM
        )

    @agent
    def language_narrator(self) -> Agent:
        return Agent(
            config=self.agents_config['language_narrator'],
            tools=[LanguageNarratorTool()],  # Uses LLM directly
        )

    @agent
    def voice_financier(self) -> Agent:
        return Agent(
            config=self.agents_config['voice_financier'],
            tools=[VoiceBroadcasterTool()],  # Placeholder for TTS integration
        )


    @task
    def evaluate_prompt_confidence(self) -> Task:
        return Task(
            config=self.tasks_config['check_prompt_task']
        )

    @task
    def poll_market_data(self) -> Task:
        return Task(
            config=self.tasks_config['market_data_task'],
        )

    @task
    def scrape_financial_filings(self) -> Task:
        return Task(
            config=self.tasks_config['filing_scrape_task'],
        )

    @task
    def retrieve_existing_knowledge(self) -> Task:
        return Task(
            config=self.tasks_config['retrieve_existing_knowledge_task'],
        )

    @task
    def perform_quantitative_analysis(self) -> Task:
        return Task(
            config=self.tasks_config['quant_analysis_task'],
        )

    @task
    def synthesize_narrative(self) -> Task:
        return Task(
            config=self.tasks_config['narrate_market_brief_task'],
        )

    @task
    def deliver_voice_response(self) -> Task:
        return Task(
            config=self.tasks_config['broadcast_brief_task'],
        )


    @crew
    def crew(self) -> Crew:
        """Creates the Finance Assistant crew with all agents and tasks"""
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
            memory=False,
        )
