# crew.py

from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, task, crew
from crewai_tools import SerperDevTool, ScrapeWebsiteTool,WebsiteSearchTool
from tools.custom_tool import ConfidenceCheckerTool,MarketDataResearcherTool,FilingScraperTool,RetrieverTool,QuantitativeAnalystTool,LanguageNarratorTool,VoiceBroadcasterTool
import os
import os
import streamlit as st
from crewai.tasks.task_output import TaskOutput
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")

@CrewBase
class BuildingAMultiAgentFinanceAssistantWithVoiceInteractionCrew:
   
   @staticmethod
   def print_output(output: TaskOutput):
    """Streamlit-friendly callback to display full agent name and message in a styled collapsible box"""

    # Initialize chat history list if not present
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    # Save the new message
    st.session_state.chat_history.append({
        "agent": str(output.agent),
        "message": output.raw
    })

    # Clear and rebuild the container with full history
    if "chat_placeholder" not in st.session_state:
        st.session_state.chat_placeholder = st.empty()

    with st.session_state.chat_placeholder.container():
        # Construct all chat messages as one HTML block, ensuring proper closing of tags
        chat_blocks = []
        for chat in st.session_state.chat_history:
            block = f"""
            <div style="border: 1px solid #ccc; border-radius: 10px; padding: 1rem; margin: 1rem 0;
                        background-color: #f9f9f9; box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);">
                <div style="font-weight: bold; margin-bottom: 0.5rem; color: #444;">
                    👤 <span>{chat['agent']}</span>
                </div>
                <div style="white-space: pre-wrap; line-height: 1.6; color: #222;">
                    {chat['message']}
                </div>
            </div>
            """
            chat_blocks.append(block)

        full_chat_html = "\n".join(chat_blocks)

        # Final collapsible HTML
        st.markdown(f"""
        <details style="margin-top: 1rem;">
            <summary style="font-size: 1.1rem; font-weight: bold; cursor: pointer;">🗂️ Chat History</summary>
            {full_chat_html}
        </details>
        """, unsafe_allow_html=True)
    
    
    @agent
    def confidence_checker(self) -> Agent:
        return Agent(
            config=self.agents_config['confidence_checker'],
            tools=[ConfidenceCheckerTool()],
        )

    @agent
    def market_data_researcher(self) -> Agent:
        return Agent(
            config=self.agents_config['market_data_researcher'],
            tools=[MarketDataResearcherTool(), ScrapeWebsiteTool(), WebsiteSearchTool()],
        )

    @agent
    def filing_scraper(self) -> Agent:
        return Agent(
            config=self.agents_config['filing_scraper'],
            tools=[ScrapeWebsiteTool(), WebsiteSearchTool(), FilingScraperTool()],
        )

    @agent
    def retriever(self) -> Agent:
        return Agent(
            config=self.agents_config['retriever'],
            tools=[RetrieverTool()],
        )

    @agent
    def quant_analyst(self) -> Agent:
        return Agent(
            config=self.agents_config['quant_analyst'],
            tools=[QuantitativeAnalystTool(), ScrapeWebsiteTool(), WebsiteSearchTool()],
        )

    @agent
    def language_narrator(self) -> Agent:
        return Agent(
            config=self.agents_config['language_narrator'],
            tools=[LanguageNarratorTool()],
        )

    @agent
    def voice_financier(self) -> Agent:
        return Agent(
            config=self.agents_config['voice_financier'],
            tools=[VoiceBroadcasterTool()],
        )

    @task
    def evaluate_prompt_confidence(self) -> Task:
        return Task(
            config=self.tasks_config['check_prompt_task'],
            callback=self.print_output,
        )

    @task
    def poll_market_data(self) -> Task:
        return Task(
            config=self.tasks_config['market_data_task'],
            callback=self.print_output,
        )

    @task
    def scrape_financial_filings(self) -> Task:
        return Task(
            config=self.tasks_config['filing_scrape_task'],
            callback=self.print_output,
        )

    @task
    def retrieve_existing_knowledge(self) -> Task:
        return Task(
            config=self.tasks_config['retrieve_existing_knowledge_task'],
            callback=self.print_output,
        )

    @task
    def perform_quantitative_analysis(self) -> Task:
        return Task(
            config=self.tasks_config['quant_analysis_task'],
            callback=self.print_output,
        )

    @task
    def synthesize_narrative(self) -> Task:
        return Task(
            config=self.tasks_config['narrate_market_brief_task'],
            callback=self.print_output,
        )

    @task
    def deliver_voice_response(self) -> Task:
        return Task(
            config=self.tasks_config['broadcast_brief_task'],
            callback=self.print_output,
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

