"""
GmailSMTPTool — local Gmail send via smtplib + App Password.

Required env vars:
  GMAIL_SMTP_SENDER    — sender address, e.g. ayush@gmail.com
  GMAIL_SMTP_PASSWORD  — Google App Password (16-char, no spaces)
                         Get one at: myaccount.google.com → Security → App Passwords
  GMAIL_SMTP_FROM_NAME — display name, e.g. "Ayush Singh"  (optional, defaults to sender address)

This tool is only wired into the crew when GMAIL_SMTP_PASSWORD is present.
On CrewAI AMP the crew uses the google_gmail/send_email app integration instead.
"""
import os
import smtplib
from email.headerregistry import Address
from email.message import EmailMessage
from typing import Type

from crewai.tools import BaseTool
from pydantic import BaseModel, Field


class GmailSMTPInput(BaseModel):
    to_email: str = Field(..., description="Recipient email address")
    cc_email: str = Field(default="", description="CC email address (optional)")
    subject: str = Field(..., description="Email subject line")
    body: str = Field(..., description="Plain-text email body")


class GmailSMTPTool(BaseTool):
    name: str = "send_email_via_smtp"
    description: str = (
        "Send an email via Gmail SMTP using an App Password. "
        "Provide to_email, cc_email (optional), subject, and body. "
        "Returns a confirmation string on success or an error message on failure."
    )
    args_schema: Type[BaseModel] = GmailSMTPInput

    def _run(self, to_email: str, subject: str, body: str, cc_email: str = "") -> str:
        sender = os.environ.get("GMAIL_SMTP_SENDER", "").strip()
        password = os.environ.get("GMAIL_SMTP_PASSWORD", "").strip()
        from_name = os.environ.get("GMAIL_SMTP_FROM_NAME", sender).strip()

        if not sender:
            return "Error: GMAIL_SMTP_SENDER env var is not set."
        if not password:
            return "Error: GMAIL_SMTP_PASSWORD env var is not set."

        msg = EmailMessage()
        msg["Subject"] = subject
        msg["From"] = f"{from_name} <{sender}>"
        msg["To"] = to_email
        if cc_email:
            msg["Cc"] = cc_email
        msg.set_content(body)

        try:
            with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
                smtp.login(sender, password)
                recipients = [to_email] + ([cc_email] if cc_email else [])
                smtp.send_message(msg, to_addrs=recipients)
            cc_note = f", CC: {cc_email}" if cc_email else ""
            return (
                f"Email sent successfully. "
                f"To: {to_email}{cc_note}. Subject: \"{subject}\"."
            )
        except smtplib.SMTPAuthenticationError:
            return (
                "Error: Gmail authentication failed. "
                "Make sure GMAIL_SMTP_PASSWORD is a valid App Password "
                "(not your regular Gmail password). "
                "Generate one at myaccount.google.com → Security → App Passwords."
            )
        except smtplib.SMTPException as e:
            return f"Error sending email: {e}"
        except Exception as e:
            return f"Unexpected error: {e}"
