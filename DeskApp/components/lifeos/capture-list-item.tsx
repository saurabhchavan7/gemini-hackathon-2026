"use client";

import { AlertCircle, Calendar, Clock, ExternalLink } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import type { CaptureItem } from "@/types/lifeos";
import { AskGeminiButton } from "./ask-gemini-button";

interface CaptureListItemProps {
  item: CaptureItem;
  isSelected?: boolean;
  onClick: () => void;
}

const urgencyColors = {
  low: "bg-muted text-muted-foreground",
  medium: "bg-warning/20 text-warning",
  high: "bg-destructive/20 text-destructive",
};

const statusColors = {
  unreviewed: "bg-accent/20 text-accent",
  reviewed: "bg-success/20 text-success",
  snoozed: "bg-muted text-muted-foreground",
  done: "bg-muted text-muted-foreground",
};

const intentIcons: Record<string, string> = {
  learn: "Learn",
  buy: "Buy",
  apply: "Apply",
  remember: "Remember",
  share: "Share",
  research: "Research",
  watch: "Watch",
  read: "Read",
  reference: "Ref",
};

export function CaptureListItem({ item, isSelected, onClick }: CaptureListItemProps) {
  const isExpiringSoon = item.deadline &&
    new Date(item.deadline).getTime() - Date.now() < 3 * 24 * 60 * 60 * 1000;

  return (
  <div
    onClick={onClick}
    className={cn(
      "group flex w-full flex-col gap-2 rounded-lg border border-border bg-card p-4 text-left transition-all cursor-pointer",
      isSelected && "border-primary bg-accent/50",
      "hover:bg-accent/50"
    )}
  >
      {/* Top row: Title and badges */}
      <div className="flex items-start justify-between gap-3">
        <h3 className="text-sm font-medium text-card-foreground line-clamp-2 leading-relaxed flex-1">
          {item.title}
        </h3>
        <div className="flex shrink-0 items-center gap-1.5">
          {/* Ask Gemini Button */}
          <div
            onClick={(e) => {
              e.stopPropagation();
              e.preventDefault();
            }}
            onMouseDown={(e) => {
              e.stopPropagation();
            }}
            onKeyDown={(e) => {
              // Prevent all keyboard events from bubbling to parent button
              e.stopPropagation();
              e.preventDefault();
            }}
            onKeyUp={(e) => {
              // Prevent all keyboard events from bubbling to parent button
              e.stopPropagation();
              e.preventDefault();
            }}
            onKeyPress={(e) => {
              // Prevent all keyboard events from bubbling to parent button
              e.stopPropagation();
              e.preventDefault();
            }}
          >
          </div>
          {/* Status Badge */}
          <Badge variant="outline" className={cn("text-xs", statusColors[item.status])}>
            {item.status}
          </Badge>
        </div>
      </div>


      {/* Summary */}
      {item.summary && (
        <p className="text-xs text-muted-foreground line-clamp-2 leading-relaxed">
          {item.summary}
        </p>
      )}

      {/* Meta row */}
      <div className="flex flex-wrap items-center gap-2 text-xs text-muted-foreground">
        {/* Source */}
        <span className="flex items-center gap-1">
          {item.sourceApp}
        </span>

        <span>•</span>

        {/* Time */}
        <span className="flex items-center gap-1">
          <Clock className="h-3 w-3" aria-hidden="true" />
          {formatRelativeTime(item.createdAt)}
        </span>

        {/* Deadline if exists */}
        {item.deadline && (
          <>
            <span>•</span>
            <span className={cn("flex items-center gap-1", isExpiringSoon && "text-destructive")}>
              <Calendar className="h-3 w-3" aria-hidden="true" />
              Due {new Date(item.deadline).toLocaleDateString()}
            </span>
          </>
        )}

        {/* URL indicator */}
        {item.url && (
          <>
            <span>•</span>
            <ExternalLink className="h-3 w-3" aria-hidden="true" />
          </>
        )}
      </div>

      {/* Bottom row: Tags and indicators */}
      <div className="flex items-center justify-between gap-2">
        <div className="flex flex-wrap items-center gap-1.5">
          {/* Intent */}
          <Badge variant="secondary" className="text-xs">
            {intentIcons[item.intent] || item.intent}
          </Badge>

          {/* Urgency */}
          <Badge variant="outline" className={cn("text-xs gap-1", urgencyColors[item.urgency])}>
            <AlertCircle className="h-2.5 w-2.5" />
            {item.urgency}
          </Badge>

          {/* First 2 tags */}
          {item.tags.slice(0, 2).map((tag) => (
            <Badge key={tag} variant="outline" className="text-xs">
              #{tag}
            </Badge>
          ))}
          {item.tags.length > 2 && (
            <span className="text-xs text-muted-foreground">+{item.tags.length - 2}</span>
          )}
        </div>

        {/* Priority score */}
        <div className="flex items-center gap-1">
          <div
            className={cn(
              "h-1.5 w-8 rounded-full bg-muted overflow-hidden"
            )}
            title={`Priority: ${item.priorityScore}/100`}
          >
            <div
              className={cn(
                "h-full rounded-full",
                item.priorityScore >= 80 ? "bg-destructive" :
                  item.priorityScore >= 60 ? "bg-warning" :
                    "bg-accent"
              )}
              style={{ width: `${item.priorityScore}%` }}
            />
          </div>
          {/* Ask Gemini */}
    <div onClick={(e) => e.stopPropagation()}>
      <AskGeminiButton captureId={item.id} variant="icon" />
    </div>
        </div>
      </div>
    </div>
  );
}

function formatRelativeTime(date: Date): string {
  const now = new Date();
  const diff = now.getTime() - date.getTime();
  const minutes = Math.floor(diff / 60000);
  const hours = Math.floor(minutes / 60);
  const days = Math.floor(hours / 24);

  if (days > 0) return `${days}d ago`;
  if (hours > 0) return `${hours}h ago`;
  if (minutes > 0) return `${minutes}m ago`;
  return "Just now";
}