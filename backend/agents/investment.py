"""
Investment Advisor agent.

Handles queries about portfolio performance, individual stock/mutual fund analysis,
NSE/BSE market data, and cryptocurrency prices via CoinGecko.

All responses include the mandatory SEBI disclaimer. This is tracked as a
guardrail metric in the audit log (disclaimer_shown = True).

Example queries:
  "How is my portfolio performing this quarter?"
  "What is the P/E ratio on Infosys?"
  "Is Bitcoin a good buy right now?"
"""

from __future__ import annotations

import asyncio
from typing import AsyncIterator

from anthropic import AsyncAnthropic

from backend.config import settings
from backend.tools.nse_bse import get_crypto_price, get_market_overview, get_multiple_quotes, get_quote

SEBI_DISCLAIMER = (
    "\n\n---\n*This is informational only and does not constitute regulated financial "
    "advice. Consult a SEBI-registered investment advisor before making any investment decisions.*"
)

SYSTEM_PROMPT = """You are the Investment Advisor for FinVoice, a personal finance assistant built for Indian users.

Your role:
- Provide factual analysis of Indian stocks (NSE, BSE), mutual funds, and cryptocurrencies.
- Use market data provided in the context block. Do not fabricate prices or returns.
- Explain financial metrics (P/E ratio, CAGR, NAV) in plain language when you use them.
- Use Indian currency (₹) and Indian market terminology (Nifty, Sensex, SIP, ELSS).
- Be objective. Present data and relevant context. Do not make directional buy/sell recommendations.
- Keep responses concise. Lead with the most relevant figure.

IMPORTANT: Every response must end with the SEBI disclaimer provided to you. Do not omit it."""


async def run(
    query: str,
    session_id: str,
) -> AsyncIterator[str]:
    """Stream a response to an investment-related query."""
    client = AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY, timeout=30.0, max_retries=0)

    context = await _build_context(query)

    messages = [
        {
            "role": "user",
            "content": f"{context}\n\nUser question: {query}",
        }
    ]

    disclaimer_appended = False

    async with client.messages.stream(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        system=SYSTEM_PROMPT,
        messages=messages,
    ) as stream:
        async for text in stream.text_stream:
            yield text

    # Append disclaimer after the stream completes
    # The router appends this as a final token so it appears in the UI
    if not disclaimer_appended:
        yield SEBI_DISCLAIMER


# Maps natural language names and ticker aliases to NSE symbols.
# Checked case-insensitively against the user query.
_EQUITY_ALIASES: dict[str, str] = {
    "RELIANCE": "RELIANCE.NS",
    "TCS": "TCS.NS",
    "INFY": "INFY.NS",
    "INFOSYS": "INFY.NS",
    "HDFCBANK": "HDFCBANK.NS",
    "HDFC BANK": "HDFCBANK.NS",
    "HDFC": "HDFCBANK.NS",
    "ICICIBANK": "ICICIBANK.NS",
    "ICICI BANK": "ICICIBANK.NS",
    "ICICI": "ICICIBANK.NS",
    "WIPRO": "WIPRO.NS",
    "AXISBANK": "AXISBANK.NS",
    "AXIS BANK": "AXISBANK.NS",
    "SBIN": "SBIN.NS",
    "SBI": "SBIN.NS",
    "STATE BANK": "SBIN.NS",
    "BAJFINANCE": "BAJFINANCE.NS",
    "BAJAJ FINANCE": "BAJFINANCE.NS",
    "TATAMOTORS": "TATAMOTORS.NS",
    "TATA MOTORS": "TATAMOTORS.NS",
    "ADANIENT": "ADANIENT.NS",
    "HINDUNILVR": "HINDUNILVR.NS",
    "HUL": "HINDUNILVR.NS",
    "HINDUSTAN UNILEVER": "HINDUNILVR.NS",
    "ITC": "ITC.NS",
    "KOTAKBANK": "KOTAKBANK.NS",
    "KOTAK BANK": "KOTAKBANK.NS",
    "KOTAK": "KOTAKBANK.NS",
    "LT": "LT.NS",
    "L&T": "LT.NS",
    "LARSEN": "LT.NS",
    "NIFTYBEES": "NIFTYBEES.NS",
    "NIFTY BEES": "NIFTYBEES.NS",
    "JUNIORBEES": "JUNIORBEES.NS",
    "GOLDBEES": "GOLDBEES.NS",
    "BANKBEES": "BANKBEES.NS",
}

