import type { Conversation } from "../../api/types";

interface ConversationItemProps {
  conversation: Conversation;
  onClick: () => void;
}

export function ConversationItem({ conversation, onClick }: ConversationItemProps) {
  const userMsg = conversation.messages.find((m) => m.role === "user");
  const preview = userMsg ? userMsg.content : "(no input)";
  const time = new Date(conversation.started_at).toLocaleString();

  return (
    <div
      className="py-3.5 px-4 border-b border-[rgba(255,200,120,0.06)] cursor-pointer transition-[background,padding-left] duration-200 rounded-sm mb-0.5 hover:bg-[#211f1d] hover:pl-5 last:border-b-0"
      onClick={onClick}
    >
      <div className="flex justify-between items-center mb-2">
        <span className="font-mono text-[10px] font-bold px-2.5 py-[3px] rounded-full bg-[rgba(232,164,74,0.15)] text-[#e8a44a] tracking-[0.06em] uppercase">
          {conversation.language}
        </span>
        <span className="font-mono text-[11px] text-[#8a8478]">{time}</span>
      </div>
      <div className="text-[13.5px] text-[#a09a8e] whitespace-nowrap overflow-hidden text-ellipsis leading-[1.4]">
        {preview}
      </div>
      <div className="flex gap-4 mt-1.5 font-mono text-[10.5px] text-[#8a8478] tracking-[0.02em]">
        <span>Total: {Math.round(conversation.total_time_ms)}ms</span>
        {conversation.intent && <span>Intent: {conversation.intent}</span>}
        <span>{conversation.messages.length} messages</span>
      </div>
    </div>
  );
}
