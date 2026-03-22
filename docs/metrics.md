# Metrics

This document defines how FinVoice measures success. Every metric has a target, a rationale, and an instrumentation plan. A metric without instrumentation is a guess.

---

## North star metric

**Weekly active voice queries per user**

Target: ≥ 3 voice queries per active user per week by the end of week six.

This metric was chosen because it captures both retention (the user came back) and the core value proposition (they used voice, not just text). A user who types but never speaks has not experienced what FinVoice is for. A user who speaks once and never returns has not found ongoing value.

Active user is defined as a user who has logged in at least once in the past seven days.

---

## Guardrail metrics

These are constraints, not goals. If any guardrail is breached, the relevant feature is paused for investigation regardless of north star performance.

| Metric | Threshold | Why it is a guardrail |
|---|---|---|
| End-to-end response latency (p95) | < 4s | Above this, voice interaction feels broken. Users abandon rather than retry. |
| Error rate (5xx responses / total requests) | < 2% | A finance app that errors frequently destroys trust faster than any UX failure. |
| Disclaimer shown on tax and investment responses | 100% | Regulatory. Not negotiable. Every response from Tax Optimizer and Investment Advisor must include the not-regulated-advice disclaimer. |
| Whisper transcription latency (p95) | < 1.5s for a 10-second clip | Longer than this and the push-to-talk UX feels broken. Users stop using voice. |

---

## Leading indicators

Leading indicators move before the north star moves. They are checked weekly to identify problems before they compound.

### Day-one retention

Definition: percentage of users who return on day two after their first session.

Target: ≥ 40% by v0.1 launch.

Instrumentation: log `session_start` event with `user_id` and `session_date`. Join on subsequent day to determine return.

Implication: if day-one retention is below 40%, the onboarding flow or the first-response quality is failing. Investigate before optimising the north star.

### Query-to-follow-up rate

Definition: percentage of queries followed by a second query from the same user within five minutes.

Target: ≥ 25%.

Instrumentation: log `query_submitted` with `user_id` and `timestamp`. A follow-up is any second event within 300 seconds of the first.

Implication: follow-up queries indicate the first response created curiosity or prompted action. Low follow-up rate suggests responses are either complete dead-ends or not useful enough to engage with.

### Agent routing accuracy

Definition: percentage of queries routed to the subjectively correct specialist agent, as assessed by manual audit of a weekly random sample.

Target: ≥ 90% on a 20-query weekly sample.

Instrumentation: log `agent_routed` event with `user_id`, `query_text`, `agent_name`, and `supervisor_confidence`. Flag low-confidence routings for manual review.

Implication: routing errors erode trust. A spending question answered by the Investment Advisor produces a wrong answer and a confused user. Below 90%, the supervisor routing logic needs retraining or prompt revision.

### Voice adoption rate

Definition: percentage of active users who submit at least one voice query in a given week.

Target: ≥ 50% of active users by end of week eight (one week after v0.2 launch).

Instrumentation: log `voice_query_submitted` event distinct from `text_query_submitted`. Voice adoption rate = users with ≥ 1 voice event / total active users.

Implication: low adoption means the push-to-talk button is not discoverable or the transcript confirmation step is too much friction. If < 30% of users try voice at all, investigate UI placement before optimising transcription quality.

---

## Instrumentation plan

All events are logged to the `audit_log` table in PostgreSQL. The schema below captures the minimum fields needed for every metric above.

```sql
CREATE TABLE audit_log (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID NOT NULL,
    session_id      UUID NOT NULL,
    event_type      TEXT NOT NULL,          -- 'query_submitted', 'voice_query_submitted', 'agent_routed', 'session_start'
    agent_name      TEXT,                   -- NULL for non-routing events
    query_text      TEXT,                   -- NULL for session_start
    latency_ms      INTEGER,               -- NULL where not applicable
    error_code      TEXT,                   -- NULL on success
    disclaimer_shown BOOLEAN,              -- TRUE/FALSE for tax and investment responses
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

No third-party analytics tool is used in v0.1. All queries run directly against this table. This keeps the demo self-contained and avoids sending user data to external services.

---

## Metric review cadence

| Cadence | What is reviewed |
|---|---|
| Daily (automated) | Error rate, Whisper latency p95, disclaimer coverage |
| Weekly (manual) | North star, day-one retention, query-to-follow-up rate, routing accuracy sample |
| Per milestone | Voice adoption rate, full metric dashboard review |

Daily automated checks run as a cron job that queries the audit_log table and logs results to the application console. No alerting infrastructure is built in v0.1. The weekly review is a manual SQL query by the developer.
