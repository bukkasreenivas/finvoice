# Experiment design

This document defines the first A/B experiment for FinVoice: voice input vs text input. It covers the hypothesis, sample size calculation, assignment logic, success criteria, and guardrails.

---

## Experiment overview

| Field | Value |
|---|---|
| Experiment name | voice-vs-text-input |
| Start date | Day one of v0.2 launch |
| Expected duration | Four weeks |
| Owner | Product |
| Status | Planned |

---

## Background

FinVoice is designed as a voice-first interface. The hypothesis is that voice input reduces friction and increases engagement compared to a standard text input. Before committing to voice as the default interaction model, this experiment tests whether users actually prefer it.

---

## Hypothesis

Voice input (push-to-talk) reduces time-to-query by 40% and increases daily active queries per user by 20%, compared to text input.

Time-to-query is defined as the time from page load to the first query submitted in a session.

---

## Experiment design

### Variants

| Variant | Description | Assignment |
|---|---|---|
| Control | Text input only. Standard text box visible. Push-to-talk button hidden. | 50% of new users |
| Treatment | Both text and push-to-talk visible. Push-to-talk is prominently placed above the text box. | 50% of new users |

### Assignment logic

Assignment is random, user-level, and persistent. A user assigned to control stays in control for the full experiment duration. Assignment is made on the user's first session and stored in the `users` table as `experiment_variant`.

New users only. Existing users (anyone who created an account before v0.2 launch) are excluded from the experiment. They receive the treatment (voice available) without being in the experiment cohort.

Assignment is 50/50 using a hash of the user's UUID mod 2. This is deterministic and requires no external feature flag service.

```python
def assign_variant(user_id: str) -> str:
    import hashlib
    digest = int(hashlib.sha256(user_id.encode()).hexdigest(), 16)
    return "treatment" if digest % 2 == 0 else "control"
```

### What is held constant

The following are identical across both variants to isolate the input method as the only variable:

- Agent routing logic and response quality
- UI layout except for the presence of the push-to-talk button
- Onboarding flow
- Response streaming speed

---

## Sample size calculation

Primary metric: daily active queries per user.

Assumptions:
- Baseline (control): 2.0 queries per active user per day (estimated from v0.1 data)
- Minimum detectable effect: 20% increase (target: 2.4 queries per day)
- Standard deviation: 1.5 queries per day (estimated, to be refined with v0.1 data)
- Statistical significance: 95% (α = 0.05, two-tailed)
- Statistical power: 80% (β = 0.20)

Using a two-sample t-test approximation:

n ≈ 2 × ((z_α/2 + z_β) × σ / δ)²
n ≈ 2 × ((1.96 + 0.84) × 1.5 / 0.4)²
n ≈ 2 × (2.80 × 1.5 / 0.4)²
n ≈ 2 × (10.5)²
n ≈ 220 users per variant
n ≈ 440 users total

At an estimated new user rate of 20 users per week post-v0.2 launch, reaching 440 users takes approximately 22 weeks. This is too slow for an initial open source release.

**Adjusted approach for early release context:** run the experiment for four weeks and report directional results rather than statistically significant results. State explicitly in the readout that the sample is insufficient for significance and that the design is the artefact, not the conclusion. This is honest and demonstrates experiment literacy without fabricating a result.

---

## Metrics

### Primary metric

Daily active queries per user (averaged over the experiment period).

### Secondary metrics

| Metric | Rationale |
|---|---|
| Time-to-first-query per session | Direct test of the friction hypothesis |
| Voice adoption rate in treatment | Checks whether treatment users actually use voice |
| Day-seven retention | Checks whether the friction reduction improves return rate |
| Query-to-follow-up rate | Checks whether voice queries generate more engagement |

### Guardrail metrics (must not move adversely)

| Metric | Threshold | Action if breached |
|---|---|---|
| Error rate | > 2% in either variant | Pause experiment, investigate |
| Whisper latency p95 | > 1.5s | Pause experiment, fix transcription pipeline |
| Disclaimer coverage | < 100% on tax/investment responses | Pause experiment, fix immediately |

---

## Analysis plan

Analysis runs at the end of week four. Steps:

1. Pull all `query_submitted` and `voice_query_submitted` events from audit_log for users in the experiment cohort.
2. Calculate per-user daily average query count for each variant.
3. Run a two-sample t-test. Report p-value and 95% confidence interval on the difference.
4. Report voice adoption rate in treatment as a separate descriptive statistic (not a hypothesis test).
5. Report time-to-first-query using median, not mean (right-skewed distribution).
6. If sample < 440, state this explicitly in the readout. Report direction and effect size without claiming significance.

---

## Success criteria

| Criterion | Target | Interpretation |
|---|---|---|
| Daily active queries, treatment > control | ≥ 20% higher | Hypothesis supported |
| Time-to-first-query, treatment < control | ≥ 40% lower | Friction reduction confirmed |
| Voice adoption in treatment | ≥ 50% | Button is discoverable and used |
| No guardrail breached | All within threshold | Experiment ran cleanly |

---

## Failure criteria

The experiment is declared a failure and voice is demoted to secondary input (text first) if:

- Daily active queries in treatment are lower than control, or
- Voice adoption in treatment is below 30% (button not used even when available), or
- Any guardrail metric is breached.

A failed experiment is still a portfolio artefact. The readout documents what the data showed and what the product decision would be. This demonstrates rigorous PM thinking, not just positive outcomes.

---

## Risks and mitigations

| Risk | Mitigation |
|---|---|
| Sample too small for significance | Acknowledged upfront. Report direction and effect size with confidence intervals. |
| Novelty effect inflates treatment results | Note in readout. Recommend a follow-up experiment at week eight to test whether the effect persists. |
| Whisper errors frustrate treatment users | Transcript confirmation step lets users correct errors before submission. Monitor Whisper error rate as a guardrail. |
| Control users discover push-to-talk exists | Assignment is enforced server-side. Control users do not see the button. |
