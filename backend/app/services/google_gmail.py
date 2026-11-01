"""Send emails via the Gmail API using OAuth credentials."""

import asyncio
import base64
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from googleapiclient.discovery import build

from app.services.google_auth import get_credentials


async def send_email(to: str, subject: str, html_body: str) -> bool:
    creds = get_credentials()
    if not creds:
        return False

    def _send() -> None:
        from app.services.google_auth import get_user_email  # avoid circular at module level

        service = build("gmail", "v1", credentials=creds, cache_discovery=False)
        msg = MIMEMultipart("alternative")
        sender = get_user_email() or "me"
        msg["From"] = sender
        msg["To"] = to
        msg["Subject"] = subject
        msg.attach(MIMEText(html_body, "html"))
        raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
        service.users().messages().send(userId="me", body={"raw": raw}).execute()

    await asyncio.to_thread(_send)
    return True


def build_scheduling_email_html(
    candidate_name: str,
    job_title: str,
    scheduling_url: str,
) -> str:
    return f"""\
<html>
<body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; color: #1a1a2e; max-width: 560px; margin: 0 auto; padding: 24px;">
  <h2 style="color: #1a1a2e; margin-bottom: 4px;">Interview Scheduling</h2>
  <p style="color: #64748b; margin-top: 0;">HirePilot AI</p>
  <hr style="border: none; border-top: 1px solid #e2e8f0; margin: 20px 0;" />
  <p>Hi {candidate_name},</p>
  <p>
    We'd like to schedule an interview with you for the
    <strong>{job_title}</strong> position.
  </p>
  <p>Please select a time slot that works best for you:</p>
  <p style="text-align: center; margin: 28px 0;">
    <a href="{scheduling_url}"
       style="display: inline-block; background: #3b82f6; color: #fff;
              padding: 12px 32px; border-radius: 8px; text-decoration: none;
              font-weight: 600; font-size: 15px;">
      Choose Your Time Slot
    </a>
  </p>
  <p style="color: #64748b; font-size: 13px;">
    If the button doesn't work, copy and paste this link into your browser:<br/>
    <a href="{scheduling_url}" style="color: #3b82f6;">{scheduling_url}</a>
  </p>
  <hr style="border: none; border-top: 1px solid #e2e8f0; margin: 24px 0;" />
  <p style="color: #94a3b8; font-size: 12px;">
    This is an automated email from HirePilot AI. Please do not reply directly.
  </p>
</body>
</html>"""
