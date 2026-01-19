"use client";

import { useState, useMemo } from "react";
import { Search, Filter, X, Calendar } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import { CaptureListItem } from "@/components/lifeos/capture-list-item";
import { useLifeOS } from "@/components/lifeos/lifeos-provider";
import type { Intent, Urgency } from "@/types/lifeos";
import { useSearchParams, Suspense } from "next/navigation";
import Loading from "./loading";

const intents: { value: Intent | "all"; label: string }[] = [
  { value: "all", label: "All Intents" },
  { value: "learn", label: "Learn" },
  { value: "buy", label: "Buy" },
  { value: "apply", label: "Apply" },
  { value: "remember", label: "Remember" },
  { value: "share", label: "Share" },
  { value: "research", label: "Research" },
  { value: "watch", label: "Watch" },
  { value: "read", label: "Read" },
  { value: "reference", label: "Reference" },
];

const urgencies: { value: Urgency | "all"; label: string }[] = [
  { value: "all", label: "All Urgency" },
  { value: "low", label: "Low" },
  { value: "medium", label: "Medium" },
  { value: "high", label: "High" },
];

const sourceApps = ["All Sources", "Chrome", "Notion", "Google Drive", "Gmail", "Netflix"];

export default function SearchPage() {
  const searchParams = useSearchParams();
  const { captures, isLoading, selectItem, selectedItem } = useLifeOS();
  const [query, setQuery] = useState(searchParams?.get("query") || "");
  const [selectedIntent, setSelectedIntent] = useState<Intent | "all">(searchParams?.get("intent") || "all");
  const [selectedUrgency, setSelectedUrgency] = useState<Urgency | "all">(searchParams?.get("urgency") || "all");
  const [selectedSource, setSelectedSource] = useState(searchParams?.get("source") || "All Sources");
  const [selectedTags, setSelectedTags] = useState<string[]>(searchParams?.getAll("tags") || []);
  const [dateRange, setDateRange] = useState<{ start: string; end: string }>({
    start: searchParams?.get("start") || "",
    end: searchParams?.get("end") || "",
  });

  // Get all unique tags from captures
  const allTags = useMemo(() => {
    const tags = new Set<string>();
    captures.forEach((c) => c.tags.forEach((t) => tags.add(t)));
    return Array.from(tags).sort();
  }, [captures]);

  // Filter captures
  const filteredCaptures = useMemo(() => {
    return captures.filter((capture) => {
      // Text search
      if (query) {
        const searchLower = query.toLowerCase();
        const matchesText =
          capture.title.toLowerCase().includes(searchLower) ||
          capture.summary?.toLowerCase().includes(searchLower) ||
          capture.extractedText?.toLowerCase().includes(searchLower) ||
          capture.tags.some((t) => t.toLowerCase().includes(searchLower));
        if (!matchesText) return false;
      }

      // Intent filter
      if (selectedIntent !== "all" && capture.intent !== selectedIntent) {
        return false;
      }

      // Urgency filter
      if (selectedUrgency !== "all" && capture.urgency !== selectedUrgency) {
        return false;
      }

      // Source filter
      if (selectedSource !== "All Sources" && capture.sourceApp !== selectedSource) {
        return false;
      }

      // Tags filter
      if (selectedTags.length > 0 && !selectedTags.some((t) => capture.tags.includes(t))) {
        return false;
      }

      // Date range filter
      if (dateRange.start) {
        const startDate = new Date(dateRange.start);
        if (new Date(capture.createdAt) < startDate) return false;
      }
      if (dateRange.end) {
        const endDate = new Date(dateRange.end);
        endDate.setHours(23, 59, 59, 999);
        if (new Date(capture.createdAt) > endDate) return false;
      }

      return true;
    });
  }, [captures, query, selectedIntent, selectedUrgency, selectedSource, selectedTags, dateRange]);

  const hasActiveFilters =
    selectedIntent !== "all" ||
    selectedUrgency !== "all" ||
    selectedSource !== "All Sources" ||
    selectedTags.length > 0 ||
    dateRange.start ||
    dateRange.end;

  const clearFilters = () => {
    setSelectedIntent("all");
    setSelectedUrgency("all");
    setSelectedSource("All Sources");
    setSelectedTags([]);
    setDateRange({ start: "", end: "" });
  };

  const toggleTag = (tag: string) => {
    setSelectedTags((prev) =>
      prev.includes(tag) ? prev.filter((t) => t !== tag) : [...prev, tag]
    );
  };

  return (
    <Suspense fallback={<Loading />}>
      <div className="flex h-full flex-col">
        {/* Header */}
        <div className="border-b border-border px-6 py-4">
          <div className="flex items-center gap-3">
            <Search className="h-5 w-5 text-muted-foreground" />
            <h1 className="text-xl font-semibold text-foreground">Search</h1>
          </div>
        </div>

        {/* Search & Filters */}
        <div className="border-b border-border px-6 py-4 space-y-4">
          {/* Search Input */}
          <div className="relative">
            <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
            <Input
              type="search"
              placeholder="Search titles, summaries, tags..."
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              className="pl-10 bg-muted/50"
            />
          </div>

          {/* Filter Row */}
          <div className="flex flex-wrap items-center gap-3">
            {/* Intent */}
            <Select value={selectedIntent} onValueChange={(v) => setSelectedIntent(v as Intent | "all")}>
              <SelectTrigger className="w-36 bg-muted/50">
                <SelectValue placeholder="Intent" />
              </SelectTrigger>
              <SelectContent>
                {intents.map((intent) => (
                  <SelectItem key={intent.value} value={intent.value}>
                    {intent.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>

            {/* Urgency */}
            <Select value={selectedUrgency} onValueChange={(v) => setSelectedUrgency(v as Urgency | "all")}>
              <SelectTrigger className="w-36 bg-muted/50">
                <SelectValue placeholder="Urgency" />
              </SelectTrigger>
              <SelectContent>
                {urgencies.map((urgency) => (
                  <SelectItem key={urgency.value} value={urgency.value}>
                    {urgency.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>

            {/* Source */}
            <Select value={selectedSource} onValueChange={setSelectedSource}>
              <SelectTrigger className="w-36 bg-muted/50">
                <SelectValue placeholder="Source" />
              </SelectTrigger>
              <SelectContent>
                {sourceApps.map((source) => (
                  <SelectItem key={source} value={source}>
                    {source}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>

            {/* Tags Popover */}
            <Popover>
              <PopoverTrigger asChild>
                <Button variant="outline" size="sm" className="gap-2 bg-muted/50">
                  <Filter className="h-3.5 w-3.5" />
                  Tags
                  {selectedTags.length > 0 && (
                    <Badge variant="secondary" className="ml-1 h-5 px-1.5 text-xs">
                      {selectedTags.length}
                    </Badge>
                  )}
                </Button>
              </PopoverTrigger>
              <PopoverContent className="w-64 p-3" align="start">
                <div className="space-y-2">
                  <p className="text-sm font-medium text-foreground">Filter by tags</p>
                  <div className="flex flex-wrap gap-1.5 max-h-48 overflow-y-auto">
                    {allTags.map((tag) => (
                      <Badge
                        key={tag}
                        variant={selectedTags.includes(tag) ? "default" : "outline"}
                        className="cursor-pointer text-xs"
                        onClick={() => toggleTag(tag)}
                      >
                        #{tag}
                      </Badge>
                    ))}
                  </div>
                </div>
              </PopoverContent>
            </Popover>

            {/* Date Range */}
            <Popover>
              <PopoverTrigger asChild>
                <Button variant="outline" size="sm" className="gap-2 bg-muted/50">
                  <Calendar className="h-3.5 w-3.5" />
                  Date Range
                  {(dateRange.start || dateRange.end) && (
                    <Badge variant="secondary" className="ml-1 h-5 px-1.5 text-xs">
                      Set
                    </Badge>
                  )}
                </Button>
              </PopoverTrigger>
              <PopoverContent className="w-64 p-3" align="start">
                <div className="space-y-3">
                  <p className="text-sm font-medium text-foreground">Date range</p>
                  <div className="space-y-2">
                    <div>
                      <label className="text-xs text-muted-foreground">From</label>
                      <Input
                        type="date"
                        value={dateRange.start}
                        onChange={(e) => setDateRange((prev) => ({ ...prev, start: e.target.value }))}
                        className="mt-1"
                      />
                    </div>
                    <div>
                      <label className="text-xs text-muted-foreground">To</label>
                      <Input
                        type="date"
                        value={dateRange.end}
                        onChange={(e) => setDateRange((prev) => ({ ...prev, end: e.target.value }))}
                        className="mt-1"
                      />
                    </div>
                  </div>
                </div>
              </PopoverContent>
            </Popover>

            {/* Clear Filters */}
            {hasActiveFilters && (
              <Button variant="ghost" size="sm" onClick={clearFilters} className="gap-1 text-muted-foreground">
                <X className="h-3.5 w-3.5" />
                Clear filters
              </Button>
            )}
          </div>

          {/* Active Tags */}
          {selectedTags.length > 0 && (
            <div className="flex flex-wrap gap-1.5">
              {selectedTags.map((tag) => (
                <Badge key={tag} variant="secondary" className="gap-1 text-xs">
                  #{tag}
                  <button
                    onClick={() => toggleTag(tag)}
                    className="ml-1 rounded-full hover:bg-muted"
                    aria-label={`Remove ${tag} filter`}
                  >
                    <X className="h-3 w-3" />
                  </button>
                </Badge>
              ))}
            </div>
          )}
        </div>

        {/* Results */}
        <div className="flex-1 overflow-auto p-6">
          <div className="mb-4 text-sm text-muted-foreground">
            {filteredCaptures.length} {filteredCaptures.length === 1 ? "result" : "results"}
            {query && ` for "${query}"`}
          </div>

          {isLoading ? (
            <div className="flex h-64 items-center justify-center">
              <div className="h-8 w-8 animate-spin rounded-full border-2 border-muted border-t-accent" />
            </div>
          ) : filteredCaptures.length === 0 ? (
            <div className="flex h-64 flex-col items-center justify-center text-center">
              <Search className="h-12 w-12 text-muted-foreground/50" />
              <h3 className="mt-4 text-lg font-medium text-foreground">No results found</h3>
              <p className="mt-1 text-sm text-muted-foreground">
                Try adjusting your search or filters
              </p>
            </div>
          ) : (
            <div className="grid gap-3">
              {filteredCaptures.map((item) => (
                <CaptureListItem
                  key={item.id}
                  item={item}
                  isSelected={selectedItem?.id === item.id}
                  onClick={() => selectItem(item)}
                />
              ))}
            </div>
          )}
        </div>
      </div>
    </Suspense>
  );
}
