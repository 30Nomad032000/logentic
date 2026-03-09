import { useDashboard } from "../../context/DashboardContext";
import { Card } from "@/components/common/Card";
import { LatencyBar } from "./LatencyBar";

export function LatencyBreakdown() {
  const { stats } = useDashboard();
  const lat = stats?.avg_latency;

  const asr = lat?.asr_ms ?? 0;
  const translation = lat?.translation_ms ?? 0;
  const llm = lat?.llm_ms ?? 0;
  const tts = lat?.tts_ms ?? 0;
  const maxMs = Math.max(asr, translation, llm, tts, 100);

  return (
    <Card title="Average Latency Breakdown">
      <LatencyBar label="ASR" ms={asr} maxMs={maxMs} variant="asr" />
      <LatencyBar
        label="Translation"
        ms={translation}
        maxMs={maxMs}
        variant="translation"
      />
      <LatencyBar label="LLM" ms={llm} maxMs={maxMs} variant="llm" />
      <LatencyBar label="TTS" ms={tts} maxMs={maxMs} variant="tts" />
    </Card>
  );
}
