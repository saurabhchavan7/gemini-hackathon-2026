"use client";

import { useEffect, useCallback } from "react";
import { X, ExternalLink, Clock, Tag, AlertCircle, Calendar, Check, Moon } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import { updateCapture } from "@/lib/api";
import type { CaptureItem, CaptureStatus } from "@/types/lifeos";

interface DetailDrawerProps {
  item: CaptureItem | null;
  isOpen: boolean;
  onClose: () => void;
  onUpdate: (item: CaptureItem) => void;
}

const urgencyColors = {
  low: "bg-muted text-muted-foreground",
  medium: "bg-warning/20 text-warning",
  high: "bg-destructive/20 text-destructive",
};

const intentLabels: Record<string, string> = {
  learn: "Learning",
  buy: "Purchase",
  apply: "Application",
  remember: "Remember",
  share: "Share",
  research: "Research",
  watch: "Watch",
  read: "Read",
  reference: "Reference",
};

export function DetailDrawer({ item, isOpen, onClose, onUpdate }: DetailDrawerProps) {
  // Close on escape
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape" && isOpen) {
        onClose();
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isOpen, onClose]);

  const handleStatusChange = useCallback(async (newStatus: CaptureStatus) => {
    if (!item) return;
    const updated = await updateCapture(item.id, { status: newStatus });
    if (updated) {
      onUpdate(updated);
    }
  }, [item, onUpdate]);

  if (!item) return null;

  return (
    <>
      {/* Backdrop */}
      <div
        className={cn(
          "fixed inset-0 z-40 bg-background/80 backdrop-blur-sm transition-opacity",
          isOpen ? "opacity-100" : "pointer-events-none opacity-0"
        )}
        onClick={onClose}
        aria-hidden="true"
      />

      {/* Drawer */}
      <aside
        className={cn(
          "fixed right-0 top-0 z-50 h-full w-full max-w-md transform border-l border-border bg-background shadow-xl transition-transform duration-300 ease-in-out",
          isOpen ? "translate-x-0" : "translate-x-full"
        )}
        role="dialog"
        aria-modal="true"
        aria-labelledby="drawer-title"
      >
        {/* Header */}
        <header className="flex items-center justify-between border-b border-border p-4">
          <h2 id="drawer-title" className="text-lg font-semibold text-foreground">
            Capture Details
          </h2>
          <Button
            variant="ghost"
            size="icon"
            onClick={onClose}
            aria-label="Close drawer"
          >
            <X className="h-4 w-4" />
          </Button>
        </header>

        {/* Content */}
        <div className="flex flex-col gap-6 overflow-y-auto p-4" style={{ height: "calc(100% - 65px)" }}>
          {/* Title & Source */}
          <div>
            <h3 className="text-xl font-semibold text-foreground">{item.title}</h3>
            <div className="mt-2 flex items-center gap-2 text-sm text-muted-foreground">
              <span>{item.sourceApp}</span>
              <span>•</span>
              <span>{item.windowTitle}</span>
            </div>
            {item.url && (
              <a
                href={item.url}
                target="_blank"
                rel="noopener noreferrer"
                className="mt-2 inline-flex items-center gap-1 text-sm text-accent hover:underline"
              >
                <ExternalLink className="h-3 w-3" />
                Open source
              </a>
            )}
          </div>

          {/* Status & Priority */}
          <div className="flex flex-wrap gap-2">
            <Badge variant="outline" className={urgencyColors[item.urgency]}>
              <AlertCircle className="mr-1 h-3 w-3" />
              {item.urgency} urgency
            </Badge>
            <Badge variant="outline">
              Priority: {item.priorityScore}
            </Badge>
            <Badge variant="secondary">
              {intentLabels[item.intent] || item.intent}
            </Badge>
            <Badge variant={item.status === "done" ? "default" : "outline"}>
              {item.status}
            </Badge>
          </div>

          {/* Dates */}
          <div className="space-y-2">
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <Clock className="h-4 w-4" />
              <span>Captured {item.createdAt.toLocaleDateString()} at {item.createdAt.toLocaleTimeString()}</span>
            </div>
            {item.deadline && (
              <div className="flex items-center gap-2 text-sm text-warning">
                <Calendar className="h-4 w-4" />
                <span>Due {item.deadline.toLocaleDateString()}</span>
              </div>
            )}
          </div>

          {/* Summary */}
          {item.summary && (
            <div>
              <h4 className="mb-2 text-sm font-medium text-foreground">Summary</h4>
              <p className="text-sm text-muted-foreground leading-relaxed">{item.summary}</p>
            </div>
          )}

          {/* Extracted Text */}
          {item.extractedText && (
            <div>
              <h4 className="mb-2 text-sm font-medium text-foreground">Extracted Text</h4>
              <p className="rounded-md bg-muted p-3 text-sm text-muted-foreground font-mono leading-relaxed">
                {item.extractedText}
              </p>
            </div>
          )}

          {/* Entities */}
          {item.entities && item.entities.length > 0 && (
            <div>
              <h4 className="mb-2 text-sm font-medium text-foreground">Entities</h4>
              <div className="flex flex-wrap gap-2">
                {item.entities.map((entity, i) => (
                  <Badge key={i} variant="secondary" className="text-xs">
                    {entity.type}: {entity.value}
                  </Badge>
                ))}
              </div>
            </div>
          )}

          {/* Tags */}
          {item.tags.length > 0 && (
            <div>
              <h4 className="mb-2 flex items-center gap-2 text-sm font-medium text-foreground">
                <Tag className="h-4 w-4" />
                Tags
              </h4>
              <div className="flex flex-wrap gap-2">
                {item.tags.map((tag) => (
                  <Badge key={tag} variant="outline" className="text-xs">
                    #{tag}
                  </Badge>
                ))}
              </div>
            </div>
          )}

          {/* Actions */}
          <div className="mt-auto border-t border-border pt-4">
            <h4 className="mb-3 text-sm font-medium text-foreground">Actions</h4>
            <div className="flex flex-wrap gap-2">
              {item.status !== "reviewed" && (
                <Button
                  size="sm"
                  onClick={() => handleStatusChange("reviewed")}
                  className="gap-2"
                >
                  <Check className="h-3 w-3" />
                  Mark Reviewed
                </Button>
              )}
              {item.status !== "snoozed" && (
                <Button
                  size="sm"
                  variant="secondary"
                  onClick={() => handleStatusChange("snoozed")}
                  className="gap-2"
                >
                  <Moon className="h-3 w-3" />
                  Snooze
                </Button>
              )}
              {item.status !== "done" && (
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => handleStatusChange("done")}
                  className="gap-2"
                >
                  <Check className="h-3 w-3" />
                  Mark Done
                </Button>
              )}
            </div>
          </div>
        </div>
      </aside>
    </>
  );
}
