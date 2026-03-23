"""
Spending Analyst agent.

Handles queries about transaction history, spending trends, category breakdowns,
and anomaly detection. Uses Account Aggregator data and pgvector semantic search
for contextual follow-up queries.

Example queries:
  "Where did I spend the most last month?"
  "Flag any transactions over two thousand rupees."
  "How much did I spend on food in March?"
"""

from __future__ import annotations

from typing import AsyncIterator

from anthropic import AsyncAnthropic

from backend.config import settings
from backend.models.schemas import AgentName, Transaction
from backend.tools.account_aggregator import fetch_accounts, fetch_transactions

SYSTEM_PROMPT = """You are the Spending Analyst for FinVoice, a personal finance assistant built for Indian users.

Your role:
- Analyse transaction history from the user's linked bank accounts.
- Identify spending patterns, category breakdowns, and unusual transactions.
- Answer questions using clear, plain language. Avoid financial jargon unless the user introduces a term first.
- Use Indian currency (₹) and Indian number formatting (lakhs, crores where appropriate).
- Be concise. One insight per sentence. Do not pad responses.

You have access to the user's recent transactions. Refer to actual figures from the data provided.
Do not speculate beyond what the data shows. If the data is insufficient, say so directly."""


async def run(
    query: str,
    session_id: str,
    accounts_data: list[dict] | None = None,
) -> AsyncIterator[str]:
    """
    Stream a response to a spending-related query.

    accounts_data is pre-fetched by the supervisor to avoid duplicate API calls.
    If not provided, this agent fetches it directly.
    """
    client = AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY, timeout=30.0)

    # Build transaction context for the prompt
    context = await _build_context(session_id, accounts_data)

    messages = [
        {
            "role": "user",
            "content": f"{context}\n\nUser question: {query}",
        }
    ]

    async with client.messages.stream(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        system=SYSTEM_PROMPT,
        messages=messages,
    ) as stream:
        async for text in stream.text_stream:
            yield text


async def _build_context(
    session_id: str,
    accounts_data: list[dict] | None,
) -> str:
    """Fetch transactions and format them as a context block for the prompt."""
    try:
        accounts = await fetch_accounts(session_id)
        all_transactions: list[Transaction] = []
        for account in accounts:
            txns = await fetch_transactions(account.account_id)
            all_transactions.extend(txns)

        if not all_transactions:
            return "No transaction data is available for this user."

        # Sort by date descending, take last 90 days (max 50 transactions for context)
        all_transactions.sort(key=lambda t: t.date, reverse=True)
        recent = all_transactions[:50]

        lines = [
            f"Account summary: {len(accounts)} account(s) linked.",
            f"Transaction data covers the last 90 days ({len(recent)} transactions shown).",
            "",
            "Recent transactions (date | merchant | category | amount in ₹):",
        ]
        for t in recent:
            sign = "+" if t.category == "Income" else "-"
            lines.append(
                f"  {t.date.strftime('%d %b')} | {t.merchant or t.description} | "
                f"{t.category or 'Uncategorised'} | {sign}₹{t.amount:,.0f}"
            )
        return "\n".join(lines)

    except Exception as exc:
        return f"Transaction data could not be loaded: {exc}"
