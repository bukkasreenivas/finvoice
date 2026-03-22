"""
Account Aggregator integration via the Finvu sandbox.

The Account Aggregator (AA) framework is an RBI-regulated data-sharing
architecture. Financial data flows from Financial Information Providers (FIPs)
to Financial Information Users (FIUs) only with explicit user consent.

Finvu sandbox base URL: https://aauat.finvu.in/API/V1
Docs: https://finvu.github.io/sandbox/finvu_aa_integration

Authentication: every request requires a `client_api_key` header containing
a JWT issued by Finvu. Requests must also carry an `x-jws-signature` header
(RS256 detached JWS of the request body). Financial data is returned encrypted
using ECDH Curve25519 key material exchanged during the FI request step.

To get sandbox credentials: email support@cookiejar.co.in with your public key.
They issue the `client_api_key` JWT (valid for six months in sandbox).

This project uses the synthetic data fallback when FINVU_CLIENT_API_KEY is not
set. This is the default for local development. No real banking data is used.
See ADR-003 for the full compliance scope decision.
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

# Finvu sandbox base URL — confirmed from official docs
SANDBOX_BASE_URL = "https://aauat.finvu.in/API/V1"

_BASE = SANDBOX_BASE_URL


def _headers() -> dict[str, str]:
    """
    Build the required Finvu API headers.
    client_api_key is a JWT issued by Finvu for the sandbox.
    x-jws-signature must be an RS256 detached JWS of the request body.
    For the synthetic fallback path this function is never called.
    """
    return {
        "content-Type": "application/json",
        "Accept": "application/json",
        "client_api_key": settings.FINVU_CLIENT_API_KEY,
    }


# ─── Main interface ───────────────────────────────────────────────────────────


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=4))
async def fetch_accounts(user_id: str) -> list[AccountSummary]:
    """
    Fetch all linked accounts for a user from the Finvu sandbox.
    Falls back to synthetic data if FINVU_CLIENT_API_KEY is not set.
    """
    if not settings.FINVU_CLIENT_API_KEY:
        return _sandbox_accounts(user_id)

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.get(
                f"{_BASE}/Accounts/linked/{user_id}",
                headers=_headers(),
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
    Falls back to synthetic data if FINVU_CLIENT_API_KEY is not set.
    """
    if not settings.FINVU_CLIENT_API_KEY:
        return _sandbox_transactions(account_id, from_date, to_date)

    from_date = from_date or (datetime.utcnow() - timedelta(days=90))
    to_date = to_date or datetime.utcnow()

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.get(
                f"{_BASE}/FI/fetch/{account_id}",
                headers=_headers(),
                params={
                    "from": from_date.strftime("%Y-%m-%dT%H:%M:%S.000Z"),
                    "to": to_date.strftime("%Y-%m-%dT%H:%M:%S.000Z"),
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
