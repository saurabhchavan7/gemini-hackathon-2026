"use client";

import React from "react"

import { useState, useEffect } from "react";
import {
  FolderOpen,
  GraduationCap,
  AlertTriangle,
  ShoppingCart,
  Briefcase,
  GripVertical,
  ChevronRight,
  ArrowLeft,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { listCollections, listCaptures } from "@/lib/api";
import { CaptureListItem } from "@/components/lifeos/capture-list-item";
import { useLifeOS } from "@/components/lifeos/lifeos-provider";
import type { SmartCollection, CaptureItem } from "@/types/lifeos";

const iconMap: Record<string, React.ComponentType<{ className?: string }>> = {
  GraduationCap,
  AlertTriangle,
  ShoppingCart,
  Briefcase,
  FolderOpen,
};

export default function CollectionsPage() {
  const { selectItem, selectedItem } = useLifeOS();
  const [collections, setCollections] = useState<SmartCollection[]>([]);
  const [captures, setCaptures] = useState<CaptureItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [selectedCollection, setSelectedCollection] = useState<SmartCollection | null>(null);
  const [draggedIndex, setDraggedIndex] = useState<number | null>(null);

  useEffect(() => {
    async function loadData() {
      setIsLoading(true);
      const [collectionsData, capturesData] = await Promise.all([
        listCollections(),
        listCaptures(),
      ]);
      setCollections(collectionsData);
      setCaptures(capturesData);
      setIsLoading(false);
    }
    loadData();
  }, []);

  const getCollectionCaptures = (collection: SmartCollection) => {
    return captures.filter((c) => collection.captureIds.includes(c.id));
  };

  const handleDragStart = (index: number) => {
    setDraggedIndex(index);
  };

  const handleDragOver = (e: React.DragEvent, index: number) => {
    e.preventDefault();
    if (draggedIndex === null || draggedIndex === index) return;

    const newItems = [...collectionCaptures];
    const draggedItem = newItems[draggedIndex];
    newItems.splice(draggedIndex, 1);
    newItems.splice(index, 0, draggedItem);

    // Update local state for visual feedback
    setDraggedIndex(index);
  };

  const handleDragEnd = () => {
    setDraggedIndex(null);
  };

  const collectionCaptures = selectedCollection ? getCollectionCaptures(selectedCollection) : [];

  if (isLoading) {
    return (
      <div className="flex h-full items-center justify-center">
        <div className="flex flex-col items-center gap-3 text-muted-foreground">
          <div className="h-8 w-8 animate-spin rounded-full border-2 border-muted border-t-accent" />
          <span className="text-sm">Loading collections...</span>
        </div>
      </div>
    );
  }

  // Collection detail view
  if (selectedCollection) {
    return (
      <div className="flex h-full flex-col">
        {/* Header */}
        <div className="border-b border-border px-6 py-4">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setSelectedCollection(null)}
            className="mb-3 -ml-2 gap-2 text-muted-foreground"
          >
            <ArrowLeft className="h-4 w-4" />
            Back to Collections
          </Button>
          <div className="flex items-center gap-3">
            {(() => {
              const Icon = iconMap[selectedCollection.icon] || FolderOpen;
              return <Icon className="h-5 w-5 text-blue-500" />;
            })()}
            <h1 className="text-xl font-semibold text-foreground">{selectedCollection.name}</h1>
            <Badge variant="secondary">{collectionCaptures.length} items</Badge>
          </div>
          <p className="mt-1 text-sm text-muted-foreground">{selectedCollection.description}</p>
        </div>

        {/* Collection Items - Reorderable */}
        <div className="flex-1 overflow-auto p-6">
          {collectionCaptures.length === 0 ? (
            <div className="flex h-64 flex-col items-center justify-center text-center">
              <FolderOpen className="h-5 w-5" style={{ color: 'var(--color-accent-blue)' }} />              <h3 className="mt-4 text-lg font-medium text-foreground">No items</h3>
              <p className="mt-1 text-sm text-muted-foreground">
                This collection is empty
              </p>
            </div>
          ) : (
            <div className="space-y-2">
              <p className="mb-4 text-xs text-muted-foreground">
                Drag items to reorder
              </p>
              {collectionCaptures.map((item, index) => (
                <div
                  key={item.id}
                  draggable
                  onDragStart={() => handleDragStart(index)}
                  onDragOver={(e) => handleDragOver(e, index)}
                  onDragEnd={handleDragEnd}
                  className={`flex items-center gap-2 ${draggedIndex === index ? "opacity-50" : ""
                    }`}
                >
                  <div className="cursor-grab text-muted-foreground hover:text-foreground">
                    <GripVertical className="h-4 w-4" />
                  </div>
                  <div className="flex-1">
                    <CaptureListItem
                      item={item}
                      isSelected={selectedItem?.id === item.id}
                      onClick={() => selectItem(item)}
                    />
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    );
  }

  // Collections grid view
  return (
    <div className="flex h-full flex-col">
      {/* Header */}
      <div className="border-b border-border px-6 py-4">
        <div className="flex items-center gap-3">
          <FolderOpen className="h-5 w-5 text-muted-foreground" />
          <h1 className="text-xl font-semibold text-foreground">Collections</h1>
          <span className="rounded-full px-2 py-0.5 text-xs" style={{
            backgroundColor: 'var(--color-bg-tertiary)',
            color: 'var(--color-text-secondary)'
          }}>
            {collections.length} collections
          </span>
        </div>
      </div>

      {/* Collections Grid */}
      <div className="flex-1 overflow-auto p-6">
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {collections.map((collection) => {
            const Icon = iconMap[collection.icon] || FolderOpen;
            const itemCount = getCollectionCaptures(collection).length;

            // Color scheme per collection type
            const colorSchemes: Record<string, { bg: string, icon: string }> = {
              'Briefcase': { bg: '#e3f2fd', icon: '#1976d2' },      // Blue for Work
              'GraduationCap': { bg: '#e8f5e9', icon: '#388e3c' },  // Green for Learning
              'AlertTriangle': { bg: '#fff3e0', icon: '#f57c00' },  // Orange
              'ShoppingCart': { bg: '#f3e5f5', icon: '#7b1fa2' },   // Purple
              'FolderOpen': { bg: '#e8f0fe', icon: '#1a73e8' },     // Blue default
            };

            const scheme = colorSchemes[collection.icon] || colorSchemes['FolderOpen'];

            return (
              <Card
                key={collection.id}
                className="group cursor-pointer p-6 transition-all rounded-2xl border-0"
                style={{
                  backgroundColor: 'var(--color-bg-card)',
                  boxShadow: '0 1px 3px rgba(0,0,0,0.1)'
                }}
                onClick={() => setSelectedCollection(collection)}
                onMouseEnter={(e) => {
                  e.currentTarget.style.boxShadow = '0 8px 16px rgba(0,0,0,0.12)';
                  e.currentTarget.style.transform = 'translateY(-4px)';
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.boxShadow = '0 1px 3px rgba(0,0,0,0.1)';
                  e.currentTarget.style.transform = 'translateY(0)';
                }}
              >
                <div className="flex items-start justify-between">
                  <div
                    className="flex h-12 w-12 items-center justify-center rounded-xl"
                    style={{
                      backgroundColor: scheme.bg
                    }}
                  >
                    <Icon className="h-6 w-6" />
                  </div>
                  <ChevronRight
                    className="h-5 w-5 opacity-0 transition-opacity group-hover:opacity-100 text-muted-foreground"
                  />
                </div>

                <h3 className="mt-4 text-base font-semibold text-foreground">
                  {collection.name}
                </h3>

                <p className="mt-2 text-sm line-clamp-2 text-muted-foreground">
                  {collection.description}
                </p>

                <div className="mt-4">
                  <span
                    className="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium"
                    style={{
                      backgroundColor: 'var(--color-bg-tertiary)',
                      color: 'var(--color-text-secondary)'
                    }}
                  >
                    {itemCount} {itemCount === 1 ? "item" : "items"}
                  </span>
                </div>
              </Card>
            );
          })}
        </div>
      </div>
    </div>
  );
}
