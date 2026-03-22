/**
 * VoiceInput — push-to-talk button with recording state feedback.
 *
 * On mousedown/touchstart: starts recording.
 * On mouseup/touchend: stops recording and triggers transcription.
 * Shows a pulsing animation while recording.
 * Shows a spinner while transcribing.
 * Returns the transcript via onTranscript callback for user confirmation.
 */

import React from "react";
import { useVoice, VoiceState } from "../hooks/useVoice";

interface Props {
  onTranscript: (text: string) => void;
  disabled?: boolean;
}

const BUTTON_LABEL: Record<VoiceState, string> = {
  idle: "Hold to speak",
  recording: "Recording…",
  transcribing: "Transcribing…",
  error: "Try again",
};

export function VoiceInput({ onTranscript, disabled }: Props) {
  const { voiceState, error, startRecording, stopRecording } = useVoice(onTranscript);
  const isRecording = voiceState === "recording";
  const isBusy = voiceState === "transcribing";

  return (
    <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: "4px" }}>
      <button
        onMouseDown={startRecording}
        onMouseUp={stopRecording}
        onTouchStart={startRecording}
        onTouchEnd={stopRecording}
        disabled={disabled || isBusy}
        aria-label={BUTTON_LABEL[voiceState]}
        style={{
          width: "48px",
          height: "48px",
          borderRadius: "50%",
          border: "none",
          cursor: disabled || isBusy ? "not-allowed" : "pointer",
          backgroundColor: isRecording ? "#EF4444" : "#2563EB",
          color: "#fff",
          fontSize: "1.3rem",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          boxShadow: isRecording ? "0 0 0 6px rgba(239,68,68,0.3)" : "none",
          transition: "background-color 0.2s, box-shadow 0.2s",
          flexShrink: 0,
        }}
      >
        {isBusy ? "⋯" : "🎤"}
      </button>
      {error && (
        <p style={{ fontSize: "0.75rem", color: "#EF4444", margin: 0, maxWidth: "200px", textAlign: "center" }}>
          {error}
        </p>
      )}
    </div>
  );
}
