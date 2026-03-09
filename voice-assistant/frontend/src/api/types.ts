export interface HealthResponse {
  status: string;
  version: string;
  components: Record<string, string> | null;
}

export interface LatencyStats {
  asr_ms: number;
  translation_ms: number;
  llm_ms: number;
  tts_ms: number;
  total_ms: number;
  conversation_count: number;
}

export interface LanguageStat {
  language: string;
  count: number;
}

export interface IntentStat {
  intent: string;
  count: number;
}

export interface DashboardStats {
  total_conversations: number;
  avg_latency: LatencyStats | null;
  languages: LanguageStat[];
  intents: IntentStat[];
}

export interface Message {
  role: "user" | "assistant";
  content: string;
  language: string;
  timestamp: string;
}

export interface Conversation {
  id: string;
  session_id: string;
  language: string;
  started_at: string;
  ended_at: string | null;
  status: string;
  intent: string;
  asr_time_ms: number;
  translation_time_ms: number;
  llm_time_ms: number;
  tts_time_ms: number;
  total_time_ms: number;
  messages: Message[];
}

export interface ConversationsResponse {
  conversations: Conversation[];
  total: number;
}

export interface TextResponse {
  input: string;
  intent: string;
  response: string;
  language: string;
}

export interface TranscriptionResponse {
  text: string;
  language: string;
  language_name: string;
  confidence: number | null;
}

export interface ProcessAudioResponse {
  transcription: string;
  intent: string;
  response_text: string;
  language: string;
}
