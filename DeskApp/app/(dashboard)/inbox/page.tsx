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
import { ChevronDown, ArrowUpDown, Inbox as InboxIcon, RefreshCw } from "lucide-react";
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
  const { captures, isLoading, selectItem, selectedItem, refreshCaptures } = useLifeOS();
  const [activeTab, setActiveTab] = useState<TabFilter>("all");
  const [sortBy, setSortBy] = useState<SortOption>("newest");
  const [isRefreshing, setIsRefreshing] = useState(false);

  const handleRefresh = async () => {
    setIsRefreshing(true);
    await refreshCaptures();
    setIsRefreshing(false);
  };

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
    <div className="flex flex-col h-full" style={{ backgroundColor: 'var(--color-bg-primary)' }}>      
   {/* Header */}
<div className="px-6 py-5">
  <div className="flex items-start justify-between mb-1">
    <div>
      <h1 className="text-2xl font-semibold" style={{ color: 'var(--color-text-primary)' }}>Inbox</h1>
      <p className="text-sm mt-0.5" style={{ color: 'var(--color-text-secondary)' }}>
        {captures.length} item{captures.length !== 1 ? 's' : ''} need{captures.length === 1 ? 's' : ''} your attention
      </p>
    </div>
    
    <div className="flex items-center gap-2">
      {/* Refresh */}
      <Button
        variant="ghost"
        size="sm"
        onClick={handleRefresh}
        disabled={isRefreshing}
        className="h-9 w-9 rounded-full p-0"
      >
        <RefreshCw className={`h-4 w-4 ${isRefreshing ? 'animate-spin' : ''}`} />
      </Button>
    </div>
  </div>
</div>

      {/* Tabs */}
      <Tabs value={activeTab} onValueChange={(v) => setActiveTab(v as TabFilter)} className="flex-1 flex flex-col">
  <div className="px-6 mb-4">
    <TabsList className="h-10 bg-transparent p-0 gap-2 inline-flex">
      {tabFilters.map((tab) => {
        const count = tab.count ? tab.count(captures) : null;
        return (
          <TabsTrigger
  key={tab.value}
  value={tab.value}
  className="h-10 px-4 rounded-full border-0 data-[state=active]:shadow-none font-medium text-sm transition-all"
  style={{
    backgroundColor: tab.value === activeTab ? 'var(--color-accent-blue)' : 'transparent',
    color: tab.value === activeTab ? '#ffffff' : 'var(--color-text-secondary)',
  }}
  onMouseEnter={(e) => {
    if (tab.value !== activeTab) {
      e.currentTarget.style.backgroundColor = 'var(--color-bg-tertiary)';
    }
  }}
  onMouseLeave={(e) => {
    if (tab.value !== activeTab) {
      e.currentTarget.style.backgroundColor = 'transparent';
    }
  }}
>
            {tab.label}
            {count !== null && count > 0 && (
              <span 
                className="ml-2 px-1.5 py-0.5 text-xs rounded-full font-medium"
                style={{
                  backgroundColor: tab.value === activeTab ? 'rgba(255,255,255,0.2)' : 'var(--color-bg-tertiary)',
                  color: tab.value === activeTab ? '#ffffff' : 'var(--color-text-secondary)'
                }}
              >
                {count}
              </span>
            )}
          </TabsTrigger>
        );
      })}
    </TabsList>
    {/* Sort Dropdown */}
  <DropdownMenu>
    <DropdownMenuTrigger asChild>
      <Button variant="outline" size="sm" className="gap-2 h-9">
        <ArrowUpDown className="h-3.5 w-3.5" />
        {sortOptions.find((o) => o.value === sortBy)?.label}
        <ChevronDown className="h-3.5 w-3.5" />
      </Button>
    </DropdownMenuTrigger>
    <DropdownMenuContent 
    align="end"
  className="bg-background border border-border shadow-md">
      {sortOptions.map((option) => (
        <DropdownMenuItem
          key={option.value}
          onClick={() => setSortBy(option.value)}
        >
          {option.label}
        </DropdownMenuItem>
      ))}
    </DropdownMenuContent>
  </DropdownMenu>
  </div>

<TabsContent value={activeTab} className="flex-1 overflow-auto p-6 mt-0" style={{ backgroundColor: 'var(--color-bg-secondary)' }}>
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