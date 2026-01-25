"use client";

import React from "react"

import { useState, useCallback, useEffect } from "react";
import { Sidebar } from "./sidebar";
import { CommandBar } from "./command-bar";
import { DetailDrawer } from "./detail-drawer";
import { CommandPalette } from "./command-palette";
import type { CaptureItem } from "@/types/lifeos";

interface AppShellProps {
  children: React.ReactNode;
}

export function AppShell({ children }: AppShellProps) {
  const [selectedItem, setSelectedItem] = useState<CaptureItem | null>(null);
  const [isDrawerOpen, setIsDrawerOpen] = useState(false);
  const [isCommandPaletteOpen, setIsCommandPaletteOpen] = useState(false);

  const handleSelectItem = useCallback((item: CaptureItem) => {
    setSelectedItem(item);
    setIsDrawerOpen(true);
  }, []);

  const handleCloseDrawer = useCallback(() => {
    setIsDrawerOpen(false);
  }, []);

  const handleUpdateItem = useCallback((updatedItem: CaptureItem) => {
    setSelectedItem(updatedItem);
  }, []);

  // Global keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Ctrl+K or Cmd+K to open command palette
      if ((e.ctrlKey || e.metaKey) && e.key === "k") {
        e.preventDefault();
        setIsCommandPaletteOpen(true);
      }
      // Escape to close
      if (e.key === "Escape") {
        setIsCommandPaletteOpen(false);
        setIsDrawerOpen(false);
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, []);

  return (
    <div className="flex h-screen overflow-hidden bg-background">
      <Sidebar />
      <div className="flex flex-1 flex-col overflow-hidden">
        <CommandBar onOpenCommandPalette={() => setIsCommandPaletteOpen(true)} />
        <main className="flex-1 overflow-auto p-6">
          {typeof children === "function"
            ? (children as (props: { onSelectItem: (item: CaptureItem) => void }) => React.ReactNode)({
                onSelectItem: handleSelectItem,
              })
            : children}
        </main>
      </div>
      <DetailDrawer
        item={selectedItem}
        isOpen={isDrawerOpen}
        onClose={handleCloseDrawer}
        onUpdate={handleUpdateItem}
      />
      <CommandPalette
        isOpen={isCommandPaletteOpen}
        onClose={() => setIsCommandPaletteOpen(false)}
      />
      
    </div>
  );
}
