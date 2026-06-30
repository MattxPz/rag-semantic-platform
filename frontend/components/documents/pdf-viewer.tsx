"use client";

import { useEffect, useState } from "react";
import { Document as PdfDocument, Page, pdfjs } from "react-pdf";
import { toast } from "sonner";
import { fetchDocumentBlobUrl } from "@/lib/api/documents";
import type { SourceChunk } from "@/types";

// Elimina el "new URL(...)" y reemplázalo por esto:
pdfjs.GlobalWorkerOptions.workerSrc = `//unpkg.com/pdfjs-dist@${pdfjs.version}/build/pdf.worker.min.mjs`;

const PAGE_WIDTH = 700;

interface PdfViewerProps {
  documentId: string;
  pageWidth: number | null; // original page width in PDF points
  highlightedSources: SourceChunk[];
}

export function PdfViewer({ documentId, pageWidth, highlightedSources }: PdfViewerProps) {
  const [blobUrl, setBlobUrl] = useState<string | null>(null);
  const [numPages, setNumPages] = useState(0);

  useEffect(() => {
    let objectUrl: string | null = null;

    fetchDocumentBlobUrl(documentId).then((url) => {
      objectUrl = url;
      setBlobUrl(url);
    });

    return () => {
      if (objectUrl) URL.revokeObjectURL(objectUrl);
    };
  }, [documentId]);

  useEffect(() => {
    if (highlightedSources.length === 0) return;
    const firstPage = highlightedSources[0].page_number;
    document
      .getElementById(`pdf-page-${firstPage}`)
      ?.scrollIntoView({ behavior: "smooth", block: "start" });
  }, [highlightedSources]);

  if (!blobUrl) {
    return <p className="p-4 text-sm text-muted-foreground">Loading PDF…</p>;
  }

  const scale = pageWidth ? PAGE_WIDTH / pageWidth : 1;

  return (
    <PdfDocument
      file={blobUrl}
      onLoadSuccess={({ numPages: loadedPages }) => setNumPages(loadedPages)}
      onLoadError={(error) => toast.error(`Failed to render PDF: ${error.message}`)}
      loading={<p className="p-4 text-sm text-muted-foreground">Rendering PDF…</p>}
    >
      {Array.from({ length: numPages }, (_, index) => index + 1).map((pageNumber) => {
        const sourcesOnThisPage = highlightedSources.filter(
          (source) => source.page_number === pageNumber
        );

        return (
          <div
            key={pageNumber}
            id={`pdf-page-${pageNumber}`}
            className="relative mx-auto mb-4 w-fit shadow-md"
          >
            <Page
              pageNumber={pageNumber}
              width={PAGE_WIDTH}
              renderTextLayer={false}
              renderAnnotationLayer={false}
            />
            {sourcesOnThisPage.map((source) =>
              (source.bbox ?? []).map((rect, rectIndex) => (
                <div
                  key={`${source.chunk_id}-${rectIndex}`}
                  className="pointer-events-none absolute bg-yellow-300/40 ring-2 ring-yellow-400"
                  style={{
                    left: rect[0] * scale,
                    top: rect[1] * scale,
                    width: (rect[2] - rect[0]) * scale,
                    height: (rect[3] - rect[1]) * scale,
                  }}
                />
              ))
            )}
          </div>
        );
      })}
    </PdfDocument>
  );
}