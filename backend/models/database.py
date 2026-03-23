"""
SQLAlchemy ORM models and database setup.

Uses PostgreSQL 15 with the pgvector extension for semantic search over
transaction history. In production this connects to Supabase. Locally it
connects to the pgvector/pgvector:pg15 container in docker-compose.yml.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    Index,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from backend.config import settings


# ─── Engine and session ───────────────────────────────────────────────────────

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.ENVIRONMENT == "development",
    pool_pre_ping=True,
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db() -> AsyncSession:
    """FastAPI dependency that yields a database session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


# ─── Base ─────────────────────────────────────────────────────────────────────


class Base(DeclarativeBase):
    pass


# ─── Models ───────────────────────────────────────────────────────────────────


class AuditLog(Base):
    """Every query is written here for observability and regulatory compliance."""

    __tablename__ = "audit_log"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    session_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    user_query: Mapped[str] = mapped_column(Text, nullable=False)
    input_mode: Mapped[str] = mapped_column(String(10), nullable=False)  # text | voice
    routed_to: Mapped[str] = mapped_column(String(32), nullable=False)
    response_length: Mapped[int] = mapped_column(Integer, default=0)
    latency_ms: Mapped[int] = mapped_column(Integer, default=0)
    disclaimer_shown: Mapped[bool] = mapped_column(Boolean, default=False)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class TransactionEmbedding(Base):
    """
    Stores transaction text with a 1536-dimension pgvector embedding.
    The embedding is generated from a text representation of the transaction
    (date + merchant + category + amount) using the Claude embedding model or
    a local sentence-transformer. Enables semantic search for the Spending
    Analyst's follow-up queries.
    """

    __tablename__ = "transaction_embeddings"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    transaction_id: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    account_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    category: Mapped[str | None] = mapped_column(String(64), nullable=True)
    merchant: Mapped[str | None] = mapped_column(String(128), nullable=True)
    transaction_date: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    embedding: Mapped[list[float]] = mapped_column(Vector(1536), nullable=True)

    __table_args__ = (
        Index(
            "ix_transaction_embedding_hnsw",
            "embedding",
            postgresql_using="hnsw",
            postgresql_with={"m": 16, "ef_construction": 64},
            postgresql_ops={"embedding": "vector_cosine_ops"},
        ),
    )


class ExperimentAssignment(Base):
    """Stores A/B experiment variant assignment per user session."""

    __tablename__ = "experiment_assignments"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    session_id: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    variant: Mapped[str] = mapped_column(String(16), nullable=False)  # control | treatment
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


# ─── Initialisation ───────────────────────────────────────────────────────────


async def init_db() -> None:
    """
    Create all tables and enable the pgvector extension.
    Called once at application startup. Safe to call on an already-initialised
    database because CREATE TABLE IF NOT EXISTS is used.
    """
    async with engine.begin() as conn:
        await conn.execute(__import__("sqlalchemy").text("CREATE EXTENSION IF NOT EXISTS vector"))
        await conn.run_sync(Base.metadata.create_all)
