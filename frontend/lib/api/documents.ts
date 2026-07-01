import { apiClient, ApiError } from "@/lib/api-client";
import { useAuthStore } from "@/stores/auth-store";
import type { Document } from "@/types";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export async function listDocuments(): Promise<Document[]> {
  return apiClient.get<Document[]>("/documents/");
}

export async function getDocument(id: string): Promise<Document> {
  return apiClient.get<Document>(`/documents/${id}`);
}

export async function uploadDocument(file: File): Promise<Document> {
  const formData = new FormData();
  formData.append("file", file);
  return apiClient.postFile<Document>("/documents/", formData);
}

/**
 * Fetches the raw PDF bytes (this endpoint requires auth, so we can't pass
 * its URL directly to react-pdf) and returns a local blob URL the viewer
 * can load without needing to handle auth headers itself.
 * Remember to URL.revokeObjectURL() the result when the viewer unmounts.
 */
export async function fetchDocumentBlobUrl(id: string): Promise<string> {
  const token = useAuthStore.getState().token;
  const response = await fetch(`${API_URL}/documents/${id}/file`, {
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  });
  if (!response.ok) {
    throw new ApiError("Failed to load the PDF file.", response.status);
  }
  const blob = await response.blob();
  return URL.createObjectURL(blob);
}
