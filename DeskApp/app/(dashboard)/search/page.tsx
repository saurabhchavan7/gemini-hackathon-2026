"use client";

import { Suspense } from "react";
import { Search } from "lucide-react";
import { SearchChat } from "@/components/lifeos/search-chat";

function SearchLoading() {
  return (
    <div className="flex h-full items-center justify-center">
      <div className="flex flex-col items-center gap-4">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
        <p className="text-sm text-muted-foreground">Loading search...</p>
      </div>
    </div>
  );
}

function SearchPageContent() {
  return (
    <div className="flex h-full flex-col">
      {/* Header */}
      <div className="border-b border-border px-6 py-4">
        <div className="flex items-center gap-3">
          <Search className="h-5 w-5 text-muted-foreground" />
          <h1 className="text-xl font-semibold text-foreground">AI Search</h1>
          <span className="text-sm text-muted-foreground">Ask questions about your captures</span>
        </div>
      </div>

      {/* AI Chat */}
      <SearchChat />
    </div>
  );
}

export default function SearchPage() {
  return (
    <Suspense fallback={<SearchLoading />}>
      <SearchPageContent />
    </Suspense>
  );
}