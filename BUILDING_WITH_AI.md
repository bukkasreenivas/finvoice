# Building with AI

Author: Sreenivas Bukka, Product Manager

This document is a practitioner's account of how Claude was used to build FinVoice. It is not a product launch announcement. It is a record of what worked, what did not work, what required human judgement, and what I would do differently next time.

---

## Why this document exists

FinVoice is an open source project demonstrating enterprise-grade AI-native product and engineering skills. The code and the docs show what was built. This document explains how it was built, which is a different and arguably more useful signal.

AI-native development is not "use AI to write code faster." It is a change in how discovery, architecture, documentation, and iteration happen. This document makes that change visible.

---

## Discovery

The discovery phase produced three documents: a PRD, a user research synthesis, and a competitive analysis. All three were written with Claude in a single session.

The process was not "ask Claude to write a PRD and accept the output." The process was:

1. Define the constraints clearly before prompting. For FinVoice, the constraints were: Indian English, no hyphens in sentences, sentence case headings, direct tone, explicit regulatory acknowledgements (no "personalised recommendations," always include the not-regulated-advice disclaimer on tax and investment content).

2. Prompt for structure first, then substance. A prompt that asks for "a PRD" produces something generic. A prompt that specifies the sections, the audience, the numeric targets, and the tone produces something usable.

3. Edit for domain knowledge. The AI produced the right structure and the right format. The human contribution was the substance that requires context: which latency target is acceptable for a voice interface (4s, not 5s), which word is regulated in the Indian context ("recommendation" is regulated by SEBI), which competitor is actually the closest parallel (Fi Money's Ask Fi, not a global app).

The competitive analysis is an example of this pattern. Claude correctly identified that no Indian competitor combines voice input with multi-agent routing. That observation is accurate. But the framing, the differentiation statement, and the decision to use it in the README required a judgement call that the AI could not make: is this differentiation durable, or is Fi Money going to add multi-agent AI to Ask Fi in six months?

---

## Architecture

Architecture decisions were made by the human. The AI documented them.

The four ADRs in CLAUDE.md (LangGraph over CrewAI, self-hosted Whisper, Account Aggregator sandbox only, PostgreSQL + pgvector) were decisions I made based on prior experience with regulated systems and open source project constraints. I then asked Claude to write them up in ADR format with a context, decision, and consequences section.

The consequences sections were genuinely useful. Claude surfaced trade-offs I had not articulated explicitly. For ADR-004 (pgvector over Pinecone), it noted that pgvector query performance degrades significantly above one million vectors. For a demo project with synthetic Indian transaction data, this is not a constraint. For a production system, it is. Documenting this distinction is what separates a thoughtful ADR from a post-hoc justification.

LangGraph was chosen over CrewAI because LangGraph provides a deterministic state machine model. In a regulated finance context, you need to be able to audit exactly what happened at each step of a query. CrewAI's agent autonomy model makes that harder. I knew this from reading the LangGraph documentation. Claude did not surface this reasoning unprompted. It required explicit instruction: "the reason is deterministic control flow and audit trails for a finance context."

This is the most important pattern in AI-assisted architecture work. The AI can generate the document. The AI cannot generate the reasoning unless the reasoning is provided. If you are using AI to make architecture decisions, not just document them, you are outsourcing judgement to a model that does not know your production constraints, your team's strengths, or your regulatory environment.

---

## Documentation

The metrics framework and experiment design were the two most technically demanding documentation tasks. Both required numeric targets that the AI generated correctly as starting points and the human adjusted based on product intuition.

For metrics, the AI suggested a voice adoption target of 30% by week eight. I changed it to 50%. The reasoning: if fewer than half of active users try voice at least once in the week after launch, the feature has not landed. 30% is a target that covers for a weak feature rather than demanding the feature work. The AI does not have this intuition. The human does.

For experiment design, the AI produced success criteria but not failure criteria. This is a consistent gap in AI-generated experiment designs. Failure criteria force the designer to commit in advance to what would cause a pivot. The AI tends to avoid this because it requires negative commitment. I added the failure criteria section after reviewing the initial output. The heuristic I now use: after any AI-generated strategy document, ask explicitly "what would make this fail and what would we do if it did?"

The AI prompt journal (docs/ai-prompt-journal.md) was written last and is perhaps the most honest artefact in the project. It logs every significant prompt with its output and the PM decision that followed. Writing it revealed a pattern: the AI is consistently strong on structure (tables, frameworks, schemas) and consistently requires human contribution on substance (what goes in the cells, what the trade-offs actually are, what the failure cases look like).

---

## Code generation

Code generation for FinVoice follows the same pattern as documentation. The AI generates the structure. The human specifies the constraints.

For the FastAPI backend, the prompt pattern is: "Write a FastAPI endpoint for POST /voice/transcribe. It receives a multipart file upload, passes it to faster-whisper for transcription, and returns the transcript as JSON. Handle the case where the file is not an audio file with a 422 response. Do not use global state." The "do not use global state" constraint is the kind of thing that prevents a subtle production bug. The AI will not add it unprompted.

For the LangGraph supervisor agent, the prompt pattern is: "Write a LangGraph StateGraph for a supervisor agent that routes financial queries to one of four specialist agents: spending, investment, tax, or budget. The routing decision must be logged to the audit_log table before the specialist agent is called, not after. The state must include the original query text, the routed agent name, the supervisor confidence score, and the specialist agent response." The "before, not after" constraint matters because if the specialist agent call fails, you need the audit log entry to diagnose what was routed. The AI does not know this unless you tell it.

---

## What I would do differently

Three things.

First, prompt for failure cases explicitly in every document. The gap between success criteria and failure criteria is consistent enough that I should add it as a standard prompt suffix: "Include explicit failure criteria. What would make this fail, and what would the response be?"

Second, version the prompts. The ai-prompt-journal.md captures the prompts used for this project. Future projects should have the same journal from the start, not written retrospectively. Reconstructing a prompt from memory is less accurate than logging it at the time.

Third, use AI for code review, not just code generation. After generating a FastAPI endpoint or a LangGraph graph, asking Claude "review this for security vulnerabilities, race conditions, and compliance gaps" surfaces issues that would otherwise require a human reviewer with domain expertise. This is underused in most AI-native workflows.

---

## Skills demonstrated

This project and this document demonstrate the following enterprise AI capabilities:

- Multi-agent orchestration using LangGraph StateGraph with deterministic routing and audit logging
- RAG over structured transaction data using PostgreSQL and pgvector
- Voice and multimodal input using self-hosted Whisper via faster-whisper
- Real-time streaming using FastAPI WebSockets and React hooks
- AI-native PM workflow: PRD, user research, competitive analysis, metrics, and experiment design all produced with Claude, with documented human decisions at each stage
- Regulatory awareness: disclaimer coverage, audit logging, and ADR documentation of compliance scope decisions
- Honest evaluation of AI tooling: this document does not claim AI wrote the project. It documents what AI did well, what required human contribution, and what the workflow looks like in practice.
