import type { Conversation } from "../../api/types";
import styles from "./ConversationList.module.css";

interface ConversationItemProps {
  conversation: Conversation;
  onClick: () => void;
}

export function ConversationItem({ conversation, onClick }: ConversationItemProps) {
  const userMsg = conversation.messages.find((m) => m.role === "user");
  const preview = userMsg ? userMsg.content : "(no input)";
  const time = new Date(conversation.started_at).toLocaleString();

  return (
    <div className={styles.item} onClick={onClick}>
      <div className={styles.header}>
        <span className={styles.lang}>{conversation.language}</span>
        <span className={styles.time}>{time}</span>
      </div>
      <div className={styles.preview}>{preview}</div>
      <div className={styles.metrics}>
        <span>Total: {Math.round(conversation.total_time_ms)}ms</span>
        {conversation.intent && <span>Intent: {conversation.intent}</span>}
        <span>{conversation.messages.length} messages</span>
      </div>
    </div>
  );
}
