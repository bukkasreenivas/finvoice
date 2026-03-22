# FinVoice

This file gives Claude Code full context to continue building FinVoice. Read this entire file before taking any action.

---

## Who I am and what this project is

I am Sreenivas Bukka, a Product Manager building a GitHub project to showcase enterprise AI skills. This project — FinVoice — is one of four projects. It is a voice first, multi-agent personal finance assistant built with Python (FastAPI) + React, targeting the Indian market.

**GitHub repo:** `https://github.com/bukkasreenivas/finvoice` (public, exists)
**Target audience:** Engineering teams and product leaders evaluating enterprise AI implementations
**Primary goal:** Demonstrate RAG, multi-agent orchestration, voice/multimodal input, MCP server design, and AI-native PM thinking in a single deployable app

---

## Project overview

Users speak (or type) natural language financial questions. A supervisor agent routes to one of four specialist agents. Answers stream back in real time with agent attribution shown.

**The four specialist agents:**
1. **Spending Analyst** — transaction categorisation, trend detection, anomaly alerts
2. **Investment Advisor** — portfolio analysis, NSE/BSE market data, rebalancing suggestions
3. **Tax Optimizer** — deduction finder, LTCG/STCG loss harvesting, ITR filing guidance
4. **Budget Planner** — cash flow forecasting, variable income handling, savings goals

**Tech stack:**
- Backend: Python 3.11+, FastAPI, LangGraph (multi-agent orchestration)
- Frontend: React 18, TypeScript, WebSocket for real-time streaming
- Database: PostgreSQL + pgvector extension
- Voice: faster-whisper self-hosted (local), Deepgram API (production)
- Data APIs: Account Aggregator via Finvu sandbox (banking), NSE/BSE via yfinance (.NS suffix), CoinGecko (crypto)
- LLM: Claude claude-sonnet-4-6 (primary), Groq Llama 3 (fallback)
- Cache: Redis locally, Upstash (serverless Redis, free tier) in production
- Database: PostgreSQL + pgvector locally, Supabase free tier in production (pgvector enabled by default)
- Deployment: Docker Compose (local) | Vercel (frontend) + Railway (backend) in production

---

## Current state of the repo

The GitHub repo is live at `https://github.com/bukkasreenivas/finvoice`. All PM artefacts and the full backend and frontend scaffold are committed to `main`.

### What is complete

```
finvoice/
├── CLAUDE.md                    ✅ this file
├── README.md                    ✅ done — Mermaid architecture diagram, agent breakdown, skills section
├── BUILDING_WITH_AI.md          ✅ done — AI-native development narrative
├── docker-compose.yml           ✅ done — FastAPI, React, PostgreSQL + pgvector, Redis
├── .env.example                 ✅ done — all required env vars documented
├── .gitignore                   ✅ done
├── docs/
│   ├── PRD.md                   ✅ done — Layer 1
│   ├── user-research.md         ✅ done — Layer 1
│   ├── competitive-analysis.md  ✅ done — Layer 1 (Indian market: CRED, Fi Money, Jupiter, Groww, Money View)
│   ├── roadmap.md               ✅ done — Layer 2
│   ├── metrics.md               ✅ done — Layer 2
│   ├── experiment-design.md     ✅ done — Layer 2
│   └── ai-prompt-journal.md     ✅ done — Layer 3
├── backend/                     ✅ done — Layer 4
│   ├── main.py                  ✅ FastAPI entrypoint, CORS, lifespan startup
│   ├── config.py                ✅ Pydantic-settings, all env vars
│   ├── requirements.txt         ✅ all dependencies pinned
│   ├── Dockerfile               ✅ builds with faster-whisper model baked in
│   ├── agents/
│   │   ├── supervisor.py        ✅ LangGraph StateGraph + Claude Haiku routing
│   │   ├── spending.py          ✅ Spending Analyst with AA transaction context
│   │   ├── investment.py        ✅ Investment Advisor with NSE/BSE quotes + SEBI disclaimer
│   │   ├── tax.py               ✅ Tax Optimizer with static CBDT/IT Act RAG context + disclaimer
│   │   └── budget.py            ✅ Budget Planner with cash flow summary
│   ├── tools/
│   │   ├── account_aggregator.py ✅ Finvu sandbox + synthetic Indian data fallback
│   │   ├── nse_bse.py           ✅ yfinance .NS/.BO + CoinGecko + Redis cache
│   │   └── whisper.py           ✅ faster-whisper locally, Deepgram in production
│   ├── routers/
│   │   ├── chat.py              ✅ POST /chat + WebSocket /chat/ws with audit log
│   │   └── voice.py             ✅ POST /voice/transcribe with file validation
│   └── models/
│       ├── schemas.py           ✅ Pydantic schemas for all endpoints
│       └── database.py          ✅ SQLAlchemy + pgvector + HNSW index + init_db
└── frontend/                    ✅ done — Layer 4 (scaffold)
    ├── package.json             ✅ React 18, TypeScript
    ├── tsconfig.json            ✅
    ├── Dockerfile               ✅ multi-stage nginx build
    ├── nginx.conf               ✅
    ├── public/index.html        ✅
    └── src/
        ├── App.tsx              ✅
        ├── index.tsx            ✅
        ├── components/
        │   ├── ChatInterface.tsx ✅ streaming UI, input row, scroll management
        │   ├── VoiceInput.tsx   ✅ push-to-talk, MediaRecorder, transcript confirmation
        │   ├── AgentBadge.tsx   ✅ colour-coded badge per specialist agent
        │   └── MessageBubble.tsx ✅ streaming cursor, markdown-ready
        └── hooks/
            ├── useWebSocket.ts  ✅ WebSocket with auto-reconnect, token accumulation
            └── useVoice.ts      ✅ MediaRecorder + POST /voice/transcribe
```

