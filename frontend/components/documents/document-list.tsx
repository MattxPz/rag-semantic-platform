"use client";

import { useQuery } from "@tanstack/react-query";
import { listDocuments } from "@/lib/api/documents";
import { DocumentStatusBadge } from "./document-status-badge";
import type { Document } from "@/types";

export function DocumentList() {
  const { data: documents, isLoading } = useQuery<Document[]>({
    queryKey: ["documents"],
    queryFn: listDocuments,
    refetchInterval: (query) => {
      // Keep polling every 3s only while something is still processing.
      const hasActiveProcessing = query.state.data?.some(
        (doc) => doc.status === "pending" || doc.status === "processing"
      );
      return hasActiveProcessing ? 3000 : false;
    },
  });

  if (isLoading) {
    return <p className="text-sm text-muted-foreground">Loading documents...</p>;
  }

  if (!documents || documents.length === 0) {
    return <p className="text-sm text-muted-foreground">No documents uploaded yet.</p>;
  }

  return (
    <div className="space-y-2">
      {documents.map((doc) => (
        <div key={doc.id} className="flex items-center justify-between rounded-md border p-3">
          <div>
            <p className="text-sm font-medium">{doc.filename}</p>
            <p className="text-xs text-muted-foreground">
              {doc.num_pages ? `${doc.num_pages} pages` : "Processing..."}
            </p>
          </div>
          <DocumentStatusBadge status={doc.status} />
        </div>
      ))}
    </div>
  );
}