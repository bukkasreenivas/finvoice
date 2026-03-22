# FinVoice

**Voice-first multi-agent personal finance assistant**

![Python](https://img.shields.io/badge/Python-3.11+-blue?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.111-green?logo=fastapi&logoColor=white)
![React](https://img.shields.io/badge/React-18-61DAFB?logo=react&logoColor=black)
![LangGraph](https://img.shields.io/badge/LangGraph-multi--agent-orange)
![Claude](https://img.shields.io/badge/Claude-claude--sonnet--4--6-purple)
![Whisper](https://img.shields.io/badge/Whisper-faster--whisper-yellow)
![AA](https://img.shields.io/badge/Account_Aggregator-sandbox-blue)
![Docker](https://img.shields.io/badge/Docker-compose-2496ED?logo=docker&logoColor=white)
![Vercel](https://img.shields.io/badge/Frontend-Vercel-black?logo=vercel&logoColor=white)
![Railway](https://img.shields.io/badge/Backend-Railway-7B2FBE?logo=railway&logoColor=white)
![Supabase](https://img.shields.io/badge/Database-Supabase-3ECF8E?logo=supabase&logoColor=white)
![Upstash](https://img.shields.io/badge/Cache-Upstash-00E9A3)

---

## What it does

- Users speak or type a financial question. A supervisor agent routes it to the right specialist: Spending Analyst, Investment Advisor, Tax Optimizer, or Budget Planner.
- Answers stream back in real time with the responding agent named in the UI.
- Proactive weekly briefings are delivered without the user asking.

---

## Architecture

```mermaid
flowchart TD
    User([User]) -->|voice / text| UI[React frontend]
    UI -->|WebSocket| API[FastAPI backend]
    API --> Supervisor[Supervisor agent\nLangGraph StateGraph]

    Supervisor -->|spending query| SA[Spending Analyst]
    Supervisor -->|investment query| IA[Investment Advisor]
    Supervisor -->|tax query| TO[Tax Optimizer]
    Supervisor -->|budget query| BP[Budget Planner]

    SA --> AA[Account Aggregator\nsandbox]
    IA --> NSE[NSE/BSE via\nyfinance]
    IA --> CG[CoinGecko]
    TO --> CBDT[(CBDT / IT Act\nRAG index)]
    BP --> AA

    SA --> Stream[Streaming response]
    IA --> Stream
    TO --> Stream
    BP --> Stream

    Stream -->|token by token| UI
    API --> Audit[(Audit log\nPostgreSQL)]
    API --> Cache[(Redis cache\n60s TTL)]
    API --> Voice[Whisper\nfaster-whisper]
```

---

## Agent breakdown

| Agent | Tools | Example queries |
|---|---|---|
| Spending Analyst | Account Aggregator sandbox, pgvector transaction search | "Where did I spend the most last month?" "Flag any transactions over ₹2,000." |
| Investment Advisor | NSE/BSE via yfinance, CoinGecko | "How is my mutual fund portfolio performing this quarter?" "What is the P/E on Infosys?" |
| Tax Optimizer | CBDT / Income Tax Act RAG index | "What expenses can I claim as a freelance consultant?" "How does LTCG tax work on my equity funds?" |
| Budget Planner | Account Aggregator sandbox, cash flow model | "Am I on track this month?" "How much can I save if I cut dining out by half?" |

All Tax Optimizer and Investment Advisor responses include the disclaimer: "This is informational only and does not constitute regulated financial advice. Consult a SEBI-registered advisor."

---

## Tech stack

| Layer | Technology |
|---|---|
| Backend | Python 3.11, FastAPI, LangGraph |
| Frontend | React 18, TypeScript, WebSocket |
| LLM | Claude claude-sonnet-4-6 (primary), Groq Llama 3 (fallback) |
| Voice | faster-whisper (local), Deepgram API (production) |
| Database | PostgreSQL 15 + pgvector — Supabase free tier (production) |
| Cache | Redis — Upstash free tier (production) |
| Banking data | Account Aggregator framework via Finvu sandbox |
| Market data | NSE/BSE via yfinance (.NS suffix), CoinGecko |
| Frontend deployment | Vercel |
| Backend deployment | Railway (supports WebSockets and long-running processes) |

---

## Quick start (local)

Prerequisites: Docker and Docker Compose installed.

```bash
git clone https://github.com/bukkasreenivas/finvoice.git
cd finvoice
cp .env.example .env
# Add your API keys to .env
docker-compose up
```

The app is available at `http://localhost:3000`. The backend API is at `http://localhost:8000`. API documentation is at `http://localhost:8000/docs`.

---

## Production deployment

FinVoice uses a split deployment — each service runs on the platform best suited to it.

| Component | Platform | Notes |
|---|---|---|
| React frontend | Vercel | Connect GitHub repo, set `REACT_APP_API_URL` and `REACT_APP_WS_URL` to Railway backend URL |
| FastAPI backend | Railway | Supports WebSockets and long-running processes. Vercel serverless does not. |
| PostgreSQL + pgvector | Supabase | Free tier. pgvector enabled by default. Note: database pauses after one week of inactivity — resume via the Supabase dashboard. |
| Redis cache | Upstash | Serverless Redis, free tier (10,000 commands per day) |
| Voice transcription | Deepgram API | Free tier: 45 minutes per month. Set `DEEPGRAM_API_KEY` on Railway. Local dev uses self-hosted Whisper. |

---

## Environment variables

Copy `.env.example` to `.env` and fill in the values.

Required for local development:
- `ANTHROPIC_API_KEY` — Claude API access
- `FINVU_CLIENT_ID` and `FINVU_CLIENT_SECRET` — Finvu Account Aggregator sandbox credentials

Additional variables required for production (see `.env.example` for all):
- `SUPABASE_URL` and `SUPABASE_ANON_KEY` — Supabase project credentials
- `UPSTASH_REDIS_URL` — Upstash Redis connection string
- `DEEPGRAM_API_KEY` — Deepgram voice transcription
- `RAILWAY_BACKEND_URL` — set on Vercel so the frontend knows where to connect

---

## PM artefacts

These documents are in the `docs/` folder. They demonstrate AI-native product thinking alongside the code.

| Document | Description |
|---|---|
| [PRD.md](docs/PRD.md) | Full product requirements document covering problem statement, personas, functional requirements per agent, and non-functional requirements |
| [user-research.md](docs/user-research.md) | Synthesis of seven qualitative interviews with JTBD statements and product implications |
| [competitive-analysis.md](docs/competitive-analysis.md) | Comparison of FinVoice against CRED, Fi Money, Jupiter, Groww, and Money View |
| [roadmap.md](docs/roadmap.md) | Three milestone phases with MoSCoW priorities, dependency graphs, and success criteria |
| [metrics.md](docs/metrics.md) | North star metric, guardrail metrics, leading indicators, and PostgreSQL instrumentation schema |
| [experiment-design.md](docs/experiment-design.md) | A/B experiment design: voice input vs text input, including hypothesis, sample size calculation, and failure criteria |
| [ai-prompt-journal.md](docs/ai-prompt-journal.md) | Log of prompts used to build this project with PM decisions at each step |

For a narrative account of the AI-native development methodology, see [BUILDING_WITH_AI.md](BUILDING_WITH_AI.md).

---

## Skills demonstrated

This project demonstrates the following enterprise AI capabilities:

- **Multi-agent orchestration** — LangGraph StateGraph with deterministic routing, checkpointing, and audit logging. Four specialist agents with a supervisor that routes by query intent.

- **RAG on structured data** — pgvector extension on PostgreSQL for semantic search over transaction history. Enables contextual follow-up queries ("what did I spend on groceries last month?").

- **Voice and multimodal input** — Self-hosted Whisper via faster-whisper for speech-to-text. Push-to-talk UI with transcript confirmation before submission.

- **Real-time streaming** — FastAPI WebSocket endpoint streams agent responses token by token. React hooks manage the connection and render incrementally.

- **Regulatory awareness** — Audit log on every query. SEBI disclaimer coverage tracked as a guardrail metric. Account Aggregator sandbox only (no real banking data). ADRs document compliance scope decisions.

- **AI-native PM methodology** — PRD, user research, competitive analysis, metrics framework, and experiment design all produced with Claude. The ai-prompt-journal.md documents every significant prompt with the human decision that followed.

- **MCP server design** — See Project 3 in this portfolio for a full Model Context Protocol server implementation.

---

## Author

Sreenivas Bukka, Product Manager

This project is part of a four-project AI portfolio built to demonstrate enterprise AI skills. The other three projects are in the same GitHub profile.
