"use client";

import React from "react"

import { useState, useEffect } from "react";
import { Sidebar } from "./sidebar";
import { CommandBar } from "./command-bar";
import { DetailDrawer } from "./detail-drawer";
import { CommandPalette } from "./command-palette";
import { FloatingCaptureButton } from "./floating-capture-button";
import { LifeOSProvider, useLifeOS } from "./lifeos-provider";

interface ShellLayoutProps {
  children: React.ReactNode;
}

function ShellLayoutInner({ children }: ShellLayoutProps) {
  const [isCommandPaletteOpen, setIsCommandPaletteOpen] = useState(false);
  const { selectedItem, isDrawerOpen, closeDrawer, updateCapture } = useLifeOS();

  // Global keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key === "k") {
        e.preventDefault();
        setIsCommandPaletteOpen(true);
      }
      if (e.key === "Escape") {
        setIsCommandPaletteOpen(false);
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, []);

  const handleUpdateItem = async (item: typeof selectedItem) => {
    if (item) {
      await updateCapture(item.id, item);
    }
  };

  return (
    <div className="flex h-screen overflow-hidden bg-background">
      <Sidebar />
      <div className="flex flex-1 flex-col overflow-hidden">
        <CommandBar onOpenCommandPalette={() => setIsCommandPaletteOpen(true)} />
        <main className="flex-1 overflow-auto">
          {children}
        </main>
      </div>
      <DetailDrawer
        item={selectedItem}
        isOpen={isDrawerOpen}
        onClose={closeDrawer}
        onUpdate={handleUpdateItem}
      />
      <CommandPalette
        isOpen={isCommandPaletteOpen}
        onClose={() => setIsCommandPaletteOpen(false)}
      />
      <FloatingCaptureButton />
    </div>
  );
}

export function ShellLayout({ children }: ShellLayoutProps) {
  return (
    <LifeOSProvider>
      <ShellLayoutInner>{children}</ShellLayoutInner>
    </LifeOSProvider>
  );
}
