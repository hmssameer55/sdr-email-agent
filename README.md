# SDR Email Agent

A small multi-agent system built with the [OpenAI Agents SDK](https://openai.github.io/openai-agents-python/).
Three AI sales writers each draft a cold email, and a manager agent picks the best one
and emails it over SMTP.

```
Sales Manager ──calls as tools──▶ Professional / Witty / Concise writers
      │
      └──picks the best──▶ send_email tool ──▶ inbox
```

## What it shows

- **Agents as tools:** the manager calls each writer, gets the draft back, and stays in charge.
- **Function tools:** `@function_tool` turns a plain Python function (send an email) into a tool the LLM can call.
- **LLM-driven orchestration:** the manager plans the steps itself (draft three times, compare, send once). No hard-coded order.
- **Any model:** it works with any OpenAI-compatible endpoint (Groq, DeepSeek, OpenRouter, Ollama…) by changing three env vars.

> **Why no handoff?** The course version hands off to a separate "sender" agent. Groq
> rejects the SDK's handoff tool schema (`'required' present but 'properties' is missing`),
> so here the manager sends the email itself. On DeepSeek, handoffs work.

## Run it

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # then fill it in
python sdr_agent.py --dry-run   # prints the chosen email, sends nothing
python sdr_agent.py             # sends it for real
```

By default the email goes to your own address (`EMAIL_ADDRESS`). For Gmail, use an
[App Password](https://support.google.com/accounts/answer/185833), not your account password.

## Credits

Based on the Week 2 SDR lab from Ed Donner's
[AI Engineer Agentic Track](https://github.com/ed-donner/agents) course (MIT License),
rewritten as a standalone script with configurable models and a dry-run mode.
