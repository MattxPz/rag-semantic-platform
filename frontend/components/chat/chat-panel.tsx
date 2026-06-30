"use client";

import { useRef, useState } from "react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { streamChat } from "@/lib/api/chat";
import { ApiError } from "@/lib/api-client";
import type { SourceChunk } from "@/types";

interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  sources?: SourceChunk[];
}

interface ChatPanelProps {
  documentId: string;
  onSourcesSelected: (sources: SourceChunk[]) => void;
}

export function ChatPanel({ documentId, onSourcesSelected }: ChatPanelProps) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [isStreaming, setIsStreaming] = useState(false);
  const conversationIdRef = useRef<string | null>(null);

  const handleSend = async () => {
    const question = input.trim();
    if (!question || isStreaming) return;

    setInput("");
    const assistantId = crypto.randomUUID();
    setMessages((prev) => [
      ...prev,
      { id: crypto.randomUUID(), role: "user", content: question },
      { id: assistantId, role: "assistant", content: "" },
    ]);
    setIsStreaming(true);

    try {
      const conversationId = await streamChat({
        question,
        documentIds: [documentId],
        conversationId: conversationIdRef.current,
        onEvent: (event) => {
          if (event.type === "sources") {
            setMessages((prev) =>
              prev.map((m) => (m.id === assistantId ? { ...m, sources: event.sources } : m))
            );
            onSourcesSelected([...event.sources]);
          } else if (event.type === "token") {
            setMessages((prev) =>
              prev.map((m) =>
                m.id === assistantId ? { ...m, content: m.content + event.content } : m
              )
            );
          } else if (event.type === "error") {
            toast.error(event.content);
          }
        },
      });

      if (conversationId) {
        conversationIdRef.current = conversationId;
      }
    } catch (error) {
      toast.error(error instanceof ApiError ? error.message : "Chat request failed.");
    } finally {
      setIsStreaming(false);
    }
  };

  return (
    <div className="flex h-full flex-col">
      <div className="flex-1 space-y-4 overflow-y-auto p-4">
        {messages.length === 0 && (
          <p className="text-sm text-muted-foreground">
            Ask a question about this document to get started.
          </p>
        )}
        {messages.map((message) => (
          <div key={message.id} className={message.role === "user" ? "text-right" : "text-left"}>
            <div
              className={`inline-block max-w-[85%] whitespace-pre-wrap rounded-lg px-3 py-2 text-sm ${
                message.role === "user" ? "bg-primary text-primary-foreground" : "bg-muted"
              }`}
            >
              {message.content || (isStreaming && message.role === "assistant" ? "…" : "")}
            </div>
            {message.sources && message.sources.length > 0 && (
              <div className="mt-1 flex flex-wrap gap-1">
                {message.sources.map((source) => (
                  <button
                    key={source.chunk_id}
                    onClick={() => onSourcesSelected([...message.sources!])}
                    className="rounded-full border px-2 py-0.5 text-xs text-muted-foreground hover:bg-muted"
                  >
                    Page {source.page_number}
                  </button>
                ))}
              </div>
            )}
          </div>
        ))}
      </div>
      <div className="flex gap-2 border-t p-4">
        <Input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault();
              handleSend();
            }
          }}
          placeholder="Ask a question about this document..."
          disabled={isStreaming}
        />
        <Button onClick={handleSend} disabled={isStreaming || !input.trim()}>
          {isStreaming ? "Thinking..." : "Send"}
        </Button>
      </div>
    </div>
  );
}