/**
 * useVoice — browser microphone capture and audio upload.
 *
 * Uses the MediaRecorder API to record audio in WebM format.
 * On stop, POSTs the audio to POST /voice/transcribe and returns the transcript.
 * The transcript is then shown to the user for confirmation before submission.
 */

import { useCallback, useRef, useState } from "react";

const API_URL = process.env.REACT_APP_API_URL || "http://localhost:8000";

export type VoiceState = "idle" | "recording" | "transcribing" | "error";

export function useVoice(onTranscript: (text: string) => void) {
  const [voiceState, setVoiceState] = useState<VoiceState>("idle");
  const [error, setError] = useState<string>("");
  const mediaRecorder = useRef<MediaRecorder | null>(null);
  const audioChunks = useRef<Blob[]>([]);

  const startRecording = useCallback(async () => {
    setError("");
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const recorder = new MediaRecorder(stream, { mimeType: "audio/webm" });

      audioChunks.current = [];

      recorder.ondataavailable = (e) => {
        if (e.data.size > 0) {
          audioChunks.current.push(e.data);
        }
      };

      recorder.onstop = async () => {
        stream.getTracks().forEach((t) => t.stop());
        setVoiceState("transcribing");

        const blob = new Blob(audioChunks.current, { type: "audio/webm" });
        const formData = new FormData();
        formData.append("file", blob, "recording.webm");

        try {
          const response = await fetch(`${API_URL}/voice/transcribe`, {
            method: "POST",
            body: formData,
          });

          if (!response.ok) {
            throw new Error(`Transcription failed: ${response.status}`);
          }

          const data = await response.json();
          onTranscript(data.transcript);
          setVoiceState("idle");
        } catch (err) {
          setError("Transcription failed. Please try again or type your question.");
          setVoiceState("error");
        }
      };

      mediaRecorder.current = recorder;
      recorder.start();
      setVoiceState("recording");
    } catch {
      setError("Microphone access was denied. Please allow mic access and try again.");
      setVoiceState("error");
    }
  }, [onTranscript]);

  const stopRecording = useCallback(() => {
    if (mediaRecorder.current?.state === "recording") {
      mediaRecorder.current.stop();
    }
  }, []);

  return { voiceState, error, startRecording, stopRecording };
}
