import os

from crewai import LLM, Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai_tools import FirecrawlScrapeWebsiteTool, SerperDevTool


@CrewBase
class LeadOutreachSequencerCrew:
    """LeadOutreachSequencer crew"""

    @agent
    def lead_researcher(self) -> Agent:
        return Agent(
            config=self.agents_config["lead_researcher"],
            tools=[
                SerperDevTool(),
                FirecrawlScrapeWebsiteTool(),
            ],
            reasoning=False,
            inject_date=True,
            allow_delegation=False,
            max_iter=25,
            llm=LLM(model="openai/gpt-4o-mini"),
        )

    @agent
    def personalized_outreach_specialist(self) -> Agent:
        return Agent(
            config=self.agents_config["personalized_outreach_specialist"],
            tools=[],
            reasoning=False,
            inject_date=True,
            allow_delegation=False,
            max_iter=25,
            llm=LLM(model="openai/gpt-4o-mini"),
        )

    @agent
    def approval_coordinator(self) -> Agent:
        return Agent(
            config=self.agents_config["approval_coordinator"],
            tools=[],
            reasoning=False,
            allow_delegation=False,
            max_iter=5,
            llm=LLM(model="openai/gpt-4o-mini"),
        )

    @agent
    def email_dispatcher(self) -> Agent:
        return Agent(
            config=self.agents_config["email_dispatcher"],
            tools=[],
            reasoning=False,
            inject_date=True,
            allow_delegation=False,
            max_iter=10,
            apps=["google_gmail/send_email"],
            llm=LLM(model="openai/gpt-4o-mini"),
        )

    @task
    def research_lead_intelligence(self) -> Task:
        return Task(
            config=self.tasks_config["research_lead_intelligence"],
            markdown=False,
        )

    @task
    def draft_personalized_email(self) -> Task:
        return Task(
            config=self.tasks_config["draft_personalized_email"],
            markdown=False,
        )

    @task
    def review_and_approve_email(self) -> Task:
        return Task(
            config=self.tasks_config["review_and_approve_email"],
            human_input=True,
            markdown=False,
        )

    @task
    def send_email_via_gmail(self) -> Task:
        return Task(
            config=self.tasks_config["send_email_via_gmail"],
            markdown=False,
        )

    @crew
    def crew(self) -> Crew:
        """Creates the LeadOutreachSequencer crew"""
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
            chat_llm=LLM(model="openai/gpt-4o-mini"),
        )
