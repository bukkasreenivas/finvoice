/**
 * useWebSocket — manages the WebSocket connection to the FinVoice backend.
 *
 * Responsibilities:
 * - Open and maintain the connection to /chat/ws
 * - Send user messages
 * - Receive streaming token chunks and accumulate them per agent
 * - Signal completion when done=true is received
 *
 * Design notes:
 * - connect() has no state dependencies so it is stable across renders.
 *   sessionId is held in a ref so the onmessage closure can read the
 *   latest value without causing connect() to be recreated.
 * - connectRef always points to the current connect() so the onclose
 *   reconnect timer never holds a stale closure.
 * - Empty keepalive tokens (token: "") are filtered before updating
 *   the message list to prevent blank assistant bubbles.
 */

import { useCallback, useEffect, useRef, useState } from "react";

export interface StreamToken {
  token: string;
  agent: string;
  session_id: string;
  done: boolean;
}

export interface Message {
  role: "user" | "assistant";
  content: string;
  agent?: string;
  streaming?: boolean;
}

const WS_URL = process.env.REACT_APP_WS_URL || "ws://localhost:8000";

export function useWebSocket() {
  const ws = useRef<WebSocket | null>(null);
  const [connected, setConnected] = useState(false);
  const [messages, setMessages] = useState<Message[]>([]);
  const [sessionId, setSessionId] = useState<string>("");

  // Mirror sessionId in a ref so onmessage can read the latest value
  // without connect() taking a dependency on sessionId state.
  const sessionIdRef = useRef<string>("");

  // Always holds the current connect function so onclose can call it
  // even after connect() is recreated (though with [] deps it never is).
  const connectRef = useRef<() => void>(() => {});

  const connect = useCallback(() => {
    // Do not open a second connection if one is already live or connecting.
    if (
      ws.current?.readyState === WebSocket.OPEN ||
      ws.current?.readyState === WebSocket.CONNECTING
    ) {
      return;
    }

    console.log("[FinVoice] connecting to", `${WS_URL}/chat/ws`);
    ws.current = new WebSocket(`${WS_URL}/chat/ws`);

    ws.current.onopen = () => {
      console.log("[FinVoice] connection open");
      setConnected(true);
    };

    ws.current.onclose = (event) => {
      console.log("[FinVoice] connection closed code=%d reason=%s", event.code, event.reason);
      setConnected(false);
      // Use connectRef so we always call the latest version of connect.
      setTimeout(() => connectRef.current(), 2000);
    };

    ws.current.onerror = (event) => {
      console.error("[FinVoice] ws error", event);
      ws.current?.close();
    };

    ws.current.onmessage = (event) => {
      let data: StreamToken;
      try {
        data = JSON.parse(event.data) as StreamToken;
      } catch (err) {
        console.error("[FinVoice] failed to parse message", event.data, err);
        return;
      }

      console.log(
        "[FinVoice] message received done=%s agent=%s tokenLen=%d",
        data.done,
        data.agent,
        data.token.length
      );

      // Capture session ID from the first message that carries one.
      if (data.session_id && !sessionIdRef.current) {
        sessionIdRef.current = data.session_id;
        setSessionId(data.session_id);
      }

      if (data.done) {
        // Mark the last message as no longer streaming.
        setMessages((prev) =>
          prev.map((m, i) =>
            i === prev.length - 1 ? { ...m, streaming: false } : m
          )
        );
        return;
      }

      // Filter out empty keepalive tokens — they carry no content.
      if (!data.token) return;

      setMessages((prev) => {
        const last = prev[prev.length - 1];
        if (last?.role === "assistant" && last.streaming) {
          // Append to the in-progress assistant message.
          const updated = [...prev];
          updated[updated.length - 1] = {
            ...last,
            content: last.content + data.token,
            agent: data.agent,
          };
          return updated;
        }
        // Start a new assistant message.
        return [
          ...prev,
          {
            role: "assistant",
            content: data.token,
            agent: data.agent,
            streaming: true,
          },
        ];
      });
    };
  }, []); // No state dependencies — connect() is stable for the component lifetime.

  // Keep connectRef current whenever connect() is recreated (currently never,
  // but this guard is cheap and makes the reconnect logic safe by default).
  useEffect(() => {
    connectRef.current = connect;
  }, [connect]);

  useEffect(() => {
    connect();
    return () => {
      ws.current?.close();
    };
  }, [connect]);

  const sendMessage = useCallback(
    (text: string, inputMode: "text" | "voice" = "text") => {
      console.log(
        "[FinVoice] sendMessage readyState=%d text=%s",
        ws.current?.readyState,
        text.slice(0, 60)
      );

      if (ws.current?.readyState !== WebSocket.OPEN) {
        console.warn("[FinVoice] send skipped: socket not open (readyState=%d)", ws.current?.readyState);
        return;
      }

      // Append the user message optimistically before the round trip.
      setMessages((prev) => [...prev, { role: "user", content: text }]);

      const payload = JSON.stringify({
        message: text,
        session_id: sessionIdRef.current || undefined,
        input_mode: inputMode,
      });

      console.log("[FinVoice] sending payload:", payload);
      ws.current.send(payload);
    },
    [] // Uses sessionIdRef — no state dependency needed.
  );

  return { connected, messages, sendMessage, sessionId };
}