### What to build next

```
docs/
└── architecture.md              ← Detailed Mermaid architecture diagram (optional)
```

The app is functional end-to-end. To run locally:
```bash
cp .env.example .env
# Add ANTHROPIC_API_KEY at minimum
docker-compose up
```
Then open `http://localhost:3000`.

---

## Key architectural decisions

These are documented as ADRs and should be referenced when building the backend.

**ADR-001: LangGraph over CrewAI for agent orchestration**
Reason: LangGraph provides deterministic control flow, checkpointing, and audit trails essential for a regulated finance context. CrewAI is faster to prototype but less controllable in production.

**ADR-002: Self-hosted Whisper over managed API**
Reason: Zero cost, no data leaving the system, faster-whisper runs acceptably on CPU for demo purposes. Deepgram kept as documented fallback.

**ADR-003: Account Aggregator (AA) framework sandbox only (no real banking data)**
Reason: Open source project. Real data introduces compliance obligations under RBI's AA framework. Finvu sandbox provides realistic Indian transaction data for demo purposes.

**ADR-005: Vercel (frontend) + Railway (backend) split deployment**
Reason: Vercel does not support WebSockets or long-running processes on its serverless runtime. FastAPI with WebSocket streaming and Whisper transcription requires a persistent process. Railway free tier supports this. Vercel handles the React frontend optimally.

**ADR-006: Supabase for PostgreSQL + pgvector in production**
Reason: Supabase free tier provides PostgreSQL 15 with pgvector enabled by default. No manual extension setup needed. Standard postgresql:// connection string means zero code changes from local dev. Upstash provides equivalent serverless Redis with identical connection string format.

**ADR-007: Deepgram API for voice in production, faster-whisper locally**
Reason: Railway free tier RAM limits make self-hosted faster-whisper unreliable in production. Deepgram's free tier (45 minutes per month) is sufficient for demos. Local development continues to use self-hosted Whisper via Docker.

**ADR-004: PostgreSQL + pgvector over dedicated vector DB**
Reason: Reduces infrastructure complexity. pgvector handles semantic search over transaction history adequately at demo scale. Pinecone migration path documented for production.

---

## GitHub Issues and milestones

### Labels to create
`epic`, `story`, `spike`, `bug` + `v0.1`, `v0.2`, `v0.3`

### Milestones

```
Milestone: v0.1 — Text MVP
Due: 4 weeks from project start
Description: Multi-agent text interface with Account Aggregator sandbox, streaming
responses, and agent attribution. All 4 specialist agents functional.

Milestone: v0.2 — Voice
Due: 7 weeks from project start
Description: Push-to-talk voice input via Whisper. Visual waveform feedback.
Transcript confirmation before submission.

Milestone: v0.3 — Proactive
Due: 10 weeks from project start
Description: Weekly proactive voice briefings. Receipt scanning via camera.
Conversation history persistence.
```

### Key user stories

