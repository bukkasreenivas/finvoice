# AI prompt journal

This journal logs every significant prompt used to build FinVoice. Each entry records the goal, the prompt, a summary of what the AI produced, and the PM decision that followed. The purpose is to demonstrate an AI-native workflow, not to document every token exchanged.

---

## How to read this journal

Each entry follows this structure:

- **Goal** — what problem was being solved at that moment
- **Prompt** — the actual prompt sent, quoted verbatim or close to it
- **Output summary** — what the AI produced (summarised, not pasted in full unless the full output is itself the artefact)
- **PM decision** — what was done with the output and why

---

## Entry 001 — PRD generation

**Date:** 22 March 2026

**Goal:** Produce a full product requirements document for FinVoice without starting from a blank page. The PRD needed to cover problem framing, user personas, functional requirements for four specialist agents, non-functional requirements, and out-of-scope decisions.

**Prompt:**

> "I am building an open source enterprise AI project called FinVoice: a voice-first, multi-agent personal finance assistant targeting the Indian market. The four specialist agents are Spending Analyst, Investment Advisor, Tax Optimizer, and Budget Planner. The tech stack is FastAPI, LangGraph, React, Whisper, and the Account Aggregator framework via Finvu sandbox. Write a full PRD covering problem statement, user personas (Indian context: salaried, self-employed filing ITR-3, gig economy, retiree), functional requirements per agent, non-functional requirements (latency, error rate, SEBI disclaimer coverage), and explicit out-of-scope decisions. Write in Indian English, sentence case headings, no hyphens in sentences, direct tone."

**Output summary:** Claude produced a 12-section PRD covering problem statement, four distinct user personas (salaried professional, self-employed contractor, gig economy worker, retiree), functional requirements per agent with acceptance criteria, non-functional requirements with numeric targets (< 4s latency, < 2% error rate), and a clear out-of-scope section excluding regulated financial advice, real banking data, and mobile native apps.

**PM decision:** Accepted the PRD with two edits. The Investment Advisor section initially framed advice as "personalised recommendations," which is a regulated term under SEBI guidelines in India. Changed to "informational analysis." The latency target was tightened from < 5s to < 4s based on my own sense of what feels acceptable in a voice interaction.

---

## Entry 002 — User research synthesis

**Date:** 22 March 2026

**Goal:** Synthesise seven qualitative user interviews into a structured research document with JTBD (Jobs to Be Done) framing, key insights, and implications for product decisions.

**Prompt:**

> "I conducted seven interviews with potential FinVoice users: two salaried professionals, two self-employed contractors, one gig economy worker, one retiree, and one student. Common themes were: frustration with switching between banking apps, anxiety about tax season, discomfort with financial jargon, and a desire for proactive alerts rather than reactive dashboards. Synthesise this into a user research document. Format: executive summary, participant overview table, JTBD statements (one per persona), key findings with implications, and methodology note. Indian English, sentence case headings, no hyphens."

**Output summary:** Claude produced seven JTBD statements, eight key findings organised by theme (visibility, anxiety, jargon, proactivity), and a methodology section noting the limitations of a seven-person sample. Each finding included an implication for product design.

**PM decision:** The finding on jargon led directly to a design constraint: all agent responses must avoid technical financial terms unless the user introduced the term first. Added this as a non-functional requirement in the PRD.

---

## Entry 003 — Competitive analysis

**Date:** 22 March 2026

**Goal:** Produce a competitive analysis comparing FinVoice against the leading Indian personal finance apps across five dimensions: AI depth, voice input, multi-agent architecture, variable income support, and Indian regulatory fit.

**Prompt:**

> "Write a competitive analysis comparing FinVoice against these five Indian products: CRED, Fi Money (Ask Fi feature), Jupiter, Groww, and Money View. Evaluate each on: AI depth (is it generative AI or rule-based), voice input (exists or not), multi-agent architecture (single LLM or routed specialists), variable income support, and Indian regulatory fit (Account Aggregator support, SEBI and CBDT compliance). Conclude with a differentiation statement for FinVoice in the Indian market. Indian English, table for comparisons, no hyphens."

**Output summary:** Claude produced a five-column comparison table, a narrative section on each competitor, and a differentiation statement positioning FinVoice as the only Indian-market tool with multi-agent routing and voice input built from the ground up.

**PM decision:** The analysis confirmed that no Indian competitor combines voice input with specialist agent routing. Fi Money's Ask Fi is the closest, but it uses a single model and has no tax or investment specialist capabilities. This validated the core product bet. The differentiation statement was used verbatim in the README hero section.

---

## Entry 004 — Architecture decision records

**Date:** 22 March 2026

**Goal:** Document four architecture decisions (LangGraph vs CrewAI, self-hosted Whisper vs managed API, Account Aggregator sandbox only, PostgreSQL + pgvector vs dedicated vector DB) in ADR format to demonstrate technical decision-making.

**Prompt:**

