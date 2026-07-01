"use client";

import { useState } from "react";
import { useParams } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { getDocument } from "@/lib/api/documents";
import { PdfViewer } from "@/components/documents/pdf-viewer";
import { ChatPanel } from "@/components/chat/chat-panel";
import type { Document, SourceChunk } from "@/types";

export default function DocumentDetailPage() {
  const params = useParams<{ id: string }>();
  const documentId = params.id;

  const [highlightedSources, setHighlightedSources] = useState<SourceChunk[]>([]);

  const { data: doc, isLoading } = useQuery<Document>({
    queryKey: ["document", documentId],
    queryFn: () => getDocument(documentId),
  });

  if (isLoading || !doc) {
    return <p className="p-8 text-sm text-muted-foreground">Loading document…</p>;
  }

  if (doc.status !== "ready") {
    return (
      <div className="p-8">
        <p className="text-sm text-muted-foreground">
          This document is not ready yet (status: {doc.status}). Go back to the{" "}
          <Link href="/dashboard" className="underline underline-offset-4">
            dashboard
          </Link>{" "}
          and wait for processing to finish.
        </p>
      </div>
    );
  }

  return (
    <div className="flex h-screen flex-col">
      <header className="flex items-center gap-3 border-b px-4 py-3">
        <Link href="/dashboard" className="text-sm text-muted-foreground hover:underline">
          ← Dashboard
        </Link>
        <h1 className="truncate text-sm font-medium">{doc.filename}</h1>
      </header>
      <div className="flex flex-1 overflow-hidden">
        <div className="w-1/2 overflow-y-auto bg-muted/30 p-4">
          <PdfViewer
            documentId={documentId}
            pageWidth={doc.page_width}
            highlightedSources={highlightedSources}
          />
        </div>
        <div className="w-1/2 border-l">
          <ChatPanel documentId={documentId} onSourcesSelected={setHighlightedSources} />
        </div>
      </div>
    </div>
  );
}
