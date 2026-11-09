"""
SDR email agent: three AI sales writers draft a cold email, a manager picks the best
and emails it to you over SMTP.

Flow (OpenAI Agents SDK):
    Sales Manager ──calls as tools──▶ 3 writer agents (professional, witty, concise)
          │
          └──picks the best──▶ send_email tool ──▶ your inbox

Run:
    python sdr_agent.py            # drafts, picks, and sends a real email
    python sdr_agent.py --dry-run  # same flow, prints the email instead of sending it
"""

import argparse
import asyncio
import os

from dotenv import load_dotenv
from openai import AsyncOpenAI
from agents import (
    Agent,
    OpenAIChatCompletionsModel,
    Runner,
    function_tool,
    set_tracing_disabled,
    set_tracing_export_api_key,
    trace,
)

from messenger import send_email

load_dotenv(override=True)

# ---------------------------------------------------------------------------
# Model: any OpenAI-compatible endpoint (Groq by default; swap via .env)
# ---------------------------------------------------------------------------
client = AsyncOpenAI(
    base_url=os.getenv("MODEL_BASE_URL", "https://api.groq.com/openai/v1"),
    api_key=os.environ["MODEL_API_KEY"],
)
model = OpenAIChatCompletionsModel(
    model=os.getenv("MODEL_NAME", "openai/gpt-oss-120b"),
    openai_client=client,
)

# Traces upload to platform.openai.com/traces and need an OpenAI key, even when
# another provider runs the model. Without one, switch tracing off.
if os.getenv("OPENAI_API_KEY"):
    set_tracing_export_api_key(os.environ["OPENAI_API_KEY"])
else:
    set_tracing_disabled(True)

DRY_RUN = False

# ---------------------------------------------------------------------------
# Three writers: same model, different personalities
# ---------------------------------------------------------------------------
COMPANY = """
You are a sales agent working for ComplAI,
a company that provides a SaaS tool for ensuring SOC2 compliance and preparing for audits, powered by AI.
You write emails.
"""

writers = [
    Agent(name="Professional Writer", model=model,
          instructions=COMPANY + "Your email style is professional, serious, with gravitas and credibility."),
    Agent(name="Witty Writer", model=model,
          instructions=COMPANY + "Your email style is witty, engaging, and humorous."),
    Agent(name="Concise Writer", model=model,
          instructions=COMPANY + "Your email style is concise, to the point, in the style of a busy senior executive."),
]

writer_tools = [
    agent.as_tool(
        tool_name=f"sales_email_writer_{i}",
        tool_description="Use this tool to write a sales email. In the input, just instruct it to write a sales email.",
    )
    for i, agent in enumerate(writers, start=1)
]

# ---------------------------------------------------------------------------
# Email tool
# ---------------------------------------------------------------------------
@function_tool
def send_email_tool(subject: str, text_body: str, html_body: str) -> str:
    """
    Send out an email with the given subject and body to all sales prospects

    Args:
        subject: The subject of the email
        text_body: The body of the email as plain text
        html_body: The HTML body of the email
    """
    if DRY_RUN:
        print(f"\n--- DRY RUN: email not sent ---\nSubject: {subject}\n\n{text_body}\n-------------------------------\n")
        return "Dry run: email printed, not sent"
    send_email(subject, text_body, html_body)
    return "Email sent successfully"


# ---------------------------------------------------------------------------
# Manager: gathers drafts via the writer tools, picks one, sends it
# ---------------------------------------------------------------------------
# No handoff here: the SDK's handoff tool has an empty parameter schema that Groq
# rejects ("'required' present but 'properties' is missing"). DeepSeek accepts it.
sales_manager = Agent(
    name="Sales Manager",
    model=model,
    instructions="You are a Sales Manager at ComplAI. Your goal is to find the single best cold sales email using the sales_email_writer tools.",
    tools=writer_tools + [send_email_tool],
)

TASK = """
Follow these steps:

1. Generate Drafts: Use each of the three sales_email_writer tools to generate different email drafts.
Just instruct each to write a sales email; no further details are needed.
Do not proceed until all three drafts are ready, one from each tool.

2. Evaluate and Select: Review the drafts and choose the single best email,
imagining you are a customer and picking the one you'd most likely respond to.

3. Use your send_email_tool to send the best email (and only the best email). Only send 1 email.
"""


async def main() -> None:
    with trace("SDR email agent"):
        result = await Runner.run(sales_manager, TASK)
    print(result.final_output)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Draft, pick and send a cold sales email.")
    parser.add_argument("--dry-run", action="store_true", help="print the chosen email instead of sending it")
    DRY_RUN = parser.parse_args().dry_run
    asyncio.run(main())
