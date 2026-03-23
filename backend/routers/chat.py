"""
Chat router — WebSocket and REST endpoints.

POST /chat     — non-streaming, returns full response (for testing and simple clients)
WS   /ws/chat  — streaming, sends tokens as they are generated

The WebSocket endpoint is the primary path used by the React frontend.
Each message from the client triggers a routing call, then streams agent tokens
back as JSON-encoded StreamToken objects.

All queries are written to the audit_log table regardless of which endpoint
is used.
"""

from __future__ import annotations

import asyncio
import logging
import time
import uuid
from typing import Any

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession

from backend.agents import supervisor
from backend.models.database import AuditLog, get_db
from backend.models.schemas import (
    AgentName,
    ChatRequest,
    ChatResponse,
    StreamToken,
    WSError,
    WSIncoming,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["chat"])


# ─── REST endpoint ────────────────────────────────────────────────────────────


@router.post("", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    db: AsyncSession = Depends(get_db),
) -> ChatResponse:
    """
    Non-streaming chat endpoint. Collects the full agent response before returning.
    Useful for testing and for clients that cannot handle streaming.
    """
    session_id = request.session_id or str(uuid.uuid4())
    t0 = time.monotonic()

    tokens: list[str] = []
    final_agent: AgentName = AgentName.spending

    async for agent, token in supervisor.stream_response(request.message, session_id):
        tokens.append(token)
        final_agent = agent

    response_text = "".join(tokens)
    latency_ms = int((time.monotonic() - t0) * 1000)
    disclaimer = supervisor.requires_disclaimer(final_agent)

    await _write_audit_log(
        db=db,
        session_id=session_id,
        query=request.message,
        input_mode=request.input_mode.value,
        routed_to=final_agent.value,
        response_length=len(response_text),
        latency_ms=latency_ms,
        disclaimer_shown=disclaimer,
    )

    return ChatResponse(
        message=response_text,
        agent=final_agent,
        session_id=session_id,
        latency_ms=latency_ms,
        disclaimer=disclaimer,
    )


# ─── WebSocket endpoint ───────────────────────────────────────────────────────


@router.websocket("/ws")
async def chat_ws(
    websocket: WebSocket,
    db: AsyncSession = Depends(get_db),
) -> None:
    """
    WebSocket streaming endpoint.

    Message protocol:
      Client → server: JSON matching WSIncoming schema
      Server → client: sequence of StreamToken JSON objects, final one has done=True
      On error:        WSError JSON object
    """
    await websocket.accept()

    try:
        while True:
            raw = await websocket.receive_json()
            incoming = WSIncoming(**raw)
            session_id = incoming.session_id or str(uuid.uuid4())
            t0 = time.monotonic()
            logger.info("ws:recv session=%s query=%r", session_id, incoming.message[:80])

            tokens: list[str] = []
            final_agent: AgentName = AgentName.spending

            try:
                # Periodic keepalive — sends an empty token every 5 seconds while
                # the agent is processing. Railway's load balancer closes idle
                # WebSocket connections after 20 seconds; this keeps the connection
                # alive for as long as the agent needs to produce its first token.
                async def _keepalive() -> None:
                    while True:
                        await asyncio.sleep(5)
                        try:
                            await websocket.send_json(
                                StreamToken(
                                    token="",
                                    agent=AgentName.spending,
                                    session_id=session_id,
                                    done=False,
                                ).model_dump()
                            )
                            logger.debug("ws:keepalive session=%s", session_id)
                        except Exception:
                            break

                keepalive_task = asyncio.create_task(_keepalive())
                logger.info("ws:keepalive_started session=%s", session_id)

                try:
                    token_count = 0
                    async for agent, token in supervisor.stream_response(
                        incoming.message, session_id
                    ):
                        if token_count == 0:
                            logger.info(
                                "ws:first_token agent=%s session=%s elapsed_ms=%d",
                                agent.value,
                                session_id,
                                int((time.monotonic() - t0) * 1000),
                            )
                        final_agent = agent
                        tokens.append(token)
                        token_count += 1
                        await websocket.send_json(
                            StreamToken(
                                token=token,
                                agent=agent,
                                session_id=session_id,
                                done=False,
                            ).model_dump()
                        )

                    logger.info(
                        "ws:done session=%s agent=%s tokens=%d latency_ms=%d",
                        session_id,
                        final_agent.value,
                        token_count,
                        int((time.monotonic() - t0) * 1000),
                    )

                    # Send the terminal done=True token
                    await websocket.send_json(
                        StreamToken(
                            token="",
                            agent=final_agent,
                            session_id=session_id,
                            done=True,
                        ).model_dump()
                    )

                finally:
                    keepalive_task.cancel()
                    try:
                        await keepalive_task
                    except asyncio.CancelledError:
                        pass

            except WebSocketDisconnect:
                # Client or proxy closed the connection — exit this session cleanly.
                raise
            except Exception as exc:
                logger.exception("ws:error session=%s: %s", session_id, exc)
                # Send an error token back to the client. Swallow any send failure
                # that occurs if the socket was already closed by the time we get here.
                try:
                    await websocket.send_json(
                        WSError(error=str(exc), code=500).model_dump()
                    )
                except Exception:
                    pass

            latency_ms = int((time.monotonic() - t0) * 1000)
            disclaimer = supervisor.requires_disclaimer(final_agent)
            response_text = "".join(tokens)

            try:
                await _write_audit_log(
                    db=db,
                    session_id=session_id,
                    query=incoming.message,
                    input_mode=incoming.input_mode.value,
                    routed_to=final_agent.value,
                    response_length=len(response_text),
                    latency_ms=latency_ms,
                    disclaimer_shown=disclaimer,
                )
            except Exception:
                # Audit log failure must not disrupt the user session.
                # Acceptable data loss until the database is connected.
                pass

    except WebSocketDisconnect:
        pass


# ─── Helpers ──────────────────────────────────────────────────────────────────


async def _write_audit_log(
    db: AsyncSession,
    session_id: str,
    query: str,
    input_mode: str,
    routed_to: str,
    response_length: int,
    latency_ms: int,
    disclaimer_shown: bool,
    error: str | None = None,
) -> None:
    entry = AuditLog(
        session_id=session_id,
        user_query=query,
        input_mode=input_mode,
        routed_to=routed_to,
        response_length=response_length,
        latency_ms=latency_ms,
        disclaimer_shown=disclaimer_shown,
        error=error,
    )
    db.add(entry)
    await db.commit()
