import smtplib
from email.message import EmailMessage

import httpx

from app.core.config import Settings


class AlertService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    async def send_gate_failure(self, title: str, details: list[str]) -> None:
        lines = "\n".join(f"- {reason}" for reason in details)
        message = f"{title}\n{lines}" if lines else title

        if self.settings.slack_webhook_url:
            await self._send_slack(message)
        if self._email_enabled():
            self._send_email(subject=title, body=message)

    async def _send_slack(self, text: str) -> None:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.post(self.settings.slack_webhook_url, json={"text": text})
            response.raise_for_status()

    def _email_enabled(self) -> bool:
        return bool(
            self.settings.smtp_host
            and self.settings.smtp_username
            and self.settings.smtp_password
            and self.settings.smtp_from_email
            and self.settings.alert_recipient_list
        )

    def _send_email(self, subject: str, body: str) -> None:
        msg = EmailMessage()
        msg["Subject"] = subject
        msg["From"] = self.settings.smtp_from_email
        msg["To"] = ", ".join(self.settings.alert_recipient_list)
        msg.set_content(body)

        with smtplib.SMTP(self.settings.smtp_host, self.settings.smtp_port, timeout=10) as server:
            server.starttls()
            server.login(self.settings.smtp_username, self.settings.smtp_password)
            server.send_message(msg)
