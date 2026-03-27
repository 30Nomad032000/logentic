import type {
  HealthResponse,
  DashboardStats,
  ConversationsResponse,
  Conversation,
  TextResponse,
  TranscriptionResponse,
  TasksResponse,
} from "./types";

async function fetchJSON<T>(url: string): Promise<T> {
  const res = await fetch(url);
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

export function getHealth(): Promise<HealthResponse> {
  return fetchJSON("/health");
}

export function getStats(): Promise<DashboardStats> {
  return fetchJSON("/api/dashboard/stats");
}

export function getConversations(
  limit = 30,
  offset = 0
): Promise<ConversationsResponse> {
  return fetchJSON(`/api/dashboard/conversations?limit=${limit}&offset=${offset}`);
}

export function getConversation(id: string): Promise<Conversation> {
  return fetchJSON(`/api/dashboard/conversations/${id}`);
}

export async function postText(
  text: string,
  language: string
): Promise<TextResponse> {
  const formData = new FormData();
  formData.append("text", text);
  formData.append("language", language);

  const res = await fetch("/api/text", { method: "POST", body: formData });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

export async function transcribeAudio(
  blob: Blob,
  language?: string
): Promise<TranscriptionResponse> {
  // Use correct extension matching the blob's actual format
  const ext = blob.type.includes("webm") ? ".webm"
    : blob.type.includes("ogg") ? ".ogg"
    : blob.type.includes("mp4") ? ".m4a"
    : ".wav";
  const formData = new FormData();
  formData.append("audio", blob, `recording${ext}`);
  if (language) formData.append("language", language);

  const res = await fetch("/api/transcribe", { method: "POST", body: formData });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

export function getTasks(): Promise<TasksResponse> {
  return fetchJSON("/api/tasks");
}

export async function updateTaskStatus(
  taskId: string,
  status: "pending" | "done"
): Promise<void> {
  const formData = new FormData();
  formData.append("status", status);
  const res = await fetch(`/api/tasks/${taskId}`, {
    method: "PATCH",
    body: formData,
  });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
}

export async function deleteTask(taskId: string): Promise<void> {
  const res = await fetch(`/api/tasks/${taskId}`, { method: "DELETE" });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
}

export async function synthesizeSpeech(
  text: string,
  language: string
): Promise<Blob> {
  const formData = new FormData();
  formData.append("text", text);
  formData.append("language", language);

  const res = await fetch("/api/tts", { method: "POST", body: formData });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.blob();
}
