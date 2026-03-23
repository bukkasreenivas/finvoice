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

from typing import AsyncIterator, TypedDict

from langgraph.graph import END, StateGraph

from backend.agents import budget, investment, spending, tax
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

# Keyword sets for each agent. Checked in priority order.
# Local classification runs in < 1ms and avoids a full Claude API round trip
# (previously ~500ms–2s using Haiku) before the specialist agent even starts.
_INVESTMENT_KEYWORDS = {
    "stock", "stocks", "share", "shares", "portfolio", "nse", "bse", "sensex",
    "nifty", "mutual fund", "mf", "sip", "equity", "crypto", "bitcoin", "eth",
    "invest", "investment", "returns", "dividend", "ipo", "demat", "broker",
    "trading", "market", "fund", "nav", "largecap", "midcap", "smallcap",
    "intraday", "futures", "options", "commodity", "gold", "silver",
}

_TAX_KEYWORDS = {
    "tax", "itr", "income tax", "80c", "80d", "hra", "lta", "deduction",
    "deductions", "capital gain", "ltcg", "stcg", "tds", "gst", "pan",
    "assessment", "refund", "filing", "return", "cbdt", "regime", "slab",
    "exemption", "rebate", "surcharge", "cess", "advance tax", "audit",
    "ca", "chartered accountant", "tax-loss", "harvesting",
}

_BUDGET_KEYWORDS = {
    "budget", "save", "saving", "savings", "on track", "afford", "goal",
    "goals", "emi", "loan", "projection", "forecast", "cash flow", "cashflow",
    "monthly", "next month", "how much left", "surplus", "deficit",
    "sip target", "financial goal", "emergency fund", "net worth",
}


def route_query(query: str) -> AgentName:
    """
    Classify the query using local keyword matching.
    Runs in < 1ms. Falls back to spending_analyst if no keywords match.
    """
    q = query.lower()
    words = set(q.split())

    if words & _INVESTMENT_KEYWORDS or any(kw in q for kw in _INVESTMENT_KEYWORDS if " " in kw):
        return AgentName.investment
    if words & _TAX_KEYWORDS or any(kw in q for kw in _TAX_KEYWORDS if " " in kw):
        return AgentName.tax
    if words & _BUDGET_KEYWORDS or any(kw in q for kw in _BUDGET_KEYWORDS if " " in kw):
        return AgentName.budget
    return AgentName.spending


# ─── Graph nodes ──────────────────────────────────────────────────────────────


async def _route_node(state: FinVoiceState) -> FinVoiceState:
    agent = route_query(state["query"])
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
    # Step 1 — classify (local keyword match, < 1ms, no API call)
    agent = route_query(query)

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
