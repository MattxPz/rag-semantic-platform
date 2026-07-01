import { useAuthStore } from "@/stores/auth-store";
import { ApiError } from "@/lib/api-client";
import type { ChatStreamEvent } from "@/types";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface StreamChatParams {
  question: string;
  documentIds: string[];
  conversationId?: string | null;
  onEvent: (event: ChatStreamEvent) => void;
}

/**
 * Sends a question to the backend and consumes the Server-Sent Events
 * response manually via fetch + a stream reader. The native EventSource API
 * can't be used here because it doesn't support custom headers (we need to
 * send the Authorization bearer token).
 * Returns the conversation_id assigned/reused by the backend.
 */
export async function streamChat({
  question,
  documentIds,
  conversationId,
  onEvent,
}: StreamChatParams): Promise<string | null> {
  const token = useAuthStore.getState().token;

  const response = await fetch(`${API_URL}/chat/`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    body: JSON.stringify({
      question,
      document_ids: documentIds,
      conversation_id: conversationId ?? null,
    }),
  });

  if (!response.ok || !response.body) {
    let detail = "Chat request failed.";
    try {
      const data = await response.json();
      detail = data.detail ?? detail;
    } catch {
      /* response had no JSON body */
    }
    throw new ApiError(detail, response.status);
  }

  const conversationIdFromHeader = response.headers.get("X-Conversation-Id");

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { value, done } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });

    // SSE events are separated by a blank line.
    const events = buffer.split("\n\n");
    buffer = events.pop() ?? ""; // keep a possibly-incomplete trailing event

    for (const rawEvent of events) {
      const line = rawEvent.trim();
      if (!line.startsWith("data:")) continue;

      try {
        const event = JSON.parse(line.slice(5).trim()) as ChatStreamEvent;
        onEvent(event);
      } catch {
        // Skip malformed event chunks
      }
    }
  }

  return conversationIdFromHeader;
}
