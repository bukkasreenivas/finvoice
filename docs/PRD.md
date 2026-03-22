# Product requirements document — FinVoice

**Version:** 1.0
**Status:** Published
**Author:** Sreenivas Bukka — Product Manager
**Last updated:** March 2026

---

## TL;DR

FinVoice is a voice first multi agent personal finance assistant. Users speak naturally to a team of specialised AI agents — spending analyst, investment advisor, tax optimiser, and budget planner — and receive real time grounded financial insights without opening a spreadsheet or navigating a dashboard.

---

## Problem statement

Personal finance apps have a translation problem, not a features problem. Walnut was acquired. ET Money pivoted to wealth. The pattern repeats across Jupiter, Fi Money, and CRED: users engage for two to three weeks after account linking, then churn. The friction is not missing functionality. It is the cognitive load of translating raw data into decisions.

Three root causes drive this:

1. **Passive dashboards require active interpretation.** A chart showing ₹340 on dining tells you nothing about whether that is fine or alarming given your income, goals, and last month's pattern.
2. **No conversational interface.** People talk about money with partners, friends, and advisors. They do not pivot table it.
3. **Single agent AI is shallow.** Existing AI features (Fi Money's insights, CRED's spend analysis) use one model for everything. Tax optimisation, investment rebalancing, and budget forecasting require different reasoning modes, data sources, and guardrails.

FinVoice solves all three. Speak your question, get a reasoned answer from the right specialist agent, with sources and confidence shown.

---

## Goals

| # | Goal | Metric | Target |
|---|------|--------|--------|
| G1 | Users get meaningful financial answers without navigating menus | Weekly active voice queries per user (north star) | 3 or more queries per user per week by week 6 |
| G2 | Multi agent architecture is visible and legible to users | Percentage of responses showing agent attribution | 100% |
| G3 | Voice input reduces time to answer vs text | Median query to response time | Less than 4 seconds end to end |
| G4 | Users trust the output enough to act on it | Percentage of recommendations where user taps "tell me more" | 25% or more |

---

## Non goals

- **Not a trading or execution platform.** FinVoice never places trades, moves money, or connects to brokerage APIs for write access. Read only data only.
- **Not a regulated financial advisor.** All outputs include a disclaimer. Recommendations are informational, not advice.
- **Not a budgeting enforcer.** No spending limits, no guilt driven notifications. The tone is a knowledgeable friend, not a bank's compliance system.
- **Not multilingual at v1.** English only. Internationalisation is a v2 consideration.
- **Not a mobile app.** Web first (React). PWA support is a future milestone.

---

## Target personas

### Priya — the reluctant budgeter
- 28 years old, UX designer, freelance income that varies month to month
- Has tried Walnut, Jupiter, and a spreadsheet. All abandoned within a month.
- Core frustration: "I don't want to manage a system. I just want to know if I'm okay."
- JTBD: When my income is irregular, I want to know if my spending is sustainable right now, so I don't get a nasty surprise at month end.
- Voice query example: "Am I on track this month given I haven't invoiced yet?"

### Arjun — the passive investor
- 34 years old, software engineer, has a Zerodha portfolio of direct equities and mutual funds he rarely checks
- Comfortable with tech, intimidated by financial jargon
- Core frustration: "I know I should rebalance but I never know when or how much."
- JTBD: When markets move, I want to understand what it means for my portfolio in plain English, so I can decide whether to act.
- Voice query example: "My IT sector funds are down 12%. Should I be worried or is this normal?"

### Deepa — the tax anxious self employed
- 41 years old, independent consultant, proprietor filing ITR-3
- Dreads ITR filing every July, poor visibility of deductible expenses throughout the year
- Core frustration: "I only find out I've overpaid or underpaid when it's too late to do anything."
- JTBD: When I am approaching tax season, I want to know what I can legitimately claim under the Income Tax Act, so I don't overpay or get caught out.
- Voice query example: "What home office expenses can I claim this quarter under Section 80?"

---

## User journey (happy path)

1. User opens FinVoice web app and connects their bank via the Account Aggregator (AA) framework.
2. User taps the mic button and speaks a question.
3. Whisper transcribes the audio in under one second.
4. Supervisor agent classifies intent and routes to the correct specialist agent.
5. Specialist agent fetches relevant data (transactions, market prices, tax rules).
6. Response streams to the UI in real time with agent attribution shown ("Spending Analyst").
7. User sees a plain English answer with a confidence indicator and source links.
8. User asks a follow up question. The conversation context is maintained.

