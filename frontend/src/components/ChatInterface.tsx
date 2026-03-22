/**
 * ChatInterface — main chat UI component.
 *
 * Layout:
 *   - Message list (scrollable)
 *   - Input row: voice button | text input | send button
 *
 * After a voice transcript is received it is placed in the text input
 * for the user to review and edit before sending. This deliberate step
 * prevents Whisper transcription errors from silently reaching the agents.
 */

import React, { useEffect, useRef, useState } from "react";
import { MessageBubble } from "./MessageBubble";
import { VoiceInput } from "./VoiceInput";
import { useWebSocket } from "../hooks/useWebSocket";

export function ChatInterface() {
  const { connected, messages, sendMessage } = useWebSocket();
  const [input, setInput] = useState("");
  const [pendingVoice, setPendingVoice] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  // Scroll to bottom whenever messages update
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSend = () => {
    const text = input.trim();
    if (!text || !connected) return;
    sendMessage(text, pendingVoice ? "voice" : "text");
    setInput("");
    setPendingVoice(false);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleTranscript = (text: string) => {
    setInput(text);
    setPendingVoice(true);
  };

  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        height: "100vh",
        maxWidth: "760px",
        margin: "0 auto",
        fontFamily: "'Inter', 'Segoe UI', sans-serif",
      }}
    >
      {/* Header */}
      <div
        style={{
          padding: "16px 20px",
          borderBottom: "1px solid #E5E7EB",
          display: "flex",
          alignItems: "center",
          gap: "10px",
        }}
      >
        <span style={{ fontSize: "1.4rem" }}>💬</span>
        <div>
          <h1 style={{ margin: 0, fontSize: "1.1rem", fontWeight: 700 }}>FinVoice</h1>
          <p style={{ margin: 0, fontSize: "0.78rem", color: "#6B7280" }}>
            {connected ? "Connected" : "Reconnecting…"}
          </p>
        </div>
      </div>

      {/* Message list */}
      <div
        style={{
          flex: 1,
          overflowY: "auto",
          padding: "20px",
        }}
      >
        {messages.length === 0 && (
          <div style={{ textAlign: "center", color: "#9CA3AF", marginTop: "60px" }}>
            <p style={{ fontSize: "1.5rem", margin: "0 0 8px" }}>🇮🇳</p>
            <p style={{ margin: 0 }}>Ask me about your spending, investments, taxes, or budget.</p>
            <p style={{ margin: "4px 0 0", fontSize: "0.85rem" }}>
              Try: "Where did I spend the most last month?"
            </p>
          </div>
        )}
        {messages.map((msg, i) => (
          <MessageBubble key={i} message={msg} />
        ))}
        <div ref={bottomRef} />
      </div>

      {/* Input row */}
      <div
        style={{
          padding: "12px 16px",
          borderTop: "1px solid #E5E7EB",
          display: "flex",
          alignItems: "center",
          gap: "10px",
          backgroundColor: "#fff",
        }}
      >
        <VoiceInput onTranscript={handleTranscript} disabled={!connected} />

        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={pendingVoice ? "Review transcript then press send…" : "Type a question…"}
          disabled={!connected}
          style={{
            flex: 1,
            padding: "10px 14px",
            borderRadius: "24px",
            border: "1px solid #D1D5DB",
            fontSize: "0.95rem",
            outline: "none",
            backgroundColor: pendingVoice ? "#EFF6FF" : "#fff",
          }}
        />

        <button
          onClick={handleSend}
          disabled={!connected || !input.trim()}
          style={{
            padding: "10px 18px",
            borderRadius: "24px",
            border: "none",
            backgroundColor: "#2563EB",
            color: "#fff",
            fontWeight: 600,
            cursor: !connected || !input.trim() ? "not-allowed" : "pointer",
            opacity: !connected || !input.trim() ? 0.5 : 1,
          }}
        >
          Send
        </button>
      </div>
    </div>
  );
}
