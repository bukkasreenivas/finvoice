# Roadmap

This document defines the three milestone phases for FinVoice, the MoSCoW priority of each feature, and the dependency chain that determines build order.

---

## Milestone overview

| Milestone | Theme | Target | Success condition |
|---|---|---|---|
| v0.1 | Text MVP | Week 4 | All four specialist agents respond correctly in < 4s via text |
| v0.2 | Voice | Week 7 | Push-to-talk transcription live, Whisper latency < 1.5s |
| v0.3 | Proactive | Week 10 | Weekly briefing delivered without user prompt, receipt scan functional |

---

## v0.1 — Text MVP

Goal: a working multi-agent text interface with Account Aggregator sandbox data, streaming responses, and agent attribution. This milestone proves the core orchestration logic.

### Features

| Feature | Priority | Notes |
|---|---|---|
| LangGraph supervisor agent with routing logic | Must have | Blocks all specialist agents |
| Spending Analyst agent | Must have | Requires Account Aggregator tool |
| Investment Advisor agent | Must have | Requires NSE/BSE via yfinance (.NS suffix) |
| Tax Optimizer agent | Must have | Indian ITR scope only (Income Tax Act, CBDT guidelines) |
| Budget Planner agent | Must have | Must handle irregular income |
| FastAPI backend with WebSocket streaming | Must have | Blocks frontend integration |
| React chat interface with streaming renderer | Must have | Required for demo |
| Agent attribution badge in UI | Must have | Key portfolio differentiator |
| Account Aggregator sandbox integration (Finvu) | Must have | Source of all transaction data |
| NSE/BSE market data via yfinance (.NS suffix) | Must have | Source of investment data |
| Redis cache for market data (60s TTL) | Should have | Prevents rate limit errors during demo |
| PostgreSQL + pgvector setup | Should have | Required for v0.3 RAG; schema defined now |
| Audit log table (every query persisted) | Should have | Demonstrates compliance thinking |
| Docker Compose local setup | Should have | One-command setup for contributors |
| Confidence score returned per response | Could have | Shown in ConfidenceBar component |
| Groq Llama 3 fallback if Claude unavailable | Won't have in v0.1 | Deferred to v0.2 |

### Dependency graph

```
Account Aggregator tool (Finvu sandbox)
    └── Spending Analyst agent
            └── Supervisor routing logic
                    └── FastAPI WebSocket router
                            └── React ChatInterface
                                    └── AgentBadge + MessageBubble

NSE/BSE via yfinance (.NS suffix)
    └── Investment Advisor agent
            └── (same chain above)

PostgreSQL schema
    └── Audit log
    └── pgvector embeddings (used in v0.3)
```

The supervisor agent is the single most critical dependency. Nothing in the UI is testable end-to-end until routing works.

### Success criteria

- Supervisor routes spending, investment, tax, and budget queries to the correct agent with ≥ 90% accuracy on a 20-query manual test set.
- End-to-end response time (query received to first token streamed) < 4s on a standard laptop.
- All four agents return a non-empty response with agent name attribution.
- Docker Compose starts the full stack with a single `docker-compose up`.
- Audit log entry created for every query (verified by direct database inspection).

---

## v0.2 — Voice

Goal: push-to-talk voice input via self-hosted Whisper. The user can speak a question, see the transcript, confirm it, and receive a streamed agent response. Text input remains available.

### Features

| Feature | Priority | Notes |
|---|---|---|
| Browser mic capture (useVoice hook) | Must have | Blocks all voice features |
| Push-to-talk button with waveform visualisation | Must have | Core UX |
| Whisper transcription endpoint (POST /voice/transcribe) | Must have | faster-whisper on CPU |
| Transcript confirmation step before submission | Must have | Prevents mis-transcription errors |
| Whisper latency < 1.5s for a 10-second clip | Must have | Defined acceptance criterion |
| Groq Llama 3 fallback when Claude unavailable | Should have | Resilience for demo environment |
| Deepgram as documented fallback for Whisper | Should have | Documented in .env.example |
| Mobile-responsive voice UI | Could have | Desirable but not blocking demo |
| Audio waveform playback of agent response (TTS) | Won't have in v0.2 | Deferred to v0.3 |

### Dependency graph

```
Browser mic (useVoice hook)
    └── VoiceInput component (push-to-talk button)
            └── POST /voice/transcribe endpoint
                    └── faster-whisper model loaded on startup
                            └── Transcript returned to UI
                                    └── User confirms → submitted as text query
                                            └── (same WebSocket flow as v0.1)
```

### Success criteria

- Push-to-talk button visible and functional in Chrome and Firefox.
- Whisper transcribes a 10-second spoken query in < 1.5s on the demo machine.
- Transcript is shown to the user before submission.
- User can edit the transcript before confirming.
- Voice input and text input coexist without UI conflicts.

---

## v0.3 — Proactive

Goal: FinVoice acts without being asked. A weekly briefing is generated and delivered automatically. Receipt scanning adds a multimodal input path.

### Features

| Feature | Priority | Notes |
|---|---|---|
| Weekly proactive briefing (cron-triggered) | Must have | Defines "proactive" milestone |
| Briefing covers spending summary, top anomaly, investment delta | Must have | Minimum useful content |
| Conversation history persisted to PostgreSQL | Must have | Required for contextual follow-ups |
| RAG over transaction history via pgvector | Must have | Enables "last month vs this month" queries |
| Receipt scanning via device camera | Should have | Multimodal input demonstration |
| TTS playback of briefing (audio response) | Should have | Completes the voice-first loop |
| Push notification or email delivery of briefing | Could have | Requires notification infra |
| Pinecone migration path documented | Could have | Shows production readiness thinking |

### Dependency graph

```
PostgreSQL conversation history
    └── pgvector embeddings of past transactions
            └── RAG retrieval tool (injected into agent context)
                    └── All four specialist agents (enriched responses)

Cron scheduler (APScheduler or Railway cron)
    └── Weekly briefing generator
            └── Supervisor agent (proactive mode, no user query)
                    └── Briefing delivery (UI notification or email)

Camera capture (browser API)
    └── Receipt image upload endpoint
            └── Claude vision for OCR + categorisation
                    └── Spending Analyst agent (adds to transaction log)
```

### Success criteria

- Weekly briefing generated automatically every Monday at 08:00 local time.
- Briefing includes: spending summary for the past seven days, the largest single transaction, and portfolio delta vs the previous week.
- RAG retrieval returns relevant past transactions for follow-up queries ("what did I spend on groceries last month?").
- Receipt scan correctly extracts merchant name and amount for ≥ 85% of clean receipt images.

---

## Cross-milestone dependencies

The table below shows which v0.1 decisions constrain later milestones. Get these right in v0.1 to avoid rework.

| Decision | Why it matters later |
|---|---|
| PostgreSQL schema includes pgvector extension | v0.3 RAG requires it from day one |
| WebSocket message format includes `agent_name` and `confidence` fields | v0.2 voice responses use the same format |
| Audit log captures query text, agent routed to, and latency | v0.3 analytics and briefing generation read from this table |
| Docker Compose defines all services including Redis | v0.2 and v0.3 add no new infra dependencies |
