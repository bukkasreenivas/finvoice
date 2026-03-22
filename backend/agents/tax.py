"""
Tax Optimizer agent.

Handles queries about Indian income tax: deductions, ITR forms, tax-loss harvesting,
capital gains, and self-assessment guidance under the Income Tax Act and CBDT guidelines.

All responses include the mandatory SEBI/tax disclaimer. This is tracked as a
guardrail metric in the audit log (disclaimer_shown = True).

Example queries:
  "What expenses can I claim as a freelance consultant?"
  "How does LTCG tax work on my equity funds?"
  "Should I opt for the new or old tax regime?"
"""

from __future__ import annotations

from typing import AsyncIterator

from anthropic import AsyncAnthropic

from backend.config import settings

DISCLAIMER = (
    "\n\n---\n*This is informational only and does not constitute regulated tax or "
    "financial advice. Consult a qualified CA or SEBI-registered advisor for "
    "personalised guidance. Tax laws are subject to annual amendments in the Union Budget.*"
)

# Static RAG context covering the most common Indian tax questions.
# In a production system this would be retrieved from a pgvector index built
# from CBDT circulars, Income Tax Act sections, and official CBDT FAQs.
# For the demo, a curated static context covers the key topics.

TAX_CONTEXT = """
Indian Income Tax — key facts (Financial Year 2024-25, AY 2025-26)

TAX REGIMES
New regime (default from FY 2023-24):
  Up to ₹3 lakh: nil
  ₹3-7 lakh: 5%  |  ₹7-10 lakh: 10%  |  ₹10-12 lakh: 15%
  ₹12-15 lakh: 20%  |  Above ₹15 lakh: 30%
  Standard deduction: ₹75,000 for salaried (from FY 2024-25)
  Most deductions (80C, 80D, HRA) not available.

Old regime:
  Up to ₹2.5 lakh: nil  |  ₹2.5-5 lakh: 5%
  ₹5-10 lakh: 20%  |  Above ₹10 lakh: 30%
  All deductions available. Choose if total deductions exceed ₹3.75 lakh.

KEY DEDUCTIONS (old regime only unless stated)
  Section 80C: Up to ₹1.5 lakh. Covers ELSS, PPF, EPF, LIC, NSC, home loan principal, tuition fees.
  Section 80D: Health insurance premiums. Up to ₹25,000 (self/family), ₹50,000 (parents above 60).
  Section 80CCD(1B): Additional ₹50,000 for NPS. Available in both regimes.
  Section 24(b): Home loan interest. Up to ₹2 lakh for self-occupied property.
  HRA: Exempt = min of (actual HRA received, 50%/40% of basic, rent paid minus 10% of basic).

CAPITAL GAINS
  Equity (STT paid) STCG (held < 1 year): 20% (raised from 15% in Budget 2024).
  Equity LTCG (held > 1 year, gains above ₹1.25 lakh): 12.5% (raised from 10% in Budget 2024).
  Debt mutual funds (after Mar 2023 purchase): taxed as income per slab. No indexation.
  Property LTCG (held > 2 years): 12.5% without indexation (Budget 2024 change).

FREELANCERS / SELF-EMPLOYED (ITR-3 or ITR-4)
  Presumptive taxation (Section 44ADA for professionals): 50% of gross receipts deemed profit.
  Deductible business expenses: internet, office rent, software subscriptions, professional development,
  travel for work, professional fees paid to others. Keep receipts and bank records.
  GST registration required if turnover exceeds ₹20 lakh (services).

TAX-LOSS HARVESTING
  Sell underperforming equity positions before 31 March to book STCL or LTCL.
  Short-term capital losses can offset STCG and LTCG.
  Long-term capital losses can offset only LTCG.
  Losses can be carried forward for 8 assessment years if ITR is filed on time.
"""

SYSTEM_PROMPT = f"""You are the Tax Optimizer for FinVoice, a personal finance assistant built for Indian users.

Your role:
- Answer questions about Indian income tax using the context provided below.
- Cite the relevant section (e.g. Section 80C, Section 44ADA) when applicable.
- Use plain language. Define any technical term you introduce (e.g. "LTCG — long-term capital gains").
- Use Indian financial year conventions (FY 2024-25, AY 2025-26).
- If a question falls outside the context provided, say so and suggest consulting a CA.

Tax knowledge base:
{TAX_CONTEXT}

IMPORTANT: Every response must end with the disclaimer that will be appended automatically. Do not add your own disclaimer."""


async def run(
    query: str,
    session_id: str,
) -> AsyncIterator[str]:
    """Stream a response to a tax-related query."""
    client = AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)

    messages = [{"role": "user", "content": query}]

    async with client.messages.stream(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        system=SYSTEM_PROMPT,
        messages=messages,
    ) as stream:
        async for text in stream.text_stream:
            yield text

    yield DISCLAIMER
