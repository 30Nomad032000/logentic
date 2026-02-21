import type { Conversation } from "../../api/types";
import styles from "./ConversationDetail.module.css";

interface ConversationDetailProps {
  conversation: Conversation;
  onBack: () => void;
}

export function ConversationDetail({
  conversation,
  onBack,
}: ConversationDetailProps) {
  return (
    <>
      <div className={styles.detail}>
        <div className={styles.detailTitle}>Conversation Detail</div>
        <div className={styles.meta}>
          ID: {conversation.id} | Language: {conversation.language} | Status:{" "}
          {conversation.status}
        </div>
        {conversation.messages.map((m, i) => (
          <div
            key={i}
            className={`${styles.message} ${
              m.role === "user" ? styles.userMessage : styles.assistantMessage
            }`}
          >
            <div className={styles.messageRole}>
              {m.role.toUpperCase()} ({m.language})
            </div>
            {m.content}
          </div>
        ))}
        <div className={styles.timing}>
          ASR: {Math.round(conversation.asr_time_ms)}ms | Translation:{" "}
          {Math.round(conversation.translation_time_ms)}ms | LLM:{" "}
          {Math.round(conversation.llm_time_ms)}ms | TTS:{" "}
          {Math.round(conversation.tts_time_ms)}ms | Total:{" "}
          {Math.round(conversation.total_time_ms)}ms
        </div>
      </div>
      <div className={styles.backWrap}>
        <button className={styles.backBtn} onClick={onBack}>
          Back to list
        </button>
      </div>
    </>
  );
}
