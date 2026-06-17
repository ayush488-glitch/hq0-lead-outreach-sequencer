#!/usr/bin/env python
"""
Lead Outreach Sequencer — main entry point.

Required environment variables:
  OPENAI_API_KEY      — for GPT-4o-mini
  SERPER_API_KEY      — for Google search via SerperDevTool
  FIRECRAWL_API_KEY   — for website scraping via FirecrawlScrapeWebsiteTool
  (Gmail OAuth handled automatically by CrewAI apps integration)

Input fields per lead:
  lead_name           — first name of the lead
  lead_email          — their email address
  company_name        — their company name
  company_website     — their company website URL (used for Firecrawl scraping)
  conversation_history — the full LinkedIn conversation text
  sender_name         — name of the person sending this email (e.g. "Ayush")
  colleague_name      — name who had the original LinkedIn conversation (e.g. "Rohan")
"""
import json
import sys
from pathlib import Path

from lead_outreach_sequencer.crew import LeadOutreachSequencerCrew

# Sample lead — replace with real data when running
SAMPLE_LEAD = {
    "lead_name": "Sheldon",
    "lead_email": "sheldon@example.com",
    "company_name": "ReboundTAG",
    "company_website": "https://reboundtag.com",
    "conversation_history": (
        "Rohan (Mar 31): hey Sheldon - thanks for connecting :) Would it be cool if I shared "
        "a free tool that helps companies brand their meeting links instead of using generic Zoom ones?\n"
        "Sheldon (Mar 31): What does this cost?\n"
        "Rohan (Mar 31): hey, hq0 lets you run meetings on your own domain instead of zoom or google meet "
        "links. so it's like meet.yourcompany.com, with your logo and colors. makes calls look way more "
        "polished. free to start (no credit card). paid plans if you want more later. here's the link: hq0.com\n"
        "Sheldon (Mar 31): 👍\n"
        "Rohan (Apr 2): Loved your recent posts about ReboundTAG - great visibility. If you'd like, I can "
        "set up an HQ0 room tied to your brand and share a preview link so you can try it with one client; "
        "I'll handle the setup. Want me to create one for you?\n"
        "Sheldon (Apr 2): Sure"
    ),
    "sender_name": "Ayush",
    "colleague_name": "Rohan",
}


def run():
    """Run the crew for a single lead (uses SAMPLE_LEAD)."""
    LeadOutreachSequencerCrew().crew().kickoff(inputs=SAMPLE_LEAD)


def run_lead(lead: dict):
    """Run the crew for a single lead dict."""
    LeadOutreachSequencerCrew().crew().kickoff(inputs=lead)


def run_batch(leads_file: str, batch_size: int = 10):
    """
    Process leads from a JSON file in batches.

    The JSON file should contain a list of lead objects, each with the fields
    described in the module docstring. Leads are processed sequentially — for each
    lead the crew runs all 4 steps: research → draft → human review (pause) → send.
    The human reviewer approves or rejects each draft in the CrewAI dashboard.

    Usage:
        python -m lead_outreach_sequencer.main batch leads.json
        python -m lead_outreach_sequencer.main batch leads.json 5   # process only 5 leads
    """
    leads_path = Path(leads_file)
    if not leads_path.exists():
        print(f"Error: leads file not found: {leads_file}")
        sys.exit(1)

    with open(leads_path) as f:
        all_leads = json.load(f)

    if not isinstance(all_leads, list):
        print("Error: leads file must be a JSON array of lead objects.")
        sys.exit(1)

    batch = all_leads[:batch_size]
    total = len(batch)
    print(f"\nStarting batch run: {total} lead(s) from {leads_file}")
    print("=" * 60)

    results = []
    for i, lead in enumerate(batch, start=1):
        print(f"\n[{i}/{total}] Processing: {lead.get('lead_name', 'Unknown')} "
              f"({lead.get('company_name', '')})")
        print("-" * 60)
        try:
            result = LeadOutreachSequencerCrew().crew().kickoff(inputs=lead)
            results.append({
                "lead": lead.get("lead_name"),
                "email": lead.get("lead_email"),
                "status": "processed",
                "output": str(result),
            })
        except Exception as e:
            print(f"  Error processing {lead.get('lead_name')}: {e}")
            results.append({
                "lead": lead.get("lead_name"),
                "email": lead.get("lead_email"),
                "status": "error",
                "output": str(e),
            })

    print("\n" + "=" * 60)
    print("BATCH COMPLETE")
    print("=" * 60)
    for r in results:
        status_icon = "✓" if r["status"] == "processed" else "✗"
        print(f"  {status_icon} {r['lead']} ({r['email']})")

    return results


def train():
    """Train the crew for a given number of iterations."""
    try:
        LeadOutreachSequencerCrew().crew().train(
            n_iterations=int(sys.argv[2]),
            filename=sys.argv[3],
            inputs=SAMPLE_LEAD,
        )
    except Exception as e:
        raise Exception(f"An error occurred while training the crew: {e}")


def replay():
    """Replay the crew execution from a specific task."""
    try:
        LeadOutreachSequencerCrew().crew().replay(task_id=sys.argv[2])
    except Exception as e:
        raise Exception(f"An error occurred while replaying the crew: {e}")


def test():
    """Test the crew execution and return results."""
    try:
        LeadOutreachSequencerCrew().crew().test(
            n_iterations=int(sys.argv[2]),
            openai_model_name=sys.argv[3],
            inputs=SAMPLE_LEAD,
        )
    except Exception as e:
        raise Exception(f"An error occurred while testing the crew: {e}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: main.py <command> [args]")
        print("Commands:")
        print("  run                        — run crew for sample lead")
        print("  batch <leads.json> [n]     — process batch of leads from JSON file")
        print("  train <n> <file>           — train crew")
        print("  replay <task_id>           — replay from task")
        print("  test <n> <model>           — test crew")
        sys.exit(1)

    command = sys.argv[1]
    if command == "run":
        run()
    elif command == "batch":
        if len(sys.argv) < 3:
            print("Usage: main.py batch <leads.json> [batch_size]")
            sys.exit(1)
        size = int(sys.argv[3]) if len(sys.argv) > 3 else 10
        run_batch(sys.argv[2], batch_size=size)
    elif command == "train":
        train()
    elif command == "replay":
        replay()
    elif command == "test":
        test()
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)
