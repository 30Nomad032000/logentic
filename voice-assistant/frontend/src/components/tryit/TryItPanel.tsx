import { useState, useEffect, useRef, type KeyboardEvent } from "react";
import { postText, transcribeAudio, synthesizeSpeech } from "../../api/client";
import { useRefresh } from "../../DashboardDataLoader";
import { useAudioRecorder } from "../../hooks/useAudioRecorder";
import { Card } from "@/components/common/Card";
import { Textarea } from "@/components/ui/textarea";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectTrigger,
  SelectContent,
  SelectItem,
  SelectValue,
} from "@/components/ui/select";
import { VoiceVisualizer } from "./VoiceVisualizer";
import { cn } from "@/lib/utils";

const LANGUAGES = [
  { code: "en", name: "English" },
  { code: "ml", name: "Malayalam" },
  { code: "hi", name: "Hindi" },
  { code: "ta", name: "Tamil" },
  { code: "te", name: "Telugu" },
  { code: "bn", name: "Bengali" },
];

type PipelineStage = "idle" | "recording" | "asr" | "processing" | "tts" | "done";

interface StageTime {
  asr_ms?: number;
  processing_ms?: number;
  tts_ms?: number;
  total_ms?: number;
}

export function TryItPanel() {
  const refresh = useRefresh();
  const [text, setText] = useState("");
  const [language, setLanguage] = useState("ml");
  const [sending, setSending] = useState(false);
  const [response, setResponse] = useState<{
    text: string;
    intent: string;
    language: string;
  } | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [stage, setStage] = useState<PipelineStage>("idle");
  const [stageTimes, setStageTimes] = useState<StageTime>({});
  const [lastAudioUrl, setLastAudioUrl] = useState<string | null>(null);

  const audioRef = useRef<HTMLAudioElement | null>(null);
  const recorder = useAudioRecorder();

  // When recording stops and we have a blob, run the voice pipeline
  useEffect(() => {
    if (recorder.audioBlob && !sending) {
      runVoicePipeline(recorder.audioBlob);
      recorder.clearAudio();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [recorder.audioBlob]);

  async function runVoicePipeline(blob: Blob) {
    setSending(true);
    setError(null);
    setResponse(null);
    setStageTimes({});
    setLastAudioUrl(null);

    const totalStart = performance.now();

    try {
      // Stage 1: ASR
      setStage("asr");
      const asrStart = performance.now();
      const transcription = await transcribeAudio(blob, language);
      const asrMs = performance.now() - asrStart;

      setText(transcription.text);
      if (transcription.language && transcription.language !== language) {
        setLanguage(transcription.language);
      }

      setStageTimes((prev) => ({ ...prev, asr_ms: Math.round(asrMs) }));

      // Stage 2: Text pipeline (Translation + LLM + Translation)
      setStage("processing");
      const procStart = performance.now();
      const data = await postText(
        transcription.text,
        transcription.language || language
      );
      const procMs = performance.now() - procStart;
      setStageTimes((prev) => ({ ...prev, processing_ms: Math.round(procMs) }));

      const responseText = data.response || "No response";
      const responseLang = data.language || language;

      setResponse({
        text: responseText,
        intent: data.intent || "-",
        language: responseLang,
      });

      // Stage 3: TTS
      setStage("tts");
      try {
        const ttsStart = performance.now();
        const audioBlob = await synthesizeSpeech(responseText, responseLang);
        const ttsMs = performance.now() - ttsStart;
        setStageTimes((prev) => ({ ...prev, tts_ms: Math.round(ttsMs) }));

        const url = URL.createObjectURL(audioBlob);
        setLastAudioUrl(url);

        // Auto-play the response
        if (audioRef.current) {
          audioRef.current.src = url;
          audioRef.current.play().catch(() => {});
        }
      } catch {
        // TTS failure is non-critical, response text still shown
      }

      const totalMs = performance.now() - totalStart;
      setStageTimes((prev) => ({ ...prev, total_ms: Math.round(totalMs) }));
      setStage("done");
      setTimeout(refresh, 500);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Voice pipeline failed");
      setStage("idle");
    } finally {
      setSending(false);
    }
  }

  async function handleSend() {
    if (!text.trim() || sending) return;

    setSending(true);
    setError(null);
    setResponse(null);
    setStageTimes({});
    setLastAudioUrl(null);
    setStage("processing");

    const totalStart = performance.now();

    try {
      const data = await postText(text.trim(), language);
      const procMs = performance.now() - totalStart;

      setResponse({
        text: data.response || "No response",
        intent: data.intent || "-",
        language: data.language,
      });
      setStageTimes({ processing_ms: Math.round(procMs), total_ms: Math.round(procMs) });
      setStage("done");
      setTimeout(refresh, 500);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Request failed");
      setStage("idle");
    } finally {
      setSending(false);
    }
  }

  function handleKeyDown(e: KeyboardEvent) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  }

  function handleMicClick() {
    if (recorder.isRecording) {
      recorder.stopRecording();
    } else {
      setStage("recording");
      recorder.startRecording();
    }
  }

  function handlePlayback() {
    if (lastAudioUrl && audioRef.current) {
      audioRef.current.src = lastAudioUrl;
      audioRef.current.play().catch(() => {});
    }
  }

  const stageLabels: { key: PipelineStage; label: string }[] = [
    { key: "asr", label: "ASR" },
    { key: "processing", label: "LLM Pipeline" },
    { key: "tts", label: "TTS" },
  ];

  const activeStageIndex = stageLabels.findIndex((s) => s.key === stage);

  return (
    <Card title="Try It">
      <div className="flex flex-col gap-3.5">
        <Textarea
          className="bg-[#211f1d] border-[rgba(255,200,120,0.06)] rounded-lg px-4 py-3.5 text-[#ede9e1] font-sans text-sm resize-y min-h-[88px] leading-relaxed transition-[border-color,box-shadow] duration-200 placeholder:text-[#8a8478] focus:border-[rgba(232,164,74,0.3)] focus:shadow-[0_0_0_3px_rgba(232,164,74,0.08),0_0_16px_rgba(232,164,74,0.06)] focus-visible:ring-0 focus-visible:ring-offset-0 disabled:opacity-60 disabled:cursor-not-allowed"
          placeholder="Type a message or click the mic to speak..."
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={recorder.isRecording || sending}
        />
        <div className="flex gap-2.5 items-center">
          <Select value={language} onValueChange={setLanguage}>
            <SelectTrigger className="w-auto bg-[#211f1d] border-[rgba(255,200,120,0.06)] rounded-md px-3.5 py-2 text-[#ede9e1] font-mono text-xs cursor-pointer transition-[border-color] duration-200 focus:border-[rgba(232,164,74,0.3)] focus:ring-0 focus:ring-offset-0">
              <SelectValue />
            </SelectTrigger>
            <SelectContent className="bg-[#211f1d] border-[rgba(255,200,120,0.06)] text-[#ede9e1]">
              {LANGUAGES.map((l) => (
                <SelectItem
                  key={l.code}
                  value={l.code}
                  className="font-mono text-xs text-[#ede9e1] focus:bg-[rgba(232,164,74,0.15)] focus:text-[#e8a44a]"
                >
                  {l.name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>

          <button
            className={cn(
              "flex items-center justify-center w-[38px] h-[38px] rounded-full border border-[rgba(255,200,120,0.06)] bg-[#211f1d] text-[#8a8478] cursor-pointer transition-all duration-200 shrink-0",
              "hover:enabled:border-[rgba(232,164,74,0.3)] hover:enabled:text-[#e8a44a]",
              "disabled:opacity-30 disabled:cursor-not-allowed",
              recorder.isRecording && "border-[#d4564e] text-[#d4564e] bg-[rgba(212,86,78,0.1)] animate-[micPulse_1.5s_ease-in-out_infinite]"
            )}
            onClick={handleMicClick}
            disabled={sending && !recorder.isRecording}
            title={recorder.isRecording ? "Stop recording" : "Start recording"}
          >
            {recorder.isRecording ? (
              <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor">
                <rect x="6" y="6" width="12" height="12" rx="2" />
              </svg>
            ) : (
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z" />
                <path d="M19 10v2a7 7 0 0 1-14 0v-2" />
                <line x1="12" y1="19" x2="12" y2="23" />
                <line x1="8" y1="23" x2="16" y2="23" />
              </svg>
            )}
          </button>

          <Button
            className="bg-gradient-to-br from-[#e8a44a] to-[rgba(232,164,74,0.7)] text-[#111] border-none px-6 py-2 rounded-md font-mono text-xs font-semibold tracking-[0.04em] uppercase cursor-pointer transition-[transform,box-shadow,opacity] duration-150 hover:enabled:-translate-y-px hover:enabled:shadow-[0_4px_16px_rgba(232,164,74,0.3)] active:enabled:translate-y-0 disabled:opacity-30 disabled:cursor-not-allowed"
            disabled={sending || !text.trim()}
            onClick={handleSend}
          >
            {sending ? "Processing..." : "Send"}
          </Button>
        </div>

        {/* Live voice visualizer during recording */}
        {(recorder.isRecording || stage === "recording") && (
          <div className="relative">
            <VoiceVisualizer stream={recorder.stream} isRecording={recorder.isRecording} />
            <div className="flex items-center justify-between mt-2">
              <div className="flex items-center gap-2 font-mono text-xs text-[#d4564e] font-semibold tracking-[0.04em]">
                <span className="w-2 h-2 rounded-full bg-[#d4564e] animate-[dotPulse_1s_ease-in-out_infinite]" />
                Listening...
              </div>
              <div className="font-mono text-[10px] text-[#8a8478] tracking-[0.04em]">
                Tap mic to stop
              </div>
            </div>
          </div>
        )}

        {/* Pipeline stage indicators */}
        {stage !== "idle" && !recorder.isRecording && stage !== "recording" && (
          <div className="py-2">
            <div className="flex gap-1.5 flex-wrap">
                {stageLabels.map((s, i) => {
                  const timeKey = s.key === "asr" ? "asr_ms" : s.key === "processing" ? "processing_ms" : "tts_ms";
                  const time = stageTimes[timeKey];
                  const isActive = s.key === stage;
                  const isDone = i < activeStageIndex || stage === "done";

                  return (
                    <div
                      key={s.key}
                      className={cn(
                        "flex items-center gap-1 px-2.5 py-1 rounded-md border border-[rgba(255,200,120,0.06)] bg-[#211f1d] font-mono text-[11px] text-[#8a8478] transition-all duration-200",
                        isActive && "border-[rgba(232,164,74,0.3)] text-[#e8a44a] animate-[stagePulse_1.5s_ease-in-out_infinite]",
                        isDone && "border-[rgba(46,204,113,0.3)] text-[rgb(46,204,113)]"
                      )}
                    >
                      <span className="font-semibold tracking-[0.04em] uppercase">{s.label}</span>
                      {time != null && (
                        <span className="font-normal opacity-80">{time}ms</span>
                      )}
                    </div>
                  );
                })}
                {stageTimes.total_ms != null && (
                  <div className="flex items-center gap-1 px-2.5 py-1 rounded-md border border-[rgba(46,204,113,0.3)] bg-[#211f1d] font-mono text-[11px] text-[rgb(46,204,113)] transition-all duration-200">
                    <span className="font-semibold tracking-[0.04em] uppercase">Total</span>
                    <span className="font-normal opacity-80">{stageTimes.total_ms}ms</span>
                  </div>
                )}
            </div>
          </div>
        )}

        {recorder.error && (
          <div className="font-mono text-[10px] font-semibold text-[#d4564e] uppercase tracking-[0.08em] mb-1.5">
            {recorder.error}
          </div>
        )}

        <div className="bg-[#211f1d] border border-[rgba(255,200,120,0.06)] rounded-lg px-[18px] py-4 min-h-[64px] text-sm leading-relaxed transition-[border-color] duration-200">
          {error ? (
            <div className="font-mono text-[10px] font-semibold text-[#d4564e] uppercase tracking-[0.08em] mb-1.5">
              Error: {error}
            </div>
          ) : response ? (
            <>
              <div className="flex items-center justify-between">
                <div className="font-mono text-[10px] font-semibold text-[#9a9488] uppercase tracking-[0.08em] mb-1.5">
                  Assistant Response
                </div>
                {lastAudioUrl && (
                  <button
                    className="flex items-center justify-center w-7 h-7 rounded-md border border-[rgba(255,200,120,0.06)] bg-[#211f1d] text-[#e8a44a] cursor-pointer transition-all duration-150 shrink-0 hover:border-[rgba(232,164,74,0.3)] hover:bg-[rgba(232,164,74,0.1)]"
                    onClick={handlePlayback}
                    title="Play response audio"
                  >
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                      <polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5" />
                      <path d="M19.07 4.93a10 10 0 0 1 0 14.14" />
                      <path d="M15.54 8.46a5 5 0 0 1 0 7.07" />
                    </svg>
                  </button>
                )}
              </div>
              <div className="mt-1">{response.text}</div>
              <div className="flex gap-4 mt-2.5 font-mono text-[11px] text-[#8a8478]">
                <span>Intent: {response.intent}</span>
                <span>Language: {response.language}</span>
              </div>
            </>
          ) : (
            <div className="font-mono text-[10px] font-semibold text-[#8a8478] uppercase tracking-[0.08em] mb-1.5">
              {sending ? "Processing..." : "Response will appear here"}
            </div>
          )}
        </div>

        <audio ref={audioRef} hidden />
      </div>
    </Card>
  );
}
