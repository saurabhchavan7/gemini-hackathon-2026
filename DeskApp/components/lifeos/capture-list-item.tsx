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
  unreviewed: "border-0",
  reviewed: "border-0",
  snoozed: "border-0",
  done: "border-0",
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
  className="group flex w-full flex-col gap-2 rounded-xl p-4 text-left cursor-pointer transition-shadow duration-200 border-l-4"
  style={{
    backgroundColor: 'var(--color-bg-card)',
    boxShadow: '0 1px 2px rgba(0,0,0,0.05)',
    borderLeftColor: item.urgency === 'medium'
      ? 'var(--color-accent-orange)'
      : item.intent === 'research' || item.intent === 'learn'
        ? 'var(--color-accent-blue)'
        : 'var(--color-accent-green)'
  }}
      onMouseEnter={(e) => {
        e.currentTarget.style.boxShadow = '0 4px 12px rgba(0,0,0,0.1)';
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.boxShadow = '0 1px 2px rgba(0,0,0,0.05)';
      }}
    >
      {/* Top row: Title and badges */}
      <div className="flex items-start justify-between gap-3">
<h3 className="text-sm font-bold text-card-foreground line-clamp-2 leading-relaxed flex-1" style={{ fontWeight: 700 }}>          {item.title}
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
          <Badge
            className="text-xs border-0 px-2 py-0.5 rounded-full"
            style={{
              backgroundColor: item.status === 'unreviewed' ? 'var(--color-accent-blue-light)' : 'var(--color-bg-tertiary)',
              color: item.status === 'unreviewed' ? 'var(--color-accent-blue)' : 'var(--color-text-secondary)'
            }}
          >
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
          <Clock className="h-3 w-3" style={{ color: 'var(--color-accent-blue)' }} aria-hidden="true" />
          {formatRelativeTime(item.createdAt)}
        </span>

        {/* Deadline if exists */}
        {item.deadline && (
          <>
            <span>•</span>
            <span className={cn("flex items-center gap-1", isExpiringSoon && "text-destructive")}>
              <Calendar className="h-3 w-3" style={{ color: isExpiringSoon ? 'var(--color-accent-red)' : 'var(--color-accent-green)' }} aria-hidden="true" />
              Due {new Date(item.deadline).toLocaleDateString()}
            </span>
          </>
        )}

        {/* URL indicator */}
        {item.url && (
          <>
            <span>•</span>
            <ExternalLink className="h-3 w-3" style={{ color: 'var(--color-accent-blue)' }} aria-hidden="true" />
          </>
        )}
      </div>

      {/* Bottom row: Tags and indicators */}
      <div className="flex items-center justify-between gap-2">
        <div className="flex flex-wrap items-center gap-1.5">
          {/* Intent */}
          <Badge
            className="text-xs border-0 px-2 py-0.5"
            style={{
              backgroundColor: 'var(--color-bg-tertiary)',
              color: 'var(--color-text-primary)'
            }}
          >
            {intentIcons[item.intent] || item.intent}
          </Badge>

          {/* Urgency */}
          <Badge
            className="text-xs gap-1 border-0 px-2 py-0.5"
            style={{
              backgroundColor: item.urgency === 'medium'
                ? 'var(--color-accent-orange-light)'
                : 'var(--color-accent-green-light)',
              color: item.urgency === 'medium'
                ? 'var(--color-accent-orange)'
                : 'var(--color-accent-green)'
            }}
          >
            <AlertCircle className="h-2.5 w-2.5" />
            {item.urgency}
          </Badge>

          {/* First 2 tags */}
          {item.tags.slice(0, 2).map((tag, idx) => (
            <Badge
              key={tag}
              className="text-xs border-0 px-2 py-0.5"
              style={{
                backgroundColor: idx === 0 ? 'var(--color-accent-green-light)' : 'var(--color-accent-orange-light)',
                color: idx === 0 ? 'var(--color-accent-green)' : 'var(--color-accent-orange)'
              }}
            >
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
            className="h-1.5 w-12 rounded-full overflow-hidden"
            style={{
              backgroundColor: 'var(--color-bg-tertiary)'

            }}
            title={`Priority: ${item.priorityScore}/100`}
          >
            <div
              className="h-full rounded-full"
              style={{
                width: `${item.priorityScore}%`,
                backgroundColor: item.priorityScore >= 80
                  ? 'var(--color-accent-red)'
                  : item.priorityScore >= 60
                    ? 'var(--color-accent-orange)'
                    : 'var(--color-accent-green)'
              }}
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