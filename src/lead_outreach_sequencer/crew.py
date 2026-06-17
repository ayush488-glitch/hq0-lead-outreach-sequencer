from crewai import LLM, Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai_tools import FirecrawlScrapeWebsiteTool, SerperDevTool


# ─────────────────────────────────────────────────────────
# CREW 1: Draft Crew
# Run this first. The final output is the ready-to-send
# email draft. Review it in the CrewAI dashboard.
# If it looks good, copy it and trigger Send Crew.
# ─────────────────────────────────────────────────────────
@CrewBase
class DraftCrew:
    """Researches the lead and drafts a personalized email."""

    agents_config = "config/draft/agents.yaml"
    tasks_config = "config/draft/tasks.yaml"

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

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
            chat_llm=LLM(model="openai/gpt-4o-mini"),
        )


# ─────────────────────────────────────────────────────────
# CREW 2: Send Crew
# Run this AFTER reviewing and approving the draft.
# Required inputs:
#   lead_email     — recipient email
#   approved_email — copy-paste the full email from Draft Crew output
# ─────────────────────────────────────────────────────────
@CrewBase
class SendCrew:
    """Sends a pre-approved email draft via Gmail."""

    agents_config = "config/send/agents.yaml"
    tasks_config = "config/send/tasks.yaml"

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


# Alias for backward compatibility
LeadOutreachSequencerCrew = DraftCrew
