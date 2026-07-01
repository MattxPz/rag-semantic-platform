export interface User {
  id: string;
  email: string;
}

export type DocumentStatus = "pending" | "processing" | "ready" | "error";

export interface Document {
  id: string;
  filename: string;
  status: DocumentStatus;
  num_pages: number | null;
  page_width: number | null;
  page_height: number | null;
  uploaded_at: string;
}

export interface SourceChunk {
  chunk_id: string;
  page_number: number;
  content_preview: string;
  bbox: number[][] | null;
}

export type ChatStreamEvent =
  | { type: "sources"; sources: SourceChunk[] }
  | { type: "token"; content: string }
  | { type: "done" }
  | { type: "error"; content: string };
