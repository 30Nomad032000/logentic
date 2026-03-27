import { useState, useRef, useCallback, useEffect } from "react";

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
  const warmStreamRef = useRef<MediaStream | null>(null);

  // Pre-acquire mic on mount so it's ready instantly when recording starts
  useEffect(() => {
    navigator.mediaDevices
      .getUserMedia({ audio: true })
      .then((s) => {
        // Mute the tracks so the mic isn't "hot" until recording
        s.getAudioTracks().forEach((t) => (t.enabled = false));
        warmStreamRef.current = s;
      })
      .catch(() => {
        // Permission denied — will retry on first record click
      });

    return () => {
      warmStreamRef.current?.getTracks().forEach((t) => t.stop());
      warmStreamRef.current = null;
    };
  }, []);

  const startRecording = useCallback(async () => {
    setError(null);
    setAudioBlob(null);
    chunksRef.current = [];

    try {
      // Reuse warm stream or request a new one
      let mediaStream = warmStreamRef.current;
      if (!mediaStream || mediaStream.getAudioTracks().every((t) => t.readyState === "ended")) {
        mediaStream = await navigator.mediaDevices.getUserMedia({ audio: true });
        warmStreamRef.current = mediaStream;
      }
      // Un-mute the tracks
      mediaStream.getAudioTracks().forEach((t) => (t.enabled = true));
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
        // Mute tracks instead of stopping — keeps stream warm for next use
        mediaStream!.getAudioTracks().forEach((t) => (t.enabled = false));
        setStream(null);
      };

      // Use 250ms timeslice so data arrives in small chunks (reduces start-of-audio loss)
      recorder.start(250);
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
