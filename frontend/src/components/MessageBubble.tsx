/**
 * MessageBubble — renders a single chat message.
 * Handles user messages, streaming assistant messages, and completed responses.
 */

import React from "react";
import { AgentBadge } from "./AgentBadge";
import type { Message } from "../hooks/useWebSocket";

interface Props {
  message: Message;
}

export function MessageBubble({ message }: Props) {
  const isUser = message.role === "user";

  return (
    <div
      style={{
        display: "flex",
        justifyContent: isUser ? "flex-end" : "flex-start",
        marginBottom: "12px",
      }}
    >
      <div
        style={{
          maxWidth: "72%",
          borderRadius: "12px",
          padding: "10px 14px",
          backgroundColor: isUser ? "#2563EB" : "#F3F4F6",
          color: isUser ? "#fff" : "#111827",
        }}
      >
        {!isUser && message.agent && (
          <div style={{ marginBottom: "4px" }}>
            <AgentBadge agent={message.agent} />
          </div>
        )}
        <p
          style={{
            margin: 0,
            fontSize: "0.95rem",
            lineHeight: 1.55,
            whiteSpace: "pre-wrap",
          }}
        >
          {message.content}
          {message.streaming && (
            <span
              style={{
                display: "inline-block",
                width: "2px",
                height: "1em",
                backgroundColor: "#6B7280",
                marginLeft: "2px",
                verticalAlign: "text-bottom",
                animation: "blink 0.8s step-end infinite",
              }}
            />
          )}
        </p>
      </div>
    </div>
  );
}
