#!/usr/bin/env python
"""
Lead Outreach Sequencer — main entry point.

Required environment variables:
  OPENAI_API_KEY      — required by crewai even when using Anthropic (routing layer)
  ANTHROPIC_API_KEY   — for Claude Sonnet (used for all 3 agents)
  SERPER_API_KEY      — kept for potential future use (not used in current pipeline)

Local Gmail sending (optional — only needed when running locally):
  GMAIL_SMTP_SENDER    — your Gmail address, e.g. hq0@sbl.so
  GMAIL_SMTP_PASSWORD  — Google App Password (16 chars, no spaces)
                         Generate at: myaccount.google.com -> Security -> App Passwords
  GMAIL_SMTP_FROM_NAME — display name shown to recipients (e.g. "Agnes Allison")

  When GMAIL_SMTP_PASSWORD is set the crew uses smtplib directly.
  When absent (e.g. on CrewAI AMP) the crew uses the google_gmail/send_email app.

Input fields per lead:
  lead_name           — first name
  lead_email          — email address
  company_name        — company name
  lead_headline       — LinkedIn headline
  lead_location       — location string
  recent_posts        — summary of recent LinkedIn posts
  conversation_history — full LinkedIn conversation text
  sender_name         — always "Agnes Allison" for this campaign
  colleague_name      — name of the person who did the LinkedIn outreach (from JSON senderName)
  dry_run             — "true" = preview only, "false" = actually send

Batch runner reads the campaign JSON export format from the hq0 LinkedIn campaign tool.
"""
import json
import sys
from pathlib import Path

from lead_outreach_sequencer.crew import LeadOutreachSequencerCrew


def _lead_from_json(record: dict) -> dict:
    """Convert a campaign JSON record to a crew inputs dict."""
    pd = record["linkedinDetails"]["profileDetails"]
    first_name = pd.get("first_name", record["userName"].split()[0])
    emails = pd.get("contact_info", {}).get("emails", [])
    email = emails[0] if emails else ""

    work = pd.get("work_experience", [])
    company = work[0].get("company", "") if work else ""

    recent_posts = record["linkedinDetails"].get("info", {}).get("value", "")

    # Colleague = the name on AI-sent messages in the conversation
    ai_msgs = [m for m in record.get("messages", []) if m.get("senderType") == "AI"]
    colleague_name = ai_msgs[0]["senderName"] if ai_msgs else "Smeha"

    # Build plain conversation string, skip empty messages
    convo_lines = []
    for m in record.get("messages", []):
        if not m.get("message", "").strip():
            continue
        role = m["senderName"] if m["senderType"] == "AI" else first_name
        convo_lines.append(f"{role}: {m['message']}")
    conversation = "\n".join(convo_lines)

    return {
        "lead_name": first_name,
        "lead_email": email,
        "company_name": company,
        "lead_headline": pd.get("headline", ""),
        "lead_location": pd.get("location", ""),
        "recent_posts": recent_posts,
        "conversation_history": conversation,
        "sender_name": "Agnes Allison",
        "colleague_name": colleague_name,
        "dry_run": "true",  # always preview by default — pass dry_run=false to send
    }


# Sample lead for crewai run / crewai test
SAMPLE_LEAD = {
    "lead_name": "Sheldon",
    "lead_email": "sheldon@example.com",
    "company_name": "ReboundTAG",
    "lead_headline": "Co-Founder at ReboundTAG | Helping brands track lost items",
    "lead_location": "United States",
    "recent_posts": "Recently posted about product launch momentum and B2B client growth.",
    "conversation_history": (
        "Rohan (Mar 31): hey Sheldon - thanks for connecting :) Would it be cool if I shared "
        "a free tool that helps companies brand their meeting links instead of using generic Zoom ones?\n"
        "Sheldon (Mar 31): What does this cost?\n"
        "Rohan (Mar 31): hq0 lets you run meetings on your own domain instead of zoom or google meet "
        "links. so it's like meet.yourcompany.com, with your logo and colors. free to start. hq0.com\n"
        "Sheldon (Mar 31): 👍\n"
        "Rohan (Apr 2): If you'd like, I can set up an HQ0 room tied to your brand and share a "
        "preview link so you can try it with one client. Want me to create one for you?\n"
        "Sheldon (Apr 2): Sure"
    ),
    "sender_name": "Agnes Allison",
    "colleague_name": "Rohan",
    "dry_run": "true",
}


