import React from "react";
import { ChatInterface } from "./components/ChatInterface";

export default function App() {
  return (
    <>
      <style>{`
        * { box-sizing: border-box; }
        body { margin: 0; background: #F9FAFB; }
        @keyframes blink {
          0%, 100% { opacity: 1; }
          50% { opacity: 0; }
        }
      `}</style>
      <ChatInterface />
    </>
  );
}
