import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { DocumentStatusBadge } from "@/components/documents/document-status-badge";

describe("DocumentStatusBadge", () => {
  it("renders the correct label for each status", () => {
    const { rerender } = render(<DocumentStatusBadge status="pending" />);
    expect(screen.getByText("Pending")).toBeInTheDocument();

    rerender(<DocumentStatusBadge status="processing" />);
    expect(screen.getByText("Processing")).toBeInTheDocument();

    rerender(<DocumentStatusBadge status="ready" />);
    expect(screen.getByText("Ready")).toBeInTheDocument();

    rerender(<DocumentStatusBadge status="error" />);
    expect(screen.getByText("Error")).toBeInTheDocument();
  });
});
