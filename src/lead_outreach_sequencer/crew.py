import os

from crewai import LLM, Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai_tools import SerperDevTool

from lead_outreach_sequencer.tools.gmail_smtp_tool import GmailSMTPTool

# Detect local vs hosted Gmail path at import time.
# On CrewAI AMP: GMAIL_SMTP_PASSWORD is absent -> use apps=[...] integration.
# Locally:       GMAIL_SMTP_PASSWORD is present -> use GmailSMTPTool (smtplib).
_USE_SMTP = bool(os.environ.get("GMAIL_SMTP_PASSWORD", "").strip())

# Claude Sonnet via LiteLLM — better writing quality than gpt-4o-mini
_CLAUDE = LLM(model="anthropic/claude-sonnet-4-5-20250929")


@CrewBase
class LeadOutreachSequencerCrew:
    """
    hq0 Lead Outreach Sequencer.

    Two modes controlled by the `dry_run` input:
      dry_run=true  -> research + draft + preview (does NOT send)
      dry_run=false -> research + draft + send via Gmail (CC: ayush@sbl.so, team@sbl.so)

    Sender: Agnes Allison <hq0@sbl.so>
    Run with dry_run=true first to review. Re-run with dry_run=false to send.
    """

    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    @agent
    def lead_researcher(self) -> Agent:
        return Agent(
            config=self.agents_config["lead_researcher"],  # type: ignore[index]
            tools=[],
            reasoning=False,
            inject_date=True,
            allow_delegation=False,
            max_iter=10,
            llm=_CLAUDE,
        )

    @agent
    def personalized_outreach_specialist(self) -> Agent:
        return Agent(
            config=self.agents_config["personalized_outreach_specialist"],  # type: ignore[index]
            tools=[],
            reasoning=False,
            inject_date=True,
            allow_delegation=False,
            max_iter=10,
            llm=_CLAUDE,
        )

    @agent
    def email_dispatcher(self) -> Agent:
        if _USE_SMTP:
            # Local path: send via Gmail SMTP using App Password
            return Agent(
                config=self.agents_config["email_dispatcher"],  # type: ignore[index]
                tools=[GmailSMTPTool()],
                reasoning=False,
                inject_date=True,
                allow_delegation=False,
                max_iter=10,
                llm=_CLAUDE,
            )
        # Hosted path (CrewAI AMP): use google_gmail/send_email app integration
        return Agent(
            config=self.agents_config["email_dispatcher"],  # type: ignore[index]
            tools=[],
            reasoning=False,
            inject_date=True,
            allow_delegation=False,
            max_iter=10,
            apps=["google_gmail/send_email"],
            llm=_CLAUDE,
        )

    @task
    def research_lead_intelligence(self) -> Task:
        return Task(
            config=self.tasks_config["research_lead_intelligence"],  # type: ignore[index]
            markdown=False,
        )

    @task
    def draft_personalized_email(self) -> Task:
        return Task(
            config=self.tasks_config["draft_personalized_email"],  # type: ignore[index]
            markdown=False,
        )

    @task
    def send_email_via_gmail(self) -> Task:
        return Task(
            config=self.tasks_config["send_email_via_gmail"],  # type: ignore[index]
            markdown=False,
        )

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
            chat_llm=_CLAUDE,
        )
