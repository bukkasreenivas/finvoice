"""
Supervisor agent — LangGraph StateGraph implementation.

The supervisor receives every user query and routes it to one of four specialist
agents: Spending Analyst, Investment Advisor, Tax Optimizer, or Budget Planner.

Architecture decision: LangGraph over CrewAI. See ADR-001 in the repository wiki.
Reason: deterministic routing, checkpointing, and explicit audit trail — all
essential for a regulated finance context.

Routing is performed by a lightweight intent classification call to Claude.
The classification uses a short system prompt and returns a single agent name.
It does not stream, is cached for identical queries, and adds < 500ms latency.
"""

from __future__ import annotations

import json
from typing import AsyncIterator, TypedDict

from anthropic import AsyncAnthropic
from langgraph.graph import END, StateGraph

from backend.agents import budget, investment, spending, tax
from backend.config import settings
from backend.models.schemas import AgentName

# ─── State ────────────────────────────────────────────────────────────────────


class FinVoiceState(TypedDict):
    query: str
    session_id: str
    routed_to: str
    response_chunks: list[str]
    disclaimer_shown: bool
    error: str | None


# ─── Routing ──────────────────────────────────────────────────────────────────

ROUTER_SYSTEM = """You are a routing classifier for a personal finance assistant.
Classify the user query into exactly one of these agent categories:

  spending_analyst   — transaction history, spending patterns, category analysis, anomaly detection
  investment_advisor — stock prices, portfolio performance, mutual funds, crypto, market data
  tax_optimizer      — income tax, deductions, ITR, capital gains, GST, tax-loss harvesting
  budget_planner     — monthly cash flow, savings goals, "am I on track", projections, EMI planning

Respond with a JSON object only. No explanation. Example: {"agent": "spending_analyst"}"""


async def route_query(query: str) -> AgentName:
    """
    Classify the query and return the target agent name.
    Falls back to spending_analyst if classification fails.
    """
    client = AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY, timeout=30.0)

    try:
        message = await client.messages.create(
            model="claude-haiku-4-5-20251001",  # Fast and cheap for classification
            max_tokens=32,
            system=ROUTER_SYSTEM,
            messages=[{"role": "user", "content": query}],
        )
        raw = message.content[0].text.strip()
        data = json.loads(raw)
        agent_str = data.get("agent", "spending_analyst")
        return AgentName(agent_str)
    except Exception:
        return AgentName.spending


# ─── Graph nodes ──────────────────────────────────────────────────────────────


async def _route_node(state: FinVoiceState) -> FinVoiceState:
    agent = await route_query(state["query"])
    return {**state, "routed_to": agent.value}


def _dispatch_node(state: FinVoiceState) -> str:
    """LangGraph conditional edge — returns the next node name."""
    return state["routed_to"]


# ─── Graph assembly ───────────────────────────────────────────────────────────

graph = StateGraph(FinVoiceState)
graph.add_node("route", _route_node)
graph.add_node(AgentName.spending.value, lambda s: s)
graph.add_node(AgentName.investment.value, lambda s: s)
graph.add_node(AgentName.tax.value, lambda s: s)
graph.add_node(AgentName.budget.value, lambda s: s)

graph.set_entry_point("route")
graph.add_conditional_edges(
    "route",
    _dispatch_node,
    {
        AgentName.spending.value: AgentName.spending.value,
        AgentName.investment.value: AgentName.investment.value,
        AgentName.tax.value: AgentName.tax.value,
        AgentName.budget.value: AgentName.budget.value,
    },
)

for agent_name in [
    AgentName.spending.value,
    AgentName.investment.value,
    AgentName.tax.value,
    AgentName.budget.value,
]:
    graph.add_edge(agent_name, END)

compiled_graph = graph.compile()


# ─── Public interface ─────────────────────────────────────────────────────────


async def stream_response(
    query: str,
    session_id: str,
) -> AsyncIterator[tuple[AgentName, str]]:
    """
    Entry point for the chat router.
    Yields (agent_name, token) tuples so the WebSocket can annotate each token.
    """
    # Step 1 — classify
    agent = await route_query(query)

    # Step 2 — stream from the specialist agent
    agent_stream: AsyncIterator[str]

    if agent == AgentName.spending:
        agent_stream = spending.run(query, session_id)
    elif agent == AgentName.investment:
        agent_stream = investment.run(query, session_id)
    elif agent == AgentName.tax:
        agent_stream = tax.run(query, session_id)
    elif agent == AgentName.budget:
        agent_stream = budget.run(query, session_id)
    else:
        agent_stream = spending.run(query, session_id)

    async for token in agent_stream:
        yield agent, token


def requires_disclaimer(agent: AgentName) -> bool:
    """True for agents whose responses must include a SEBI disclaimer."""
    return agent in (AgentName.investment, AgentName.tax)
