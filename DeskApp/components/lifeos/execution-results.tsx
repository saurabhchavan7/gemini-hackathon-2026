"use client";

import type { ExecutionActionV2 } from "@/types/lifeos";
import { useState } from "react";
import {
  CheckCircle2,
  XCircle,
  Clock,
  Calendar,
  CheckSquare,
  StickyNote,
  Users,
  ExternalLink,
  ChevronDown,
  ChevronUp,
  AlertCircle,
  Link as LinkIcon,
  MapPin
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

interface ExecutionResultsProps {
  actions: ExecutionActionV2[];
  successCount: number;
  failedCount: number;
  skippedCount: number;
}

const INTENT_CONFIG: Record<string, { icon: any; label: string; color: string }> = {
  create_task: {
    icon: CheckSquare,
    label: "Created Task",
    color: "text-blue-600",
  },
  schedule_event: {
    icon: Calendar,
    label: "Created Event",
    color: "text-purple-600",
  },
  save_note: {
    icon: StickyNote,
    label: "Saved Note",
    color: "text-green-600",
  },
  send_email: {
    icon: LinkIcon,
    label: "Sent Email",
    color: "text-orange-600",
  },
};

function buildGoogleTaskLink(taskId: string): string {
  // Google Tasks web URL format
  return `https://tasks.google.com/task/${taskId}`;
}

function ActionCard({ action }: { action: ExecutionActionV2 }) {
  const isCalendarEvent = action.type === 'calendar_event';
  const isTask = action.type === 'task';
  const isEmail = action.type === 'email';

  const Icon = isCalendarEvent ? Calendar : isTask ? CheckSquare : LinkIcon;
  const label = isCalendarEvent ? 'Created Calendar Event' : isTask ? 'Created Task' : 'Action Taken';
  const statusColor = action.status === 'synced' || action.status === 'success' ? 'green' : 'red';

  return (
    <div className="rounded-lg border p-4 shadow-sm" style={{
      backgroundColor: 'var(--color-bg-card)',
      borderColor: 'var(--color-border-light)'
    }}>
      <div className="flex items-start gap-3">
        {/* Status Icon */}
        <div className="flex-shrink-0 mt-0.5">
          <CheckCircle2 className="h-5 w-5" style={{ color: 'var(--color-accent-green)' }} />
        </div>

        {/* Action Icon */}
        <div className="flex-shrink-0 mt-0.5">
          <Icon className="h-5 w-5" style={{ color: 'var(--color-accent-blue)' }} />
        </div>

        {/* Content */}
        <div className="flex-1 min-w-0">
          {/* Title */}
          <div className="flex items-start justify-between gap-2 mb-1">
            <h4 className="font-medium text-sm" style={{ color: 'var(--color-text-primary)' }}>
              {label}
            </h4>
            <Badge
              className="text-xs shrink-0 border-0 px-2 py-0.5"
              style={{
                backgroundColor: 'var(--color-accent-green-light)',
                color: 'var(--color-accent-green)'
              }}
            >
              {action.status}
            </Badge>
          </div>

          {/* Title/Summary */}
          <p className="text-sm mb-2" style={{ color: 'var(--color-text-primary)', fontWeight: 500 }}>
            {action.title || action.summary}
          </p>

          {/* Metadata */}
          <div className="space-y-1.5 text-xs" style={{ color: 'var(--color-text-secondary)' }}>
            {/* Calendar Event Time */}
            {isCalendarEvent && action.start_time && action.end_time && (
              <div className="flex items-center gap-1.5">
                <Clock className="h-3 w-3" />
                <span>
                  {new Date(action.start_time).toLocaleString('en-US', {
                    month: 'short',
                    day: 'numeric',
                    hour: 'numeric',
                    minute: '2-digit'
                  })}
                  {' - '}
                  {new Date(action.end_time).toLocaleTimeString('en-US', {
                    hour: 'numeric',
                    minute: '2-digit'
                  })}
                </span>
              </div>
            )}

            {/* Task Due Date */}
            {isTask && action.due_date && (
              <div className="flex items-center gap-1.5">
                <Calendar className="h-3 w-3" />
                <span>
                  Due: {new Date(action.due_date).toLocaleDateString('en-US', {
                    month: 'short',
                    day: 'numeric',
                    year: 'numeric'
                  })}
                </span>
              </div>
            )}

            {/* Attendees */}
            {action.attendees && action.attendees.length > 0 && (
              <div className="flex items-center gap-1.5">
                <Users className="h-3 w-3" />
                <span>{action.attendees.length} attendee{action.attendees.length !== 1 ? 's' : ''}</span>
              </div>
            )}

            {/* Location */}
            {action.location && (
              <div className="flex items-center gap-1.5">
                <MapPin className="h-3 w-3" />
                <span>{action.location}</span>
              </div>
            )}
          </div>

          {/* Primary Action Link */}
          {action.google_calendar_link && (
            <a
              href={action.google_calendar_link}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1 mt-2 text-xs font-medium hover:underline"
              style={{ color: 'var(--color-accent-blue)' }}
            >
              Open in Google Calendar
              <ExternalLink className="h-3 w-3" />
            </a>
          )}
        </div>
      </div>
    </div>
  );
}

export function ExecutionResults({
  actions,
  successCount,
  failedCount,
  skippedCount,
}: ExecutionResultsProps) {
  const [isExpanded, setIsExpanded] = useState(true);

  if (actions.length === 0) {
    return null;
  }

  const totalCount = actions.length;
  const hasFailures = failedCount > 0;

  return (
    <div className="border rounded-lg overflow-hidden shadow-sm" style={{
      backgroundColor: 'var(--color-bg-card)',
      borderColor: 'var(--color-border-light)'
    }}>{/* Header */}
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className={cn(
          "w-full flex items-center justify-between p-4 transition-colors",
          "hover:bg-muted/50 focus:outline-none focus:ring-2 focus:ring-ring focus:ring-inset",
          hasFailures ? "bg-red-50/30 dark:bg-red-950/10" : "bg-green-50/30 dark:bg-green-950/10"
        )}
      >
        <div className="flex items-center gap-3">
          <CheckSquare className={cn(
            "h-5 w-5",
            hasFailures ? "text-orange-600" : "text-green-600"
          )} />
          <div className="text-left">
            <h3 className="text-sm font-semibold text-foreground">
              Actions Taken
            </h3>
            <div className="flex items-center gap-2 mt-0.5">
              {successCount > 0 && (
                <span className="text-xs text-green-600 dark:text-green-400 font-medium">
                  {successCount} successful
                </span>
              )}
              {failedCount > 0 && (
                <span className="text-xs text-red-600 dark:text-red-400 font-medium">
                  {failedCount} failed
                </span>
              )}
              {skippedCount > 0 && (
                <span className="text-xs text-muted-foreground">
                  {skippedCount} skipped
                </span>
              )}
            </div>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <Badge variant="outline" className="text-xs">
            {totalCount} total
          </Badge>
          {isExpanded ? (
            <ChevronUp className="h-4 w-4 text-muted-foreground" />
          ) : (
            <ChevronDown className="h-4 w-4 text-muted-foreground" />
          )}
        </div>
      </button>

      {/* Content */}
      {isExpanded && (
        <div className="p-4 pt-0 space-y-3">
          {actions.map((action, idx) => (
            <ActionCard key={idx} action={action} />
          ))}
        </div>
      )}
    </div>
  );
}