def run():
    """Run the crew for the sample lead (dry_run=true — previews only)."""
    LeadOutreachSequencerCrew().crew().kickoff(inputs=SAMPLE_LEAD)


def run_lead(lead: dict):
    """Run the crew for a single lead dict (already in crew input format)."""
    LeadOutreachSequencerCrew().crew().kickoff(inputs=lead)


def run_batch(leads_file: str, batch_size: int = 10, dry_run: str = "true"):
    """
    Process leads from a campaign JSON export file.

    Reads the hq0 campaign export format (list of records with messages +
    linkedinDetails). Skips leads with no email. Processes sequentially.

    Usage:
        python -m lead_outreach_sequencer.main batch campaign.json
        python -m lead_outreach_sequencer.main batch campaign.json 5
        python -m lead_outreach_sequencer.main batch campaign.json 5 false
    """
    leads_path = Path(leads_file)
    if not leads_path.exists():
        print(f"Error: file not found: {leads_file}")
        sys.exit(1)

    with open(leads_path) as f:
        raw = json.load(f)

    if not isinstance(raw, list):
        print("Error: JSON must be a list of lead records.")
        sys.exit(1)

    # Convert to crew inputs, skip records with no email
    leads = []
    skipped = 0
    for record in raw:
        inp = _lead_from_json(record)
        if not inp["lead_email"]:
            skipped += 1
            continue
        inp["dry_run"] = dry_run
        leads.append(inp)

    batch = leads[:batch_size]
    total = len(batch)
    print(f"\nBatch: {total} lead(s) | dry_run={dry_run} | skipped (no email): {skipped}")
    print("=" * 65)

    results = []
    for i, lead in enumerate(batch, start=1):
        print(f"\n[{i}/{total}] {lead['lead_name']} ({lead['company_name']}) -> {lead['lead_email']}")
        print("-" * 65)
        try:
            result = LeadOutreachSequencerCrew().crew().kickoff(inputs=lead)
            results.append({
                "lead": lead["lead_name"],
                "email": lead["lead_email"],
                "status": "ok",
                "output": str(result),
            })
        except Exception as e:
            print(f"  Error: {e}")
            results.append({
                "lead": lead["lead_name"],
                "email": lead["lead_email"],
                "status": "error",
                "output": str(e),
            })

    print("\n" + "=" * 65)
    print("BATCH DONE")
    print("=" * 65)
    for r in results:
        icon = "v" if r["status"] == "ok" else "x"
        print(f"  [{icon}] {r['lead']} <{r['email']}>")

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
        print("  run                              -- run crew for sample lead (dry_run=true)")
        print("  batch <file.json> [n] [dry_run]  -- process campaign export (default: n=10, dry_run=true)")
        print("  train <n> <file>                 -- train crew")
        print("  replay <task_id>                 -- replay from task")
        print("  test <n> <model>                 -- test crew")
        sys.exit(1)

    command = sys.argv[1]
    if command == "run":
        run()
    elif command == "batch":
        if len(sys.argv) < 3:
            print("Usage: main.py batch <file.json> [batch_size] [dry_run]")
            sys.exit(1)
        n = int(sys.argv[3]) if len(sys.argv) > 3 else 10
        dr = sys.argv[4] if len(sys.argv) > 4 else "true"
        run_batch(sys.argv[2], batch_size=n, dry_run=dr)
    elif command == "train":
        train()
    elif command == "replay":
        replay()
    elif command == "test":
        test()
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)
