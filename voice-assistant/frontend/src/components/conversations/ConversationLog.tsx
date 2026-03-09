import { useState, useCallback } from "react";
import { getConversation } from "../../api/client";
import { useDashboard } from "../../context/DashboardContext";
import type { Conversation } from "../../api/types";
import { Card } from "@/components/common/Card";
import { ConversationList } from "./ConversationList";
import { ConversationDetail } from "./ConversationDetail";

export function ConversationLog() {
  const { conversations } = useDashboard();
  const [selected, setSelected] = useState<Conversation | null>(null);

  const handleSelect = useCallback(async (conv: Conversation) => {
    try {
      const detail = await getConversation(conv.id);
      setSelected(detail);
    } catch {
      setSelected(conv);
    }
  }, []);

  const handleBack = useCallback(() => {
    setSelected(null);
  }, []);

  return (
    <Card title="Recent Conversations">
      {selected ? (
        <ConversationDetail conversation={selected} onBack={handleBack} />
      ) : (
        <ConversationList
          conversations={conversations}
          onSelect={handleSelect}
        />
      )}
    </Card>
  );
}
