/**
 * useWebSocket — manages the WebSocket connection to the FinVoice backend.
 *
 * Responsibilities:
 * - Open and maintain the connection to /chat/ws
 * - Send user messages
 * - Receive streaming token chunks and accumulate them per agent
 * - Signal completion when done=true is received
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

  const connect = useCallback(() => {
    if (ws.current?.readyState === WebSocket.OPEN) return;

    ws.current = new WebSocket(`${WS_URL}/chat/ws`);

    ws.current.onopen = () => {
      setConnected(true);
    };

    ws.current.onclose = () => {
      setConnected(false);
      // Reconnect after two seconds
      setTimeout(connect, 2000);
    };

    ws.current.onerror = () => {
      ws.current?.close();
    };

    ws.current.onmessage = (event) => {
      const data: StreamToken = JSON.parse(event.data);

      if (data.session_id && !sessionId) {
        setSessionId(data.session_id);
      }

      if (data.done) {
        // Mark the last message as no longer streaming
        setMessages((prev) =>
          prev.map((m, i) =>
            i === prev.length - 1 ? { ...m, streaming: false } : m
          )
        );
        return;
      }

      setMessages((prev) => {
        const last = prev[prev.length - 1];
        if (last?.role === "assistant" && last.streaming) {
          // Append token to the current streaming message
          const updated = [...prev];
          updated[updated.length - 1] = {
            ...last,
            content: last.content + data.token,
            agent: data.agent,
          };
          return updated;
        }
        // Start a new assistant message
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
  }, [sessionId]);

  useEffect(() => {
    connect();
    return () => {
      ws.current?.close();
    };
  }, [connect]);

  const sendMessage = useCallback(
    (text: string, inputMode: "text" | "voice" = "text") => {
      if (ws.current?.readyState !== WebSocket.OPEN) return;

      // Append user message optimistically
      setMessages((prev) => [...prev, { role: "user", content: text }]);

      ws.current.send(
        JSON.stringify({
          message: text,
          session_id: sessionId || undefined,
          input_mode: inputMode,
        })
      );
    },
    [sessionId]
  );

  return { connected, messages, sendMessage, sessionId };
}
