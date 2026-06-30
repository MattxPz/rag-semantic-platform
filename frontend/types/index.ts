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
  uploaded_at: string;
}