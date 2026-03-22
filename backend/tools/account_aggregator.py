"""
Account Aggregator integration via the Finvu sandbox.

The Account Aggregator (AA) framework is an RBI-regulated data-sharing
architecture. Financial data flows from Financial Information Providers (FIPs)
to Financial Information Users (FIUs) only with explicit user consent.

This module uses the Finvu sandbox, which returns realistic synthetic Indian
transaction data. No real banking data is used anywhere in this project. See
ADR-003 in the repository wiki for the full compliance scope decision.

Finvu sandbox docs: https://finvu.in/docs/sandbox
"""

from __future__ import annotations

import hashlib
from datetime import datetime, timedelta
from typing import Any

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from backend.config import settings
from backend.models.schemas import AccountSummary, Transaction


# ─── Constants ────────────────────────────────────────────────────────────────

FINVU_BASE_URL = "https://webapi.finvu.in/ConsentAPI"
SANDBOX_BASE_URL = "https://sandbox.finvu.in/ConsentAPI"

_BASE = SANDBOX_BASE_URL if settings.AA_ENV == "sandbox" else FINVU_BASE_URL


# ─── Auth ─────────────────────────────────────────────────────────────────────


async def _get_token() -> str:
    """
    Exchange client credentials for a Finvu bearer token.
    The token is valid for one hour. In production, cache this in Redis.
    """
    async with httpx.AsyncClient(timeout=10) as client:
        response = await client.post(
            f"{_BASE}/v2/token",
            json={
                "client_id": settings.FINVU_CLIENT_ID,
                "client_secret": settings.FINVU_CLIENT_SECRET,
            },
        )
        response.raise_for_status()
        return response.json()["access_token"]


# ─── Main interface ───────────────────────────────────────────────────────────


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=4))
async def fetch_accounts(user_id: str) -> list[AccountSummary]:
    """
    Fetch all linked accounts for a user from the Finvu sandbox.
    Returns a list of AccountSummary objects with balances.
    """
    if not settings.FINVU_CLIENT_ID:
        return _sandbox_accounts(user_id)

    try:
        token = await _get_token()
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.get(
                f"{_BASE}/v2/accounts",
                headers={"Authorization": f"Bearer {token}"},
                params={"userId": user_id},
            )
            response.raise_for_status()
            return _parse_accounts(response.json())
    except httpx.HTTPError:
        return _sandbox_accounts(user_id)


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=4))
async def fetch_transactions(
    account_id: str,
    from_date: datetime | None = None,
    to_date: datetime | None = None,
) -> list[Transaction]:
    """
    Fetch transactions for a given account over a date range.
    Defaults to the last 90 days if no dates are supplied.
    """
    if not settings.FINVU_CLIENT_ID:
        return _sandbox_transactions(account_id, from_date, to_date)

    from_date = from_date or (datetime.utcnow() - timedelta(days=90))
    to_date = to_date or datetime.utcnow()

    try:
        token = await _get_token()
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.get(
                f"{_BASE}/v2/accounts/{account_id}/transactions",
                headers={"Authorization": f"Bearer {token}"},
                params={
                    "from": from_date.strftime("%Y-%m-%d"),
                    "to": to_date.strftime("%Y-%m-%d"),
                },
            )
            response.raise_for_status()
            return _parse_transactions(account_id, response.json())
    except httpx.HTTPError:
        return _sandbox_transactions(account_id, from_date, to_date)


# ─── Response parsers ─────────────────────────────────────────────────────────


def _parse_accounts(data: dict[str, Any]) -> list[AccountSummary]:
    accounts = []
    for item in data.get("accounts", []):
        accounts.append(
            AccountSummary(
                account_id=item["id"],
                account_type=item.get("type", "SAVINGS"),
                balance=float(item.get("balance", 0)),
                currency="INR",
                institution=item.get("fipName", "Unknown Bank"),
            )
        )
    return accounts


def _parse_transactions(
    account_id: str, data: dict[str, Any]
) -> list[Transaction]:
    txns = []
    for item in data.get("transactions", []):
        txns.append(
            Transaction(
                transaction_id=item["id"],
                date=datetime.fromisoformat(item["date"]),
                amount=float(item["amount"]),
                currency="INR",
                description=item.get("narration", ""),
                category=item.get("category"),
                merchant=item.get("merchant"),
                account_id=account_id,
            )
        )
    return txns


# ─── Sandbox fallback data ────────────────────────────────────────────────────
# Used when FINVU_CLIENT_ID is not set (local dev without credentials).
# Synthetic Indian transaction data that reflects realistic spending patterns.


def _sandbox_accounts(user_id: str) -> list[AccountSummary]:
    seed = int(hashlib.md5(user_id.encode()).hexdigest(), 16) % 10000
    return [
        AccountSummary(
            account_id=f"acc-savings-{user_id[:8]}",
            account_type="SAVINGS",
            balance=84_500.0 + seed,
            currency="INR",
            institution="HDFC Bank",
        ),
        AccountSummary(
            account_id=f"acc-current-{user_id[:8]}",
            account_type="CURRENT",
            balance=22_300.0 + seed,
            currency="INR",
            institution="ICICI Bank",
        ),
    ]


def _sandbox_transactions(
    account_id: str,
    from_date: datetime | None,
    to_date: datetime | None,
) -> list[Transaction]:
    to_date = to_date or datetime.utcnow()
    from_date = from_date or (to_date - timedelta(days=90))

    raw = [
        ("Swiggy", "Food & Dining", 485.0, -30),
        ("BigBasket", "Groceries", 1_820.0, -28),
        ("BMTC Monthly Pass", "Transport", 650.0, -27),
        ("Netflix", "Entertainment", 649.0, -25),
        ("Reliance Digital", "Electronics", 4_299.0, -22),
        ("Apollo Pharmacy", "Health", 1_140.0, -20),
        ("Zomato", "Food & Dining", 312.0, -18),
        ("Ola", "Transport", 220.0, -17),
        ("Amazon", "Shopping", 2_499.0, -15),
        ("HDFC Loan EMI", "Loan", 12_500.0, -14),
        ("Myntra", "Shopping", 1_299.0, -12),
        ("Salary Credit", "Income", 75_000.0, -10),
        ("Swiggy Instamart", "Groceries", 760.0, -8),
        ("Uber", "Transport", 185.0, -7),
        ("BookMyShow", "Entertainment", 560.0, -5),
        ("Dmart", "Groceries", 2_340.0, -3),
        ("Paytm Recharge", "Utilities", 399.0, -2),
        ("Coffee Day", "Food & Dining", 145.0, -1),
    ]

    txns = []
    for i, (merchant, category, amount, days_ago) in enumerate(raw):
        txn_date = to_date + timedelta(days=days_ago)
        if txn_date < from_date:
            continue
        txns.append(
            Transaction(
                transaction_id=f"txn-{account_id[:8]}-{i:04d}",
                date=txn_date,
                amount=amount,
                currency="INR",
                description=merchant,
                category=category,
                merchant=merchant,
                account_id=account_id,
            )
        )
    return txns
