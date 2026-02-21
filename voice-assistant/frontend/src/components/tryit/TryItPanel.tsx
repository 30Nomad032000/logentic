import { useState, type KeyboardEvent } from "react";
import { postText } from "../../api/client";
import { useRefresh } from "../../DashboardDataLoader";
import { Card } from "../common/Card";
import styles from "./TryItPanel.module.css";

const LANGUAGES = [
  { code: "en", name: "English" },
  { code: "ml", name: "Malayalam" },
  { code: "hi", name: "Hindi" },
  { code: "ta", name: "Tamil" },
  { code: "te", name: "Telugu" },
  { code: "bn", name: "Bengali" },
];

export function TryItPanel() {
  const refresh = useRefresh();
  const [text, setText] = useState("");
  const [language, setLanguage] = useState("en");
  const [sending, setSending] = useState(false);
  const [response, setResponse] = useState<{
    text: string;
    intent: string;
    language: string;
  } | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function handleSend() {
    if (!text.trim() || sending) return;

    setSending(true);
    setError(null);
    setResponse(null);

    try {
      const data = await postText(text.trim(), language);
      setResponse({
        text: data.response || "No response",
        intent: data.intent || "-",
        language: data.language,
      });
      setTimeout(refresh, 500);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Request failed");
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

  return (
    <Card title="Try It">
      <div className={styles.panel}>
        <textarea
          className={styles.textarea}
          placeholder="Type a message to test the assistant..."
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={handleKeyDown}
        />
        <div className={styles.controls}>
          <select
            className={styles.select}
            value={language}
            onChange={(e) => setLanguage(e.target.value)}
          >
            {LANGUAGES.map((l) => (
              <option key={l.code} value={l.code}>
                {l.name}
              </option>
            ))}
          </select>
          <button
            className={styles.btn}
            disabled={sending || !text.trim()}
            onClick={handleSend}
          >
            {sending ? "Processing..." : "Send"}
          </button>
        </div>
        <div className={styles.responseBox}>
          {error ? (
            <div className={`${styles.responseLabel} ${styles.errorText}`}>
              Error: {error}
            </div>
          ) : response ? (
            <>
              <div className={styles.responseLabel}>Assistant Response</div>
              <div style={{ marginTop: 4 }}>{response.text}</div>
              <div className={styles.responseTiming}>
                <span>Intent: {response.intent}</span>
                <span>Language: {response.language}</span>
              </div>
            </>
          ) : (
            <div className={styles.responseLabel}>
              {sending ? "Processing..." : "Response will appear here"}
            </div>
          )}
        </div>
      </div>
    </Card>
  );
}