---

## Functional requirements

### Must have (v0.1 MVP)

| ID | Requirement |
|----|-------------|
| FR-01 | User can connect a bank account via the Account Aggregator (AA) framework (sandbox) |
| FR-02 | User can type a question and receive a response from the correct specialist agent |
| FR-03 | Supervisor agent routes queries to: Spending Analyst, Investment Advisor, Tax Optimiser, Budget Planner |
| FR-04 | Every response shows which agent answered and what data sources were used |
| FR-05 | Responses stream in real time via WebSocket (no full page refresh) |
| FR-06 | All agent decisions are logged to an audit trail (PostgreSQL) |
| FR-07 | System refuses to give specific investment advice and appends disclaimer: "This is informational only and does not constitute regulated financial advice. Consult a SEBI-registered advisor." |

### Should have (v0.2)

| ID | Requirement |
|----|-------------|
| FR-08 | Voice input via browser mic using Whisper (self hosted) |
| FR-09 | Push to talk button with visual audio waveform feedback |
| FR-10 | Market data enrichment via NSE/BSE (yfinance .NS suffix) for investment related queries |
| FR-11 | Human in the loop confirmation step before any "action" recommendation is shown |

### Could have (v0.3)

| ID | Requirement |
|----|-------------|
| FR-12 | Weekly proactive voice briefing. System initiates a summary without user prompting. |
| FR-13 | Receipt scanning via camera (multimodal input) |
| FR-14 | Export conversation history as PDF |

### Won't have

- Write access to any financial account
- Real (non sandbox) banking data
- Native iOS or Android app

---

## Technical constraints

- **Backend:** Python 3.11+, FastAPI, LangGraph for agent orchestration
- **Frontend:** React 18, TypeScript, WebSocket for streaming
- **Database:** PostgreSQL with pgvector extension for semantic search
- **Voice:** OpenAI Whisper (self hosted, faster whisper for CPU performance)
- **Data APIs:** Account Aggregator framework via Finvu sandbox (banking), NSE/BSE data via yfinance (.NS suffix), CoinGecko (crypto)
- **LLM:** Claude claude-sonnet-4-6 as primary. Groq (Llama 3) as fallback for latency sensitive paths.
- **Deployment:** Docker Compose for local. Railway or Render for live demo.
- **Compliance:** All outputs must include AI disclaimer. PII must not appear in logs.

---

## Assumptions and risks

| # | Assumption or Risk | Mitigation |
|---|-------------------|------------|
| A1 | Account Aggregator sandbox data is sufficient to demo realistic Indian transaction scenarios | Supplement with seeded synthetic transactions if needed |
| A2 | Whisper self hosted runs acceptably on CPU for demo purposes | Fallback to Groq Whisper API if latency is unacceptable |
| R1 | LangGraph complexity may slow initial build velocity | Prototype supervisor routing with a simple if/else classifier first |
| R2 | yfinance rate limits may throttle under demo load | Implement Redis caching with 60 second TTL on all market data calls |
| R3 | SEBI or RBI may consider the app to be providing regulated financial advice | Prominent disclaimer on every response referencing SEBI. No personalised investment recommendations. |

---

## Open questions

- Should the agent attribution UI show the full reasoning chain, or just the agent name?
- What is the right confidence threshold below which the system should say "I'm not sure" rather than answer?
- Should conversation history persist across sessions (requires auth) or reset on each visit?
- Is a guest or demo mode (no Account Aggregator connection, pre seeded Indian transaction data) needed for the open source demo?

---

## Appendix — glossary

| Term | Definition |
|------|------------|
| Supervisor agent | The orchestrating LLM that receives user input, classifies intent, and delegates to specialist agents |
| Specialist agent | A focused LLM with specific tools and data access (spending, investment, tax, budget) |
| JTBD | Jobs To Be Done. A framework for expressing user motivation as "when X, I want Y, so that Z" |
| LangGraph | Python library for building stateful, graph based multi agent systems |
| Account Aggregator (AA) | RBI-mandated data sharing framework allowing users to share bank data with consent. Finvu provides a sandbox environment for testing. |