```
[EPIC] Multi-agent orchestration core
Supervisor agent routes user queries to specialist agents via LangGraph StateGraph.
Acceptance: All 4 specialist agents respond correctly to routed queries in < 4s.

[STORY] As a user, I want to type a financial question and receive an answer from the
right specialist agent, so that I get relevant expertise without navigating menus.
AC:
- Supervisor correctly routes spending/investment/tax/budget queries (manual test)
- Agent name shown in response UI
- Response streams token by token via WebSocket
- Audit log entry created for every query
Labels: story, v0.1

[STORY] As a user with irregular income, I want to ask "am I on track this month?"
and get an answer that accounts for my variable earnings, so that I'm not compared
against a fixed budget I never set.
AC:
- Budget Planner agent detects irregular income pattern from transaction history
- Response includes a probabilistic range ("you're likely to have ₹X–₹Y left")
- No fixed budget assumption in the prompt
Labels: story, v0.1

[STORY] As a self-employed user, I want to ask what expenses I can claim this quarter,
so that I don't overpay tax.
AC:
- Tax Optimizer agent responds with Income Tax Act deduction categories (Section 80C, 80D, HRA, LTA)
- Response includes disclaimer: "this is informational only and does not constitute
  regulated financial advice. Consult a SEBI-registered advisor."
- Sources cited (CBDT circular and Income Tax Act links)
Labels: story, v0.1

[SPIKE] Evaluate LangGraph vs CrewAI for supervisor routing
Research question: Which framework gives better observability and audit logging for
a regulated finance context?
Output: ADR in GitHub Wiki
Labels: spike, v0.1

[STORY] As a user, I want to tap a mic button and speak my question, so that I can
interact with FinVoice without typing.
AC:
- Push-to-talk button visible in main UI
- Audio captured from browser mic
- Whisper transcription returned in < 1.5s for a 10-second clip
- Transcript shown before being submitted so user can confirm
Labels: story, v0.2
```

### GitHub Project board columns

Board name: "FinVoice development"
- `Backlog` — all unstarted issues
- `In progress` — actively being worked
- `Review` — PR raised, awaiting review
- `Done` — merged and deployed

---

## Environment variables

```bash
# LLM
ANTHROPIC_API_KEY=your_key_here
GROQ_API_KEY=your_key_here

# Banking (Account Aggregator via Finvu sandbox)
FINVU_CLIENT_ID=your_finvu_client_id
FINVU_CLIENT_SECRET=your_finvu_client_secret
AA_ENV=sandbox

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/finvoice
REDIS_URL=redis://localhost:6379

# Voice (if using managed Whisper)
DEEPGRAM_API_KEY=your_deepgram_key  # optional, fallback to self-hosted

# App
SECRET_KEY=your_jwt_secret
ENVIRONMENT=development
```

---

## Writing style and tone guidelines

These guidelines must be followed across every document, comment, commit message, and code file written for this project.

### Language
- Use Indian English throughout. Examples: "fulfil" not "fulfill", "organise" not "organize", "behaviour" not "behavior", "colour" not "color", "licence" as noun, "license" as verb.
- Spell out numbers one through ten. Use numerals from 11 onwards.
- Dates in DD Month YYYY format e.g. 16 April 2023.

### Sentence construction
- No hyphens in sentences. This is a hard rule. Do not use em dashes, en dashes or hyphens to join clauses or add parenthetical remarks. Rewrite the sentence instead.
  Wrong: "FinVoice is a voice-first app — it uses Whisper for transcription."
  Right: "FinVoice is a voice first app. It uses Whisper for transcription."
- Write short declarative sentences. One idea per sentence.
- Do not use filler phrases like "it is worth noting that", "it goes without saying", "needless to say" or "as mentioned above".
- Active voice preferred. Passive only when the actor is genuinely unknown.

### Structure and formatting
- Sentence case for all headings. Never title case, never all caps.
- Tables for comparisons and feature matrices. Bullets for lists of items or steps. Prose for reasoning and narrative.
- Every section must answer "so what" not just "what". A finding without an implication is incomplete.
- No excessive bolding within body text. Bold is for table headers and section labels only.

### Tone
- Direct and practical. Write like a knowledgeable colleague briefing another knowledgeable colleague.
- No hype or marketing language. "FinVoice solves X" not "FinVoice revolutionises X".
- Skills demonstrated must be explicit. Do not make the reader infer them from the code. State them plainly.
- BUILDING_WITH_AI.md tone: reflective practitioner documenting real decisions, not a product launch announcement.

---

## Session continuity

To continue building in a new Claude Code session:

1. Ensure this CLAUDE.md is in the repo root (it is)
2. Run `claude` in the repo directory
3. Say: "Read CLAUDE.md and continue" — Claude Code will have full context

**Last updated:** 22 March 2026
**Current phase:** Complete — all four layers built and pushed to main
**GitHub repo:** `https://github.com/bukkasreenivas/finvoice`
**Deployment:** Vercel (frontend) + Railway (backend) + Supabase (DB) + Upstash (Redis)