> "Write four ADRs for an enterprise AI open source project targeting the Indian market. ADR-001: LangGraph chosen over CrewAI for agent orchestration, reason is deterministic control flow and audit trails for a regulated finance context. ADR-002: self-hosted Whisper (faster-whisper) chosen over Deepgram, reason is zero cost and no data leaving the system. ADR-003: Account Aggregator framework sandbox only, no real banking data, reason is compliance scope under RBI guidelines. ADR-004: PostgreSQL + pgvector chosen over Pinecone, reason is infrastructure simplicity at demo scale. Format each ADR with: title, status, context, decision, consequences. Indian English."

**Output summary:** Claude produced four ADRs in standard format. Each consequences section covered both positive consequences and trade-offs, which is more honest than ADRs that only list benefits.

**PM decision:** Added the Pinecone migration path note to ADR-004 consequences section. Anyone reading this should see that the simplified choice was made deliberately, not out of ignorance of alternatives.

---

## Entry 005 — Roadmap

**Date:** 22 March 2026

**Goal:** Define three milestone phases with MoSCoW priorities, dependency graphs, and success criteria per milestone.

**Prompt:**

> "Write a product roadmap for FinVoice with three milestones: v0.1 Text MVP (week 4), v0.2 Voice (week 7), v0.3 Proactive (week 10). For each milestone: list features with MoSCoW priority, draw a dependency graph showing what blocks what, and define measurable success criteria. The most critical v0.1 dependency is the LangGraph supervisor agent. Indian English, tables for feature lists, sentence case headings."

**Output summary:** Claude produced feature tables with MoSCoW columns, ASCII dependency graphs, and success criteria with numeric targets for each milestone. It correctly identified the supervisor agent as the single critical path item.

**PM decision:** Added a cross-milestone dependency table that was missing from the initial output. The table maps v0.1 architectural decisions (PostgreSQL schema, WebSocket message format, audit log fields) to which later milestones they constrain. This is the kind of forward-looking thinking the AI did not surface unprompted.

---

## Entry 006 — Metrics framework

**Date:** 22 March 2026

**Goal:** Define the north star metric, guardrail metrics, leading indicators, and instrumentation plan for FinVoice.

**Prompt:**

> "Define a metrics framework for FinVoice. North star: weekly active voice queries per user, target ≥ 3 per user per week by week 6. Guardrails: response latency p95 < 4s, error rate < 2%, disclaimer shown 100% on regulated responses. Leading indicators: day-one retention, query-to-follow-up rate, agent routing accuracy, voice adoption rate. For each metric: definition, target, instrumentation (what event to log and what fields). Also define a minimal PostgreSQL schema for the audit_log table that captures all metrics. Indian English."

**Output summary:** Claude produced metric definitions, targets, and instrumentation notes for all metrics, plus a PostgreSQL CREATE TABLE statement for the audit_log. The schema included `disclaimer_shown` as a boolean field, which was a good catch for the regulatory guardrail.

**PM decision:** Changed the voice adoption target from "30% by week 8" (Claude's suggestion) to "50% by week 8." The lower target felt like covering for a weak feature. If fewer than half of active users try voice at least once, the feature has not landed.

---

## Entry 007 — Experiment design

**Date:** 22 March 2026

**Goal:** Design an A/B experiment for voice input vs text input, including hypothesis, sample size calculation, assignment logic, success and failure criteria.

**Prompt:**

> "Design an A/B experiment for FinVoice testing voice input (push-to-talk) vs text input only. Hypothesis: voice reduces time-to-query by 40% and increases daily active queries by 20%. Include: variant descriptions, assignment logic using a hash of user UUID, sample size calculation using a two-sample t-test (baseline 2.0 queries/day, MDE 20%, σ 1.5, α 0.05, power 80%), primary and secondary metrics, guardrail metrics, analysis plan, success criteria, and explicit failure criteria. Acknowledge that an early open source release will not reach statistical significance and explain how to handle that honestly. Indian English."

**Output summary:** Claude produced a complete experiment design document. The sample size calculation was correct (≈ 220 per variant). The section on handling insufficient sample size was well-framed: report direction and effect size with confidence intervals, not a binary significant/not-significant conclusion.

**PM decision:** Added the "failure criteria" section after reviewing the initial output. The AI produced success criteria but not failure criteria. A well-designed experiment defines in advance what would cause a product pivot. This gap is common in AI-generated experiment designs and worth noting as a prompt refinement for next time.

---

## Patterns observed

Across seven entries, three patterns are worth noting for anyone building an AI-native PM workflow.

**The AI produces structure well, not substance.** Frameworks, tables, ADR formats, and schema skeletons come out correctly on the first pass. The substance (what goes in the cells, what the actual decision is) requires domain knowledge that the AI does not have. The most valuable human contribution is the constraint: "the Investment Advisor response must not use the word recommendation because it is regulated by SEBI in India."

**Explicit style instructions work.** Specifying Indian English, no hyphens, sentence case, and direct tone in every prompt produced consistent output across all seven documents. Without explicit style instructions, the AI defaults to American English and marketing tone.

**Failure criteria and negative cases require prompting.** The AI consistently produced the positive-case documentation (success criteria, benefits, what works) without prompting. Failure criteria, trade-offs, and "what if this does not work" sections required explicit instruction. This is a useful heuristic: after any AI-generated document, ask yourself whether the failure case is documented.
