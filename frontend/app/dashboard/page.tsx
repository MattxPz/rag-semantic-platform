"use client";

import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { DocumentUpload } from "@/components/documents/document-upload";
import { DocumentList } from "@/components/documents/document-list";
import { useAuthStore } from "@/stores/auth-store";

export default function DashboardPage() {
  const router = useRouter();
  const user = useAuthStore((s) => s.user);
  const clearAuth = useAuthStore((s) => s.clearAuth);

  const handleLogout = () => {
    clearAuth();
    router.push("/login");
  };

  return (
    <div className="mx-auto max-w-3xl px-4 py-8">
      <header className="mb-8 flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold">RAG Platform</h1>
          <p className="text-sm text-muted-foreground">{user?.email}</p>
        </div>
        <Button variant="outline" onClick={handleLogout}>
          Log out
        </Button>
      </header>

      <section className="mb-8">
        <DocumentUpload />
      </section>

      <section>
        <h2 className="mb-3 text-sm font-medium text-muted-foreground">Your documents</h2>
        <DocumentList />
      </section>
    </div>
  );
}