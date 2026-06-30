import { apiClient } from "@/lib/api-client";
import type { Document } from "@/types";

export async function listDocuments(): Promise<Document[]> {
  return apiClient.get<Document[]>("/documents/");
}

export async function uploadDocument(file: File): Promise<Document> {
  const formData = new FormData();
  formData.append("file", file);
  return apiClient.postFile<Document>("/documents/", formData);
}