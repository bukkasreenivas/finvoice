"""
NSE and BSE market data via yfinance.

NSE symbols use the .NS suffix (e.g. INFY.NS, RELIANCE.NS).
BSE symbols use the .BO suffix (e.g. INFY.BO).
CoinGecko is used for cryptocurrency prices.

All market data responses are cached in Redis for 60 seconds to avoid
hitting rate limits and to keep latency under the 4-second target.
"""

from __future__ import annotations

import json
from datetime import datetime

import httpx
import redis.asyncio as aioredis
import yfinance as yf

from backend.config import settings
from backend.models.schemas import Quote


# ─── Redis cache ──────────────────────────────────────────────────────────────

_redis: aioredis.Redis | None = None


def _get_redis() -> aioredis.Redis:
    global _redis
    if _redis is None:
        _redis = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
    return _redis


CACHE_TTL = 60  # seconds


async def _cache_get(key: str) -> dict | None:
    try:
        raw = await _get_redis().get(key)
        return json.loads(raw) if raw else None
    except Exception:
        return None


async def _cache_set(key: str, value: dict) -> None:
    try:
        await _get_redis().setex(key, CACHE_TTL, json.dumps(value))
    except Exception:
        pass


# ─── NSE / BSE quotes ─────────────────────────────────────────────────────────


async def get_quote(symbol: str) -> Quote | None:
    """
    Fetch a real-time quote for an NSE or BSE symbol.

    If the symbol does not include a suffix, .NS (NSE) is assumed.
    Returns None if yfinance cannot find the symbol.
    """
    if "." not in symbol:
        symbol = f"{symbol.upper()}.NS"

    cache_key = f"quote:{symbol}"
    cached = await _cache_get(cache_key)
    if cached:
        return Quote(**cached)

    try:
        ticker = yf.Ticker(symbol)
        info = ticker.fast_info

        # fast_info keys available without a full download
        price = float(info.get("lastPrice", 0) or 0)
        prev_close = float(info.get("previousClose", price) or price)
        change = price - prev_close
        change_pct = (change / prev_close * 100) if prev_close else 0.0

        quote = Quote(
            symbol=symbol,
            name=ticker.info.get("longName", symbol),
            price=price,
            change=round(change, 2),
            change_pct=round(change_pct, 2),
            volume=int(info.get("threeMonthAverageVolume", 0) or 0),
            market_cap=float(info.get("marketCap", 0) or 0),
            pe_ratio=float(ticker.info.get("trailingPE", 0) or 0) or None,
            exchange="NSE" if symbol.endswith(".NS") else "BSE",
        )

        await _cache_set(cache_key, quote.model_dump())
        return quote

    except Exception:
        return None


async def get_historical(
    symbol: str,
    period: str = "3mo",
    interval: str = "1d",
) -> list[dict]:
    """
    Fetch historical OHLCV data for a symbol.
    period: 1mo, 3mo, 6mo, 1y, 2y, 5y
    interval: 1d, 1wk, 1mo
    """
    if "." not in symbol:
        symbol = f"{symbol.upper()}.NS"

    cache_key = f"hist:{symbol}:{period}:{interval}"
    cached = await _cache_get(cache_key)
    if cached:
        return cached

    try:
        df = yf.download(symbol, period=period, interval=interval, progress=False)
        records = [
            {
                "date": str(idx.date()),
                "open": round(float(row["Open"]), 2),
                "high": round(float(row["High"]), 2),
                "low": round(float(row["Low"]), 2),
                "close": round(float(row["Close"]), 2),
                "volume": int(row["Volume"]),
            }
            for idx, row in df.iterrows()
        ]
        await _cache_set(cache_key, records)
        return records
    except Exception:
        return []


async def get_multiple_quotes(symbols: list[str]) -> list[Quote]:
    """Fetch quotes for multiple symbols, skipping any that fail."""
    results = []
    for symbol in symbols:
        quote = await get_quote(symbol)
        if quote:
            results.append(quote)
    return results


# ─── CoinGecko ────────────────────────────────────────────────────────────────

COINGECKO_BASE = "https://api.coingecko.com/api/v3"


async def get_crypto_price(coin_id: str) -> dict | None:
    """
    Fetch price data for a cryptocurrency from CoinGecko.
    coin_id examples: bitcoin, ethereum, matic-network, solana
    CoinGecko free tier allows 10-30 calls per minute with no API key.
    """
    cache_key = f"crypto:{coin_id}"
    cached = await _cache_get(cache_key)
    if cached:
        return cached

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(
                f"{COINGECKO_BASE}/simple/price",
                params={
                    "ids": coin_id,
                    "vs_currencies": "inr,usd",
                    "include_24hr_change": "true",
                    "include_market_cap": "true",
                },
            )
            response.raise_for_status()
            data = response.json().get(coin_id, {})
            if data:
                await _cache_set(cache_key, data)
            return data or None
    except Exception:
        return None


# ─── Index overview ───────────────────────────────────────────────────────────

MAJOR_INDICES = {
    "NIFTY 50": "^NSEI",
    "SENSEX": "^BSESN",
    "NIFTY Bank": "^NSEBANK",
    "NIFTY IT": "^CNXIT",
}


async def get_market_overview() -> list[Quote]:
    """Fetch current values for the major Indian indices."""
    return await get_multiple_quotes(list(MAJOR_INDICES.values()))
