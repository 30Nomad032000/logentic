import { useState, useEffect, useRef, type KeyboardEvent } from "react";
import { postText, transcribeAudio, synthesizeSpeech } from "../../api/client";
import type { SearchSource } from "../../api/types";
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
    agent?: string;
    sources?: SearchSource[];
    thinking?: string;
    translatedInput?: string;
    englishResponse?: string;
  } | null>(null);
  const [thinkingOpen, setThinkingOpen] = useState(false);
  const [translationOpen, setTranslationOpen] = useState(false);
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
        agent: data.agent,
        sources: data.sources,
        thinking: data.thinking,
        translatedInput: data.translated_input,
        englishResponse: data.english_response,
      });
      setThinkingOpen(false);
      setTranslationOpen(false);

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
        agent: data.agent,
        sources: data.sources,
        thinking: data.thinking,
        translatedInput: data.translated_input,
        englishResponse: data.english_response,
      });
      setThinkingOpen(false);
      setTranslationOpen(false);
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

  const AGENT_LABELS: Record<string, { label: string; icon: string; color: string }> = {
    info_agent: { label: "Info Agent", icon: "i", color: "rgb(52,152,219)" },
    task_agent: { label: "Task Agent", icon: "T", color: "rgb(155,89,182)" },
    chat_agent: { label: "Chat Agent", icon: "C", color: "rgb(46,204,113)" },
    smart_home_agent: { label: "Smart Home", icon: "H", color: "rgb(230,126,34)" },
    unknown: { label: "Agent", icon: "?", color: "#8a8478" },
  };

  const INTENT_LABELS: Record<string, string> = {
    information_query: "Information Query",
    task_management: "Task Management",
    general_chat: "General Chat",
    smart_home: "Smart Home",
    unknown: "Unknown",
  };

  const stageLabels: { key: PipelineStage; label: string }[] = [
    { key: "asr", label: "ASR" },
    { key: "processing", label: "Translate + LLM + Translate" },
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
              {/* Agent routing badge */}
              {response.agent && response.agent !== "unknown" && (() => {
                const agentInfo = AGENT_LABELS[response.agent] || AGENT_LABELS.unknown;
                return (
                  <div className="flex items-center gap-2 mb-2">
                    <div
                      className="flex items-center gap-1.5 px-2.5 py-1 rounded-md border font-mono text-[11px] font-semibold tracking-[0.04em]"
                      style={{ borderColor: `${agentInfo.color}44`, color: agentInfo.color, background: `${agentInfo.color}11` }}
                    >
                      <span className="w-4 h-4 rounded-full flex items-center justify-center text-[9px] font-bold" style={{ background: `${agentInfo.color}22`, color: agentInfo.color }}>
                        {agentInfo.icon}
                      </span>
                      {agentInfo.label}
                    </div>
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#8a8478" strokeWidth="2">
                      <path d="M5 12h14M12 5l7 7-7 7" />
                    </svg>
                    <span className="font-mono text-[11px] text-[#8a8478]">
                      {INTENT_LABELS[response.intent] || response.intent}
                    </span>
                  </div>
                );
              })()}
              {/* LLM Thinking panel */}
              {response.thinking && (
                <div className="mb-2">
                  <button
                    onClick={() => setThinkingOpen((v) => !v)}
                    className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-md border border-[rgba(232,164,74,0.15)] bg-[rgba(232,164,74,0.04)] text-[#e8a44a] font-mono text-[10.5px] font-semibold tracking-[0.04em] uppercase cursor-pointer transition-all duration-200 hover:border-[rgba(232,164,74,0.3)] hover:bg-[rgba(232,164,74,0.08)]"
                  >
                    <svg
                      width="10"
                      height="10"
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      strokeWidth="2.5"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      className="opacity-70"
                    >
                      <path d="M12 2a7 7 0 0 1 7 7c0 2.4-1.2 4.5-3 5.7V17a2 2 0 0 1-2 2h-4a2 2 0 0 1-2-2v-2.3C6.2 13.5 5 11.4 5 9a7 7 0 0 1 7-7z" />
                      <line x1="10" y1="22" x2="14" y2="22" />
                    </svg>
                    LLM Thinking
                    <svg
                      width="10"
                      height="10"
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      strokeWidth="2.5"
                      className={`transition-transform duration-200 ${thinkingOpen ? "rotate-180" : ""}`}
                    >
                      <polyline points="6 9 12 15 18 9" />
                    </svg>
                  </button>
                  {thinkingOpen && (
                    <div className="mt-1.5 px-3 py-2.5 rounded-md border border-[rgba(232,164,74,0.1)] bg-[rgba(232,164,74,0.03)] max-h-[200px] overflow-y-auto">
                      <pre className="text-[11px] text-[#9a9488] whitespace-pre-wrap font-mono leading-relaxed">
                        {response.thinking}
                      </pre>
                    </div>
                  )}
                </div>
              )}
              <div className="mt-1">{response.text}</div>
              {/* Translation panel (shown when input is non-English) */}
              {(response.translatedInput || response.englishResponse) && (
                <div className="mt-2">
                  <button
                    onClick={() => setTranslationOpen((v) => !v)}
                    className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-md border border-[rgba(46,204,113,0.15)] bg-[rgba(46,204,113,0.04)] text-[rgba(46,204,113,0.8)] font-mono text-[10.5px] font-semibold tracking-[0.04em] uppercase cursor-pointer transition-all duration-200 hover:border-[rgba(46,204,113,0.3)] hover:bg-[rgba(46,204,113,0.08)]"
                  >
                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="opacity-70">
                      <path d="M5 8l6 6" /><path d="M4 14l6-6 2-3" /><path d="M2 5h12" /><path d="M7 2h1" />
                      <path d="M22 22l-5-10-5 10" /><path d="M14 18h6" />
                    </svg>
                    Translation
                    <svg
                      width="10"
                      height="10"
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      strokeWidth="2.5"
                      className={`transition-transform duration-200 ${translationOpen ? "rotate-180" : ""}`}
                    >
                      <polyline points="6 9 12 15 18 9" />
                    </svg>
                  </button>
                  {translationOpen && (
                    <div className="mt-1.5 px-3 py-2.5 rounded-md border border-[rgba(46,204,113,0.1)] bg-[rgba(46,204,113,0.03)] space-y-2">
                      {response.translatedInput && (
                        <div>
                          <div className="font-mono text-[9.5px] font-semibold text-[rgba(46,204,113,0.5)] uppercase tracking-[0.08em] mb-0.5">
                            Input (translated to English)
                          </div>
                          <p className="text-[11.5px] text-[#b8b2a8] leading-relaxed">{response.translatedInput}</p>
                        </div>
                      )}
                      {response.englishResponse && (
                        <div>
                          <div className="font-mono text-[9.5px] font-semibold text-[rgba(46,204,113,0.5)] uppercase tracking-[0.08em] mb-0.5">
                            Response (English, before translation)
                          </div>
                          <p className="text-[11.5px] text-[#b8b2a8] leading-relaxed">{response.englishResponse}</p>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              )}
              {/* Web search sources */}
              {response.sources && response.sources.length > 0 && (
                <div className="mt-3 pt-3 border-t border-[rgba(255,200,120,0.06)]">
                  <div className="font-mono text-[10px] font-semibold text-[rgba(52,152,219,0.7)] uppercase tracking-[0.08em] mb-2 flex items-center gap-1.5">
                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                      <circle cx="11" cy="11" r="8" />
                      <line x1="21" y1="21" x2="16.65" y2="16.65" />
                    </svg>
                    Web Search Results ({response.sources.length})
                  </div>
                  <div className="space-y-2">
                    {response.sources.map((src, i) => (
                      <div
                        key={i}
                        className="bg-[rgba(52,152,219,0.04)] border border-[rgba(52,152,219,0.1)] rounded-md px-3 py-2.5 transition-all duration-200 hover:border-[rgba(52,152,219,0.25)] hover:bg-[rgba(52,152,219,0.07)]"
                      >
                        <a
                          href={src.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="font-mono text-[11.5px] font-semibold text-[rgba(52,152,219,0.9)] hover:text-[rgb(52,152,219)] transition-colors flex items-center gap-1.5"
                        >
                          <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" className="shrink-0 opacity-60">
                            <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6" />
                            <polyline points="15 3 21 3 21 9" />
                            <line x1="10" y1="14" x2="21" y2="3" />
                          </svg>
                          {src.title}
                        </a>
                        {src.snippet && (
                          <p className="text-[11px] text-[#8a8478] mt-1 leading-relaxed line-clamp-2">
                            {src.snippet}
                          </p>
                        )}
                        {src.url && (
                          <span className="text-[9.5px] text-[#555049] mt-0.5 block truncate">
                            {src.url}
                          </span>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}
              <div className="flex gap-4 mt-2.5 font-mono text-[11px] text-[#8a8478]">
                <span>Intent: {INTENT_LABELS[response.intent] || response.intent}</span>
                <span>Language: {response.language}</span>
                {response.agent && <span>Agent: {(AGENT_LABELS[response.agent] || AGENT_LABELS.unknown).label}</span>}
              </div>
            </>
          ) : (
            <div>
              {sending ? (
                <div className="space-y-2.5">
                  <div className="font-mono text-[10px] font-semibold text-[#e8a44a] uppercase tracking-[0.08em] flex items-center gap-2">
                    <span className="inline-block w-3 h-3 border-2 border-[#e8a44a] border-t-transparent rounded-full animate-spin" />
                    Processing...
                  </div>
                  <div className="flex items-center gap-2 px-3 py-2 bg-[rgba(52,152,219,0.04)] border border-[rgba(52,152,219,0.08)] rounded-md animate-pulse">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="rgba(52,152,219,0.6)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                      <circle cx="11" cy="11" r="8" />
                      <line x1="21" y1="21" x2="16.65" y2="16.65" />
                    </svg>
                    <span className="font-mono text-[11px] text-[rgba(52,152,219,0.6)]">
                      Searching the web for relevant information...
                    </span>
                  </div>
                </div>
              ) : (
                <div className="font-mono text-[10px] font-semibold text-[#8a8478] uppercase tracking-[0.08em] mb-1.5">
                  Response will appear here
                </div>
              )}
            </div>
          )}
        </div>

        <audio ref={audioRef} hidden />
      </div>
    </Card>
  );
}
