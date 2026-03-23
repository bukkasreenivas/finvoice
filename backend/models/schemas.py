"""
Pydantic request and response schemas for all FinVoice API endpoints.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


# ─── Enums ────────────────────────────────────────────────────────────────────


class AgentName(str, Enum):
    supervisor = "supervisor"
    spending = "spending_analyst"
    investment = "investment_advisor"
    tax = "tax_optimizer"
    budget = "budget_planner"


class InputMode(str, Enum):
    text = "text"
    voice = "voice"


# ─── Chat ─────────────────────────────────────────────────────────────────────


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000)
    session_id: str | None = Field(default=None)
    input_mode: InputMode = InputMode.text


class StreamToken(BaseModel):
    """Single token emitted over the WebSocket stream."""

    token: str
    agent: AgentName
    session_id: str
    done: bool = False


class ChatResponse(BaseModel):
    """Full response returned by the POST /chat endpoint (non-streaming)."""

    message: str
    agent: AgentName
    session_id: str
    latency_ms: int
    disclaimer: bool = False


# ─── Voice ────────────────────────────────────────────────────────────────────


class TranscribeResponse(BaseModel):
    transcript: str
    duration_seconds: float
    backend: str = Field(description="'whisper' or 'deepgram'")


# ─── Account Aggregator ────────────────────────────────────────────────────────


class Transaction(BaseModel):
    transaction_id: str
    date: datetime
    amount: float
    currency: str = "INR"
    description: str
    category: str | None = None
    merchant: str | None = None
    account_id: str


class AccountSummary(BaseModel):
    account_id: str
    account_type: str
    balance: float
    currency: str = "INR"
    institution: str
    transactions: list[Transaction] = []


# ─── Market data ──────────────────────────────────────────────────────────────


class Quote(BaseModel):
    symbol: str
    name: str
    price: float
    change: float
    change_pct: float
    volume: int | None = None
    market_cap: float | None = None
    pe_ratio: float | None = None
    exchange: str


class PortfolioHolding(BaseModel):
    symbol: str
    quantity: float
    avg_cost: float
    current_price: float
    current_value: float
    pnl: float
    pnl_pct: float


# ─── Audit log ────────────────────────────────────────────────────────────────


class AuditLogEntry(BaseModel):
    id: UUID
    session_id: str
    user_query: str
    input_mode: InputMode
    routed_to: AgentName
    response_length: int
    latency_ms: int
    disclaimer_shown: bool
    error: str | None = None
    created_at: datetime

    class Config:
        from_attributes = True


# ─── WebSocket messages ───────────────────────────────────────────────────────


class WSIncoming(BaseModel):
    """Message sent by the frontend over the WebSocket."""

    message: str
    session_id: str | None = None
    input_mode: InputMode = InputMode.text


class WSError(BaseModel):
    error: str
    code: int = 500
