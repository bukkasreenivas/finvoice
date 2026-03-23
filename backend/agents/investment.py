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

from typing import AsyncIterator

from anthropic import AsyncAnthropic

from backend.config import settings
from backend.tools.nse_bse import get_market_overview, get_quote

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


async def _build_context(query: str) -> str:
    """
    Pull relevant market data based on the query.
    Always includes a market overview. Adds a specific quote if a symbol
    is detected in the query.
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

    # Detect a ticker symbol in the query (crude but effective for demos)
    query_upper = query.upper()
    known_symbols = [
        "RELIANCE", "TCS", "INFY", "HDFCBANK", "ICICIBANK",
        "WIPRO", "AXISBANK", "SBIN", "BAJFINANCE", "TATAMOTORS",
        "ADANIENT", "HINDUNILVR", "ITC", "KOTAKBANK", "LT",
    ]
    for sym in known_symbols:
        if sym in query_upper:
            quote = await get_quote(f"{sym}.NS")
            if quote:
                lines.append(f"\n{sym} (NSE):")
                lines.append(f"  Price: ₹{quote.price:,.2f}")
                lines.append(f"  Change: {'+' if quote.change >= 0 else ''}{quote.change_pct:.2f}%")
                if quote.pe_ratio:
                    lines.append(f"  P/E: {quote.pe_ratio:.1f}")
                if quote.market_cap:
                    lines.append(f"  Market cap: ₹{quote.market_cap / 1e7:,.0f} Cr")

    return "\n".join(lines)
