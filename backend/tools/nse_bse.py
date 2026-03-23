"""
NSE and BSE market data via yfinance.

NSE symbols use the .NS suffix (e.g. INFY.NS, RELIANCE.NS).
BSE symbols use the .BO suffix (e.g. INFY.BO).
CoinGecko is used for cryptocurrency prices.

All market data responses are cached in Redis for 60 seconds to avoid
hitting rate limits and to keep latency under the 4-second target.

yfinance is a synchronous library. All calls are dispatched to a thread
executor via asyncio.get_running_loop().run_in_executor so they never
block the asyncio event loop (which would prevent the WebSocket keepalive
task from firing and trigger Railway's 20-second idle timeout).
"""

from __future__ import annotations

import asyncio
import json

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


def _fetch_quote_sync(symbol: str) -> dict | None:
    """
    Blocking yfinance fetch. Must be run in a thread executor.

    yfinance 0.2.x uses fast_info with attribute access (snake_case),
    not the old dict-style .get() with camelCase keys.
    Index symbols (^NSEI, ^BSESN) skip ticker.info because it is slow
    and does not contain meaningful PE ratio or market cap for indices.
    """
    try:
        ticker = yf.Ticker(symbol)
        fi = ticker.fast_info

        price = float(getattr(fi, "last_price", None) or 0)
        prev_close = float(getattr(fi, "previous_close", None) or price)
        if price == 0:
            return None

        change = price - prev_close
        change_pct = (change / prev_close * 100) if prev_close else 0.0
        volume = int(getattr(fi, "three_month_average_volume", None) or 0)

        # Skip the heavy ticker.info call for index symbols.
        is_index = symbol.startswith("^")
        if is_index:
            name = symbol
            pe_ratio = None
            market_cap = 0.0
        else:
            try:
                info = ticker.info
                name = info.get("longName", symbol)
                pe_ratio = float(info.get("trailingPE") or 0) or None
                market_cap = float(info.get("marketCap") or 0)
            except Exception:
                name = symbol
                pe_ratio = None
                market_cap = 0.0

        return {
            "symbol": symbol,
            "name": name,
            "price": price,
            "change": round(change, 2),
            "change_pct": round(change_pct, 2),
            "volume": volume,
            "market_cap": market_cap,
            "pe_ratio": pe_ratio,
            "exchange": "NSE" if symbol.endswith(".NS") else "BSE",
        }
    except Exception:
        return None


async def get_quote(symbol: str) -> Quote | None:
    """
    Fetch a real-time quote for an NSE or BSE symbol.

    If the symbol does not include a suffix, .NS (NSE) is assumed.
    Returns None if yfinance cannot find the symbol.
    The blocking yfinance call runs in a thread executor so the event
    loop remains free for keepalive and other coroutines.
    """
    if "." not in symbol:
        symbol = f"{symbol.upper()}.NS"

    cache_key = f"quote:{symbol}"
    cached = await _cache_get(cache_key)
    if cached:
        return Quote(**cached)

    try:
        loop = asyncio.get_running_loop()
        data = await loop.run_in_executor(None, _fetch_quote_sync, symbol)
        if data is None:
            return None
        quote = Quote(**data)
        await _cache_set(cache_key, quote.model_dump())
        return quote
    except Exception:
        return None


def _fetch_historical_sync(symbol: str, period: str, interval: str) -> list[dict]:
    """Blocking yfinance historical download. Must be run in a thread executor."""
    try:
        df = yf.download(symbol, period=period, interval=interval, progress=False)
        return [
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
    except Exception:
        return []


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

    loop = asyncio.get_running_loop()
    records = await loop.run_in_executor(
        None, _fetch_historical_sync, symbol, period, interval
    )
    if records:
        await _cache_set(cache_key, records)
    return records


async def get_multiple_quotes(symbols: list[str]) -> list[Quote]:
    """
    Fetch quotes for multiple symbols in parallel.
    Using asyncio.gather means all yfinance calls run concurrently in
    separate threads rather than sequentially, keeping total latency
    close to the slowest single call rather than the sum of all calls.
    """
    results = await asyncio.gather(
        *[get_quote(s) for s in symbols], return_exceptions=True
    )
    return [r for r in results if isinstance(r, Quote)]


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
    """Fetch current values for the major Indian indices in parallel."""
    return await get_multiple_quotes(list(MAJOR_INDICES.values()))
