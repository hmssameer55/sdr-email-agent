"""Send an email over SMTP (STARTTLS, port 587). Settings come from .env."""

import os
import smtplib
from email.message import EmailMessage

from dotenv import load_dotenv

load_dotenv(override=True)


def send_email(subject: str, text_body: str, html_body: str) -> None:
    sender = os.environ["EMAIL_ADDRESS"]
    recipient = os.getenv("EMAIL_TO") or sender  # defaults to emailing yourself

    msg = EmailMessage()
    msg["From"] = sender
    msg["To"] = recipient
    msg["Subject"] = subject
    msg.set_content(text_body)
    msg.add_alternative(html_body, subtype="html")

    with smtplib.SMTP(os.environ["EMAIL_SMTP_SERVER"], 587) as server:
        server.starttls()
        server.login(sender, os.environ["EMAIL_APP_PASSWORD"])
        server.send_message(msg)
