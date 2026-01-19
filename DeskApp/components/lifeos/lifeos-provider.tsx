"use client";

import { createContext, useContext, useState, useCallback, useEffect, type ReactNode } from "react";
import { listCaptures, updateCapture as apiUpdateCapture } from "@/lib/api";
import type { CaptureItem } from "@/types/lifeos";

interface LifeOSContextType {
  captures: CaptureItem[];
  isLoading: boolean;
  selectedItem: CaptureItem | null;
  isDrawerOpen: boolean;
  selectItem: (item: CaptureItem) => void;
  closeDrawer: () => void;
  updateCapture: (id: string, updates: Partial<CaptureItem>) => Promise<void>;
  refreshCaptures: () => Promise<void>;
}

const LifeOSContext = createContext<LifeOSContextType | null>(null);

export function useLifeOS() {
  const context = useContext(LifeOSContext);
  if (!context) {
    throw new Error("useLifeOS must be used within a LifeOSProvider");
  }
  return context;
}

interface LifeOSProviderProps {
  children: ReactNode;
}

export function LifeOSProvider({ children }: LifeOSProviderProps) {
  const [captures, setCaptures] = useState<CaptureItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [selectedItem, setSelectedItem] = useState<CaptureItem | null>(null);
  const [isDrawerOpen, setIsDrawerOpen] = useState(false);

  const refreshCaptures = useCallback(async () => {
    setIsLoading(true);
    try {
      const data = await listCaptures();
      setCaptures(data);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    refreshCaptures();
  }, [refreshCaptures]);

  const selectItem = useCallback((item: CaptureItem) => {
    setSelectedItem(item);
    setIsDrawerOpen(true);
  }, []);

  const closeDrawer = useCallback(() => {
    setIsDrawerOpen(false);
  }, []);

  const updateCapture = useCallback(async (id: string, updates: Partial<CaptureItem>) => {
    const updated = await apiUpdateCapture(id, updates);
    if (updated) {
      setCaptures((prev) => prev.map((c) => (c.id === id ? updated : c)));
      if (selectedItem?.id === id) {
        setSelectedItem(updated);
      }
    }
  }, [selectedItem?.id]);

  return (
    <LifeOSContext.Provider
      value={{
        captures,
        isLoading,
        selectedItem,
        isDrawerOpen,
        selectItem,
        closeDrawer,
        updateCapture,
        refreshCaptures,
      }}
    >
      {children}
    </LifeOSContext.Provider>
  );
}
