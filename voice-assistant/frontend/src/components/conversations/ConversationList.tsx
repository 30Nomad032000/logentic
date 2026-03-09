import type { Conversation } from "../../api/types";
import { EmptyState } from "@/components/common/EmptyState";
import { ConversationItem } from "./ConversationItem";

interface ConversationListProps {
  conversations: Conversation[];
  onSelect: (conv: Conversation) => void;
}

export function ConversationList({
  conversations,
  onSelect,
}: ConversationListProps) {
  if (conversations.length === 0) {
    return (
      <EmptyState message='No conversations yet. Use the "Try It" panel to get started.' />
    );
  }

  return (
    <div className="max-h-[440px] overflow-y-auto">
      {conversations.map((conv) => (
        <ConversationItem
          key={conv.id}
          conversation={conv}
          onClick={() => onSelect(conv)}
        />
      ))}
    </div>
  );
}
