/**
 * AgentBadge — displays which specialist agent generated a response.
 * Shown in the top-left corner of each assistant message bubble.
 */

import React from "react";

const AGENT_LABELS: Record<string, string> = {
  spending_analyst: "Spending Analyst",
  investment_advisor: "Investment Advisor",
  tax_optimizer: "Tax Optimizer",
  budget_planner: "Budget Planner",
  supervisor: "FinVoice",
};

const AGENT_COLOURS: Record<string, string> = {
  spending_analyst: "#2563EB",    // blue
  investment_advisor: "#059669",  // green
  tax_optimizer: "#7C3AED",       // purple
  budget_planner: "#D97706",      // amber
  supervisor: "#6B7280",          // grey
};

interface Props {
  agent: string;
}

export function AgentBadge({ agent }: Props) {
  const label = AGENT_LABELS[agent] ?? agent;
  const colour = AGENT_COLOURS[agent] ?? "#6B7280";

  return (
    <span
      style={{
        display: "inline-block",
        fontSize: "0.7rem",
        fontWeight: 600,
        letterSpacing: "0.03em",
        color: "#fff",
        backgroundColor: colour,
        borderRadius: "4px",
        padding: "2px 8px",
        marginBottom: "4px",
      }}
    >
      {label}
    </span>
  );
}
