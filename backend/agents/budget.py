"""
Budget Planner agent.

Handles queries about monthly cash flow, savings goals, and spending projections.
Designed for variable-income earners (freelancers, gig economy workers) where
a fixed monthly budget is not the right frame.

Example queries:
  "Am I on track this month?"
  "How much can I save if I cut dining out by half?"
  "What would my savings look like if I invested ₹5,000 more per month in SIPs?"
"""

from __future__ import annotations

from typing import AsyncIterator

from anthropic import AsyncAnthropic

from backend.config import settings
from backend.models.schemas import Transaction
from backend.tools.account_aggregator import fetch_accounts, fetch_transactions

SYSTEM_PROMPT = """You are the Budget Planner for FinVoice, a personal finance assistant built for Indian users.

Your role:
- Analyse cash flow: income in vs spending out for the current and recent months.
- Handle variable income gracefully. Do not assume a fixed monthly salary unless confirmed by the data.
- Provide probabilistic guidance for variable-income users: "based on your last three months, you are likely to have ₹X to ₹Y available".
- Answer savings and projection questions with concrete numbers from the transaction data.
- Avoid jargon. Use plain language and Indian number formatting (₹, lakhs, crores).
- Do not moralise about spending habits. Present data. Let the user decide.

You have access to recent transaction data. Use it. Do not speculate beyond what the data shows."""


async def run(
    query: str,
    session_id: str,
) -> AsyncIterator[str]:
    """Stream a response to a budget-related query."""
    client = AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY, timeout=30.0)

    context = await _build_context(session_id)

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


async def _build_context(session_id: str) -> str:
    """
    Build a cash flow summary from the last three months of transactions.
    Separates income from expenses, groups expenses by category.
    """
    try:
        accounts = await fetch_accounts(session_id)
        all_transactions: list[Transaction] = []
        for account in accounts:
            txns = await fetch_transactions(account.account_id)
            all_transactions.extend(txns)

        if not all_transactions:
            return "No transaction data is available."

        income_total = sum(
            t.amount for t in all_transactions if t.category == "Income"
        )
        expense_total = sum(
            t.amount for t in all_transactions if t.category != "Income"
        )
        net = income_total - expense_total

        # Category breakdown
        categories: dict[str, float] = {}
        for t in all_transactions:
            if t.category and t.category != "Income":
                categories[t.category] = categories.get(t.category, 0) + t.amount

        lines = [
            "Cash flow summary (last 90 days):",
            f"  Total income:   ₹{income_total:>10,.0f}",
            f"  Total expenses: ₹{expense_total:>10,.0f}",
            f"  Net:            ₹{net:>10,.0f}",
            "",
            "Spending by category:",
        ]
        for cat, total in sorted(categories.items(), key=lambda x: x[1], reverse=True):
            lines.append(f"  {cat:<22} ₹{total:>8,.0f}")

        total_balance = sum(a.balance for a in accounts)
        lines.append(f"\nCurrent total balance across all accounts: ₹{total_balance:,.0f}")

        return "\n".join(lines)

    except Exception as exc:
        return f"Transaction data could not be loaded: {exc}"
