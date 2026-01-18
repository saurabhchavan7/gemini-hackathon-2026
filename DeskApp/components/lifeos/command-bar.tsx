"use client";

import { Search, Plus } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Kbd } from "@/components/ui/kbd";

interface CommandBarProps {
  onOpenCommandPalette: () => void;
}

export function CommandBar({ onOpenCommandPalette }: CommandBarProps) {
  return (
    <header className="flex h-14 items-center justify-between border-b border-border bg-background px-6">
      {/* Search */}
      <div className="relative flex-1 max-w-md">
        <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" aria-hidden="true" />
        <Input
          type="search"
          placeholder="Search captures..."
          className="h-9 w-full bg-muted/50 pl-9 pr-16 text-sm placeholder:text-muted-foreground focus:bg-muted"
          onClick={onOpenCommandPalette}
          readOnly
          aria-label="Open search"
        />
        <div className="absolute right-2 top-1/2 -translate-y-1/2 flex items-center gap-1">
          <Kbd>Ctrl</Kbd>
          <Kbd>K</Kbd>
        </div>
      </div>

      {/* Actions */}
      <div className="flex items-center gap-3">
        <Button
          size="sm"
          className="gap-2"
          aria-label="Capture new item"
        >
          <Plus className="h-4 w-4" aria-hidden="true" />
          Capture
        </Button>
      </div>
    </header>
  );
}
