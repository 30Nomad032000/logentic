import { useState, useRef, useCallback } from "react";

export interface AudioRecorderState {
  isRecording: boolean;
  audioBlob: Blob | null;
  error: string | null;
  stream: MediaStream | null;
  startRecording: () => Promise<void>;
  stopRecording: () => void;
  clearAudio: () => void;
}

export function useAudioRecorder(): AudioRecorderState {
  const [isRecording, setIsRecording] = useState(false);
  const [audioBlob, setAudioBlob] = useState<Blob | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [stream, setStream] = useState<MediaStream | null>(null);

  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);

  const startRecording = useCallback(async () => {
    setError(null);
    setAudioBlob(null);
    chunksRef.current = [];

    try {
      const mediaStream = await navigator.mediaDevices.getUserMedia({ audio: true });
      setStream(mediaStream);

      // Prefer WAV-compatible mime types, fall back to whatever is available
      const mimeType = MediaRecorder.isTypeSupported("audio/webm;codecs=opus")
        ? "audio/webm;codecs=opus"
        : MediaRecorder.isTypeSupported("audio/webm")
          ? "audio/webm"
          : "";

      const recorder = new MediaRecorder(mediaStream, mimeType ? { mimeType } : undefined);
      mediaRecorderRef.current = recorder;

      recorder.ondataavailable = (e) => {
        if (e.data.size > 0) chunksRef.current.push(e.data);
      };

      recorder.onstop = () => {
        const blob = new Blob(chunksRef.current, { type: recorder.mimeType || "audio/webm" });
        setAudioBlob(blob);
        // Stop all tracks to release the microphone
        mediaStream.getTracks().forEach((t) => t.stop());
        setStream(null);
      };

      recorder.start();
      setIsRecording(true);
    } catch (e) {
      const msg = e instanceof DOMException && e.name === "NotAllowedError"
        ? "Microphone permission denied"
        : e instanceof Error ? e.message : "Failed to start recording";
      setError(msg);
    }
  }, []);

  const stopRecording = useCallback(() => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== "inactive") {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
    }
  }, []);

  const clearAudio = useCallback(() => {
    setAudioBlob(null);
    setError(null);
  }, []);

  return { isRecording, audioBlob, error, stream, startRecording, stopRecording, clearAudio };
}