# Maps natural language names to CoinGecko coin IDs.
_CRYPTO_ALIASES: dict[str, str] = {
    "ETH": "ethereum",
    "ETHEREUM": "ethereum",
    "BTC": "bitcoin",
    "BITCOIN": "bitcoin",
    "MATIC": "matic-network",
    "POLYGON": "matic-network",
    "SOL": "solana",
    "SOLANA": "solana",
    "BNB": "binancecoin",
    "XRP": "ripple",
    "ADA": "cardano",
    "DOGE": "dogecoin",
    "DOGECOIN": "dogecoin",
}


async def _build_context(query: str) -> str:
    """
    Pull relevant market data based on the query.
    Always includes a market overview. Adds equity quotes and crypto prices
    for any symbols or natural language names detected in the query.
    All data fetches run in parallel where possible.
    """
    lines = ["Current Indian market overview:"]

    try:
        indices = await get_market_overview()
        for idx in indices:
            direction = "+" if idx.change >= 0 else ""
            lines.append(
                f"  {idx.name}: {idx.price:,.2f} ({direction}{idx.change_pct:.2f}%)"
            )
    except Exception:
        lines.append("  Market data temporarily unavailable.")

    query_upper = query.upper()

    # Detect equity symbols using alias map. Longer aliases are checked first
    # so "HDFC BANK" matches before the shorter "HDFC" alias.
    detected_nse: list[str] = []
    for alias in sorted(_EQUITY_ALIASES, key=len, reverse=True):
        nse_sym = _EQUITY_ALIASES[alias]
        if alias in query_upper and nse_sym not in detected_nse:
            detected_nse.append(nse_sym)

    # Detect crypto symbols.
    detected_crypto: list[str] = []
    for alias, coin_id in _CRYPTO_ALIASES.items():
        if alias in query_upper and coin_id not in detected_crypto:
            detected_crypto.append(coin_id)

    # Fetch equity and crypto data in parallel.
    equity_task = get_multiple_quotes(detected_nse) if detected_nse else asyncio.sleep(0)
    crypto_tasks = [get_crypto_price(c) for c in detected_crypto]

    results = await asyncio.gather(equity_task, *crypto_tasks, return_exceptions=True)
    quotes = results[0] if detected_nse else []
    crypto_results = results[1:] if detected_crypto else []

    if isinstance(quotes, list):
        for quote in quotes:
            short = quote.symbol.replace(".NS", "").replace(".BO", "")
            lines.append(f"\n{short} (NSE):")
            lines.append(f"  Price: ₹{quote.price:,.2f}")
            lines.append(
                f"  Change: {'+' if quote.change >= 0 else ''}{quote.change_pct:.2f}%"
            )
            if quote.pe_ratio:
                lines.append(f"  P/E: {quote.pe_ratio:.1f}")
            if quote.market_cap:
                lines.append(f"  Market cap: ₹{quote.market_cap / 1e7:,.0f} Cr")

    for coin_id, result in zip(detected_crypto, crypto_results):
        if isinstance(result, dict) and result:
            inr_price = result.get("inr", 0)
            change_24h = result.get("inr_24h_change", 0) or 0
            direction = "+" if change_24h >= 0 else ""
            lines.append(f"\n{coin_id.title()}:")
            lines.append(f"  Price: ₹{inr_price:,.2f}")
            lines.append(f"  24h change: {direction}{change_24h:.2f}%")

    return "\n".join(lines)
