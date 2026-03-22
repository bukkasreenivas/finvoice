# User research summary — FinVoice

**Research type:** Exploratory qualitative interviews and competitive usability audit  
**Conducted:** February to March 2026  
**Participants:** 7 interviews (simulated representative profiles)  
**Author:** Sreenivas Bukka — Product Manager

---

## Research goals

1. Understand why people abandon personal finance apps after initial setup.
2. Identify the moments where financial anxiety peaks and what people do in those moments.
3. Test appetite for voice as a primary input modality for financial questions.
4. Understand trust thresholds for AI generated financial guidance.

---

## Key findings

### Finding 1 — Dashboards are the problem, not the solution

Every participant described their relationship with finance apps as "checking in" rather than "using." The most common pattern: open the app, look at the numbers, close the app, feel neither better nor worse informed.

> "I open Fi Money, see I spent ₹200 more than last month, and I still don't know if that's fine or not. I close it feeling vaguely anxious." — Participant 4, 31, marketing manager

> "The dashboard is always in the past. It tells me what happened. It doesn't tell me what to do." — Participant 6, 38, consultant

**Implication for FinVoice:** The product must answer the question behind the question. Not "you spent ₹340 on dining" but "your dining spend is 12% over your rolling average. Here is what that means for your end of month position."

---

### Finding 2 — Voice is already how people process money stress

Six of seven participants described calling or texting a friend, partner, or family member when they felt financially uncertain — not opening an app.

> "When I'm worried about money I call my mum. She doesn't know more than me but just saying it out loud helps me think." — Participant 2, 26, freelance designer

> "I have a WhatsApp group with my two closest friends. We talk about money there. No app has ever felt like that." — Participant 7, 44, teacher

**Implication for FinVoice:** Voice input is not a gimmick. It maps directly to the existing behaviour of processing financial stress conversationally. The product should feel like a knowledgeable friend who happens to have your bank data open.

---

### Finding 3 — Trust in AI for finance follows a clear threshold

Participants were consistently comfortable with AI answering descriptive and comparative questions ("how much did I spend?", "is this normal?"). Trust dropped sharply for prescriptive recommendations ("you should sell this", "put ₹500 in savings now").

> "I'd trust it to tell me what's going on. I wouldn't trust it to tell me what to do." — Participant 1, 29, software engineer

> "If it said 'you should move your mutual fund holdings', I'd want to know why, and I'd want a human to have a look before I did anything." — Participant 5, 42, project manager

**Implication for FinVoice:** The human in the loop confirmation step (FR-11) is not just a compliance feature. It is what users actually want. Frame it as a feature, not a disclaimer.

---

### Finding 4 — The "explain like I'm not a finance person" need is universal

All seven participants, regardless of income or financial literacy, expressed a desire for plain English. Financial jargon was cited as a trust breaker.

> "The moment an app says 'your expense ratio' without explaining it, I feel stupid and I close it." — Participant 3, 33, nurse

**Implication for FinVoice:** Agent responses must default to plain English. Financial terms should be defined inline, not assumed. The Investment Advisor agent in particular needs a "explain this simply" mode built into its system prompt.

---

### Finding 5 — Irregular income creates acute anxiety that existing apps ignore

Three of seven participants were self employed or had variable income. All three described existing apps as designed for salaried employees.

> "Every app assumes I get paid the same amount every month. I don't. So the budget feature is useless." — Participant 4, 31, marketing manager

> "I have feast and famine months. I need to know if I can afford a quiet month, not if I've hit a fixed budget." — Participant 6, 38, consultant

**Implication for FinVoice:** The Budget Planner agent must handle variable income natively. "Am I okay this month?" should produce a probabilistic answer based on historical income variance, not a fixed budget comparison.

---

## Jobs To Be Done (JTBD) summary

| Persona | Situation | Motivation | Expected outcome |
|---------|-----------|------------|-----------------|
| Priya (freelancer) | When my income is irregular | I want to know if my spending is sustainable right now | So I don't get a nasty surprise at month end |
| Arjun (passive investor) | When markets move | I want to understand what it means for my portfolio in plain English | So I can decide whether to act without feeling overwhelmed |
| Deepa (self employed) | When approaching ITR filing season | I want to know what I can legitimately claim under the Income Tax Act | So I don't overpay or get caught out |
| General (all) | When I feel financial anxiety | I want to speak my worry and get a grounded answer | So the anxiety is replaced with clarity |

---

## Competitive usability audit

Five products were assessed: Fi Money, CRED, Jupiter, Groww, and Money View. Each was evaluated on five dimensions.

| Dimension | Fi Money | CRED | Jupiter | Groww | FinVoice target |
|-----------|---------|---------|------|------|-----------------|
| Voice input | None | None | None | None | Push to talk with Whisper |
| AI depth | Single model, chat | None | None | None | Multi agent specialised |
| Answer quality | Conversational | Descriptive | Descriptive | Descriptive | Reasoned and attributed |
| Irregular income support | Poor | Poor | Poor | None | Native variable income mode |
| Trust mechanics | Tone only | None | None | None | Agent attribution and confidence |

**Key gap FinVoice fills:** No existing Indian consumer product combines voice input, multi agent reasoning, and trust transparent responses. The closest is Fi Money's Ask Fi (conversational interface) but it lacks agent depth, voice input, and tax or investment specialist capabilities.

---

## Pain point severity matrix

| Pain point | Frequency | Severity | FinVoice addresses? |
|------------|-----------|----------|---------------------|
| Dashboards don't answer "so what?" | 7 of 7 | High | Yes. Agent responses are prescriptive, not descriptive. |
| No voice interface | 6 of 7 | Medium | Yes. v0.2 push to talk. |
| Jargon and complexity | 7 of 7 | High | Yes. Plain English system prompts. |
| Irregular income not supported | 3 of 7 | High (for segment) | Yes. Variable income Budget Planner. |
| Fear of acting on AI advice | 5 of 7 | High | Yes. HITL confirmation and disclaimer. |
| App churn after setup | 7 of 7 | High | Addressed via weekly proactive briefings (v0.3). |

---

## Research limitations

- Interviews were conducted with simulated representative profiles rather than recruited participants. Findings should be validated with real user research before v1 launch decisions.
- Sample skews towards the 26 to 44 age range and Indian context. Findings may not generalise to other demographics or geographies.
- Usability audit was heuristic, not task based. Quantitative usability testing is recommended for v0.2.

---

## Recommended next steps

1. Validate Finding 2 (voice as natural financial processing) with a prototype usability test using the v0.1 text interface before investing in voice infrastructure.
2. Co design the "human in the loop confirmation" UI pattern with three to five participants from the self employed segment.
3. Define the plain English style guide for agent responses before writing system prompts.
