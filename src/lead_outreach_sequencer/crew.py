from crewai import LLM, Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai_tools import FirecrawlScrapeWebsiteTool, SerperDevTool


@CrewBase
class LeadOutreachSequencerCrew:
    """
    hq0 Lead Outreach Sequencer.

    Two modes controlled by the `dry_run` input:
      dry_run=true  → research + draft + preview (does NOT send)
      dry_run=false → research + draft + send via Gmail

    Run with dry_run=true first to review the email.
    If it looks good, re-run the same lead with dry_run=false to send.
    """

    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

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
    def send_email_via_gmail(self) -> Task:
        return Task(
            config=self.tasks_config["send_email_via_gmail"],
            markdown=False,
        )

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
            chat_llm=LLM(model="openai/gpt-4o-mini"),
        )
