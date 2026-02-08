"use client";

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
  Link as LinkIcon
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

interface ExecutionAction {
  intent: string;
  summary: string;
  status: string;
  tool_used?: string;
  tool_params?: {
    title?: string;
    notes?: string;
    due_date?: string;
    start_time?: string;
    end_time?: string;
    attendees?: string[];
    [key: string]: any;
  };
  result_data?: any;
  google_calendar_link?: string;
  google_task_id?: string;
  created_task_id?: string;
  created_event_id?: string;
  created_note_id?: string;
  invites_sent_to?: string[];
  error_message?: string;
}

interface ExecutionResultsProps {
  actions: ExecutionAction[];
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

function ActionCard({ action }: { action: ExecutionAction }) {
  const config = INTENT_CONFIG[action.intent] || {
    icon: CheckCircle2,
    label: action.intent.replace(/_/g, ' '),
    color: "text-gray-600",
  };
  
  const Icon = config.icon;
  const isSuccess = action.status === "success";
  const isFailed = action.status === "error";
  const isSkipped = action.status === "skipped";
  
  // Determine primary link
  const primaryLink = action.google_calendar_link || 
    (action.google_task_id ? buildGoogleTaskLink(action.google_task_id) : null);
  
  // Extract details from tool_params
  const dueDate = action.tool_params?.due_date;
  const startTime = action.tool_params?.start_time;
  const endTime = action.tool_params?.end_time;
  const attendees = action.invites_sent_to || action.tool_params?.attendees || [];
  
  return (
    <div className={cn(
      "rounded-lg border p-4 transition-all",
      isSuccess && "bg-green-50/50 border-green-200 dark:bg-green-950/20 dark:border-green-800",
      isFailed && "bg-red-50/50 border-red-200 dark:bg-red-950/20 dark:border-red-800",
      isSkipped && "bg-gray-50/50 border-gray-200 dark:bg-gray-900/20 dark:border-gray-700"
    )}>
      <div className="flex items-start gap-3">
        {/* Status Icon */}
        <div className="flex-shrink-0 mt-0.5">
          {isSuccess && <CheckCircle2 className="h-5 w-5 text-green-600" />}
          {isFailed && <XCircle className="h-5 w-5 text-red-600" />}
          {isSkipped && <AlertCircle className="h-5 w-5 text-gray-400" />}
        </div>
        
        {/* Action Icon */}
        <div className="flex-shrink-0 mt-0.5">
          <Icon className={cn("h-5 w-5", config.color)} />
        </div>
        
        {/* Content */}
        <div className="flex-1 min-w-0">
          {/* Title */}
          <div className="flex items-start justify-between gap-2 mb-1">
            <h4 className="font-medium text-sm text-foreground">
              {config.label}
            </h4>
            <Badge 
              variant={isSuccess ? "default" : isFailed ? "destructive" : "secondary"}
              className="text-xs shrink-0"
            >
              {action.status}
            </Badge>
          </div>
          
          {/* Summary */}
          <p className="text-sm text-muted-foreground mb-2">
            {action.summary}
          </p>
          
          {/* Metadata */}
          <div className="space-y-1.5 text-xs text-muted-foreground">
            {/* Due Date / Event Time */}
            {dueDate && (
              <div className="flex items-center gap-1.5">
                <Calendar className="h-3 w-3" />
                <span>
                  Due: {new Date(dueDate).toLocaleDateString('en-US', {
                    month: 'short',
                    day: 'numeric',
                    year: 'numeric'
                  })}
                </span>
              </div>
            )}
            
            {startTime && endTime && (
              <div className="flex items-center gap-1.5">
                <Clock className="h-3 w-3" />
                <span>
                  {new Date(startTime).toLocaleString('en-US', {
                    month: 'short',
                    day: 'numeric',
                    hour: 'numeric',
                    minute: '2-digit'
                  })}
                  {' - '}
                  {new Date(endTime).toLocaleTimeString('en-US', {
                    hour: 'numeric',
                    minute: '2-digit'
                  })}
                </span>
              </div>
            )}
            
            {/* Attendees */}
            {attendees.length > 0 && (
              <div className="flex items-center gap-1.5">
                <Users className="h-3 w-3" />
                <span>{attendees.length} attendee{attendees.length !== 1 ? 's' : ''} invited</span>
              </div>
            )}
            
            {/* Error Message */}
            {isFailed && action.error_message && (
              <div className="flex items-start gap-1.5 text-red-600 dark:text-red-400 mt-2">
                <AlertCircle className="h-3 w-3 mt-0.5 flex-shrink-0" />
                <span className="text-xs">{action.error_message}</span>
              </div>
            )}
          </div>
          
          {/* Primary Action Link */}
          {isSuccess && primaryLink && (
            <Button
              variant="link"
              size="sm"
              asChild
              className="h-auto p-0 mt-2 text-xs font-medium"
            >
              <a
                href={primaryLink}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-1"
              >
                {action.google_calendar_link && "Open in Google Calendar"}
                {action.google_task_id && "Open in Google Tasks"}
                {!action.google_calendar_link && !action.google_task_id && "View Item"}
                <ExternalLink className="h-3 w-3" />
              </a>
            </Button>
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
    <div className="border border-border rounded-lg overflow-hidden">
      {/* Header */}
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
