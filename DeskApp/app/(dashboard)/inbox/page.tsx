"use client";

import { useState, useMemo } from "react";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { ChevronDown, ArrowUpDown, Inbox as InboxIcon } from "lucide-react";
import { CaptureListItem } from "@/components/lifeos/capture-list-item";
import { useLifeOS } from "@/components/lifeos/lifeos-provider";
import type { CaptureItem, CaptureStatus } from "@/types/lifeos";

type SortOption = "newest" | "priority" | "deadline";
type TabFilter = "all" | "unreviewed" | "snoozed" | "expiring";

const sortOptions: { value: SortOption; label: string }[] = [
  { value: "newest", label: "Newest First" },
  { value: "priority", label: "Highest Priority" },
  { value: "deadline", label: "Deadline Soon" },
];

const tabFilters: { value: TabFilter; label: string; count?: (items: CaptureItem[]) => number }[] = [
  { value: "all", label: "All" },
  { 
    value: "unreviewed", 
    label: "Unreviewed",
    count: (items) => items.filter(i => i.status === "unreviewed").length
  },
  { 
    value: "snoozed", 
    label: "Snoozed",
    count: (items) => items.filter(i => i.status === "snoozed").length
  },
  { 
    value: "expiring", 
    label: "Expiring",
    count: (items) => items.filter(i => i.deadline && new Date(i.deadline).getTime() - Date.now() < 7 * 24 * 60 * 60 * 1000).length
  },
];

export default function InboxPage() {
  const { captures, isLoading, selectItem, selectedItem } = useLifeOS();
  const [activeTab, setActiveTab] = useState<TabFilter>("all");
  const [sortBy, setSortBy] = useState<SortOption>("newest");

  const filteredAndSortedCaptures = useMemo(() => {
    let filtered = [...captures];

    // Filter by tab
    switch (activeTab) {
      case "unreviewed":
        filtered = filtered.filter((c) => c.status === "unreviewed");
        break;
      case "snoozed":
        filtered = filtered.filter((c) => c.status === "snoozed");
        break;
      case "expiring":
        filtered = filtered.filter(
          (c) => c.deadline && new Date(c.deadline).getTime() - Date.now() < 7 * 24 * 60 * 60 * 1000
        );
        break;
    }

    // Sort
    switch (sortBy) {
      case "newest":
        filtered.sort((a, b) => new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime());
        break;
      case "priority":
        filtered.sort((a, b) => b.priorityScore - a.priorityScore);
        break;
      case "deadline":
        filtered.sort((a, b) => {
          if (!a.deadline && !b.deadline) return 0;
          if (!a.deadline) return 1;
          if (!b.deadline) return -1;
          return new Date(a.deadline).getTime() - new Date(b.deadline).getTime();
        });
        break;
    }

    return filtered;
  }, [captures, activeTab, sortBy]);

  if (isLoading) {
    return (
      <div className="flex h-full items-center justify-center">
        <div className="flex flex-col items-center gap-3 text-muted-foreground">
          <div className="h-8 w-8 animate-spin rounded-full border-2 border-muted border-t-accent" />
          <span className="text-sm">Loading captures...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-border px-6 py-4">
        <div className="flex items-center gap-3">
          <InboxIcon className="h-5 w-5 text-muted-foreground" />
          <h1 className="text-xl font-semibold text-foreground">Inbox</h1>
          <span className="rounded-full bg-muted px-2 py-0.5 text-xs text-muted-foreground">
            {captures.length} items
          </span>
        </div>

        {/* Sort dropdown */}
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="outline" size="sm" className="gap-2 bg-transparent">
              <ArrowUpDown className="h-3.5 w-3.5" />
              {sortOptions.find((o) => o.value === sortBy)?.label}
              <ChevronDown className="h-3.5 w-3.5" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            {sortOptions.map((option) => (
              <DropdownMenuItem
                key={option.value}
                onClick={() => setSortBy(option.value)}
                className={sortBy === option.value ? "bg-accent" : ""}
              >
                {option.label}
              </DropdownMenuItem>
            ))}
          </DropdownMenuContent>
        </DropdownMenu>
      </div>

      {/* Tabs */}
      <Tabs value={activeTab} onValueChange={(v) => setActiveTab(v as TabFilter)} className="flex-1 flex flex-col">
        <div className="border-b border-border px-6">
          <TabsList className="h-12 bg-transparent p-0 gap-6">
            {tabFilters.map((tab) => {
              const count = tab.count ? tab.count(captures) : null;
              return (
                <TabsTrigger
                  key={tab.value}
                  value={tab.value}
                  className="h-12 rounded-none border-b-2 border-transparent px-0 data-[state=active]:border-accent data-[state=active]:bg-transparent data-[state=active]:shadow-none"
                >
                  {tab.label}
                  {count !== null && count > 0 && (
                    <span className="ml-2 rounded-full bg-accent/20 px-1.5 py-0.5 text-xs text-accent">
                      {count}
                    </span>
                  )}
                </TabsTrigger>
              );
            })}
          </TabsList>
        </div>

        <TabsContent value={activeTab} className="flex-1 overflow-auto p-6 mt-0">
          {filteredAndSortedCaptures.length === 0 ? (
            <div className="flex h-64 flex-col items-center justify-center text-center">
              <InboxIcon className="h-12 w-12 text-muted-foreground/50" />
              <h3 className="mt-4 text-lg font-medium text-foreground">No captures</h3>
              <p className="mt-1 text-sm text-muted-foreground">
                {activeTab === "all"
                  ? "Your inbox is empty. Start capturing!"
                  : `No ${activeTab} items found.`}
              </p>
            </div>
          ) : (
            <div className="grid gap-3">
              {filteredAndSortedCaptures.map((item) => (
                <CaptureListItem
                  key={item.id}
                  item={item}
                  isSelected={selectedItem?.id === item.id}
                  onClick={() => selectItem(item)}
                />
              ))}
            </div>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
}
