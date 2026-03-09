import type { Conversation } from "../../api/types";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

interface ConversationDetailProps {
  conversation: Conversation;
  onBack: () => void;
}

export function ConversationDetail({
  conversation,
  onBack,
}: ConversationDetailProps) {
  return (
    <div className="py-1 animate-[slideInRight_0.3s_ease]">
      <div className="flex items-center justify-between mb-4">
        <div className="font-display text-lg font-normal text-[#ede9e1]">
          Conversation Detail
        </div>
        <Button
          variant="outline"
          size="sm"
          className="rounded-full font-mono text-[11px] font-medium text-[#e8a44a] border-[rgba(255,200,120,0.06)] bg-transparent tracking-[0.03em] hover:border-[#e8a44a] hover:bg-[rgba(232,164,74,0.08)]"
          onClick={onBack}
        >
          &larr; Back
        </Button>
      </div>
      <div className="font-mono text-[11px] text-[#8a8478] mb-5 flex gap-4 flex-wrap">
        <span className="px-2.5 py-[3px] bg-[#211f1d] rounded-full border border-[rgba(255,200,120,0.06)]">
          ID: {conversation.id}
        </span>
        <span className="px-2.5 py-[3px] bg-[#211f1d] rounded-full border border-[rgba(255,200,120,0.06)]">
          Lang: {conversation.language}
        </span>
        <span className="px-2.5 py-[3px] bg-[#211f1d] rounded-full border border-[rgba(255,200,120,0.06)]">
          Status: {conversation.status}
        </span>
      </div>
      <div className="flex flex-col gap-2.5 mb-5">
        {conversation.messages.map((m, i) => (
          <div
            key={i}
            className={cn(
              "py-3 px-4 rounded-lg text-[13.5px] leading-[1.55] border border-transparent",
              m.role === "user"
                ? "bg-[rgba(232,164,74,0.08)] border-[rgba(232,164,74,0.08)] ml-6"
                : "bg-[#211f1d] border-[rgba(255,200,120,0.06)] mr-6"
            )}
          >
            <div className="font-mono text-[10px] font-bold text-[#8a8478] mb-1 uppercase tracking-[0.06em]">
              {m.role} &middot; {m.language}
            </div>
            {m.content}
          </div>
        ))}
      </div>
      <div className="font-mono text-[11px] text-[#8a8478] py-3 px-3.5 bg-[#211f1d] rounded-lg flex flex-wrap gap-x-5 gap-y-2.5 border border-[rgba(255,200,120,0.06)]">
        <div className="flex gap-1">
          <span className="text-[#8a8478]">ASR</span>
          <span className="text-[#a09a8e] font-semibold">{Math.round(conversation.asr_time_ms)}ms</span>
        </div>
        <div className="flex gap-1">
          <span className="text-[#8a8478]">Translation</span>
          <span className="text-[#a09a8e] font-semibold">{Math.round(conversation.translation_time_ms)}ms</span>
        </div>
        <div className="flex gap-1">
          <span className="text-[#8a8478]">LLM</span>
          <span className="text-[#a09a8e] font-semibold">{Math.round(conversation.llm_time_ms)}ms</span>
        </div>
        <div className="flex gap-1">
          <span className="text-[#8a8478]">TTS</span>
          <span className="text-[#a09a8e] font-semibold">{Math.round(conversation.tts_time_ms)}ms</span>
        </div>
        <div className="flex gap-1">
          <span className="text-[#8a8478]">Total</span>
          <span className="text-[#a09a8e] font-semibold">{Math.round(conversation.total_time_ms)}ms</span>
        </div>
      </div>
    </div>
  );
}
