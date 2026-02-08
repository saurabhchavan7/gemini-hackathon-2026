"use client";

import { Calendar, Clock, AlertCircle } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

interface HeroSectionProps {
  title: string;
  summary?: string;
  domain: string;
  intent: string;
  urgency: string;
  deadline?: string | Date;
  domainConfidence?: number;
}

const DOMAIN_ICONS: Record<string, string> = {
  work_career: "💼",
  education_learning: "📚",
  money_finance: "💰",
  home_daily_life: "🏠",
  health_wellbeing: "❤️",
  family_relationships: "👨‍👩‍👧‍👦",
  travel_movement: "✈️",
  shopping_consumption: "🛒",
  entertainment_leisure: "🎮",
  social_community: "👥",
  admin_documents: "📋",
  ideas_thoughts: "💡",
};

const DOMAIN_LABELS: Record<string, string> = {
  work_career: "Work & Career",
  education_learning: "Education",
  money_finance: "Finance",
  home_daily_life: "Daily Life",
  health_wellbeing: "Health",
  family_relationships: "Family",
  travel_movement: "Travel",
  shopping_consumption: "Shopping",
  entertainment_leisure: "Entertainment",
  social_community: "Social",
  admin_documents: "Documents",
  ideas_thoughts: "Ideas",
};

const INTENT_COLORS: Record<string, string> = {
  act: "bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200",
  schedule: "bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200",
  pay: "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200",
  buy: "bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-200",
  remember: "bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-200",
  learn: "bg-cyan-100 text-cyan-800 dark:bg-cyan-900 dark:text-cyan-200",
  research: "bg-indigo-100 text-indigo-800 dark:bg-indigo-900 dark:text-indigo-200",
  watch: "bg-pink-100 text-pink-800 dark:bg-pink-900 dark:text-pink-200",
  read: "bg-teal-100 text-teal-800 dark:bg-teal-900 dark:text-teal-200",
  follow_up: "bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200",
};

const URGENCY_COLORS: Record<string, string> = {
  critical: "bg-red-100 text-red-800 border-red-300 dark:bg-red-900 dark:text-red-200",
  high: "bg-orange-100 text-orange-800 border-orange-300 dark:bg-orange-900 dark:text-orange-200",
  medium: "bg-yellow-100 text-yellow-800 border-yellow-300 dark:bg-yellow-900 dark:text-yellow-200",
  low: "bg-gray-100 text-gray-600 border-gray-300 dark:bg-gray-800 dark:text-gray-300",
};

function getTimeUntil(deadline: Date): { text: string; urgent: boolean } {
  const now = new Date();
  const diff = deadline.getTime() - now.getTime();
  
  if (diff < 0) {
    return { text: "Overdue", urgent: true };
  }
  
  const hours = Math.floor(diff / (1000 * 60 * 60));
  const days = Math.floor(hours / 24);
  
  if (hours < 24) {
    return { text: `in ${hours} hour${hours !== 1 ? 's' : ''}`, urgent: true };
  } else if (days === 1) {
    return { text: "tomorrow", urgent: true };
  } else if (days < 7) {
    return { text: `in ${days} days`, urgent: days <= 3 };
  } else if (days < 30) {
    const weeks = Math.floor(days / 7);
    return { text: `in ${weeks} week${weeks !== 1 ? 's' : ''}`, urgent: false };
  } else {
    const months = Math.floor(days / 30);
    return { text: `in ${months} month${months !== 1 ? 's' : ''}`, urgent: false };
  }
}

export function HeroSection({
  title,
  summary,
  domain,
  intent,
  urgency,
  deadline,
  domainConfidence,
}: HeroSectionProps) {
  const domainIcon = DOMAIN_ICONS[domain] || "📁";
  const domainLabel = DOMAIN_LABELS[domain] || domain;
  
  const deadlineDate = deadline ? (deadline instanceof Date ? deadline : new Date(deadline)) : null;
  const timeUntil = deadlineDate ? getTimeUntil(deadlineDate) : null;
  
  return (
    <div className="bg-gradient-to-br from-muted/40 to-muted/20 rounded-xl p-5 border border-border/50">
      {/* Domain & Intent Badges */}
      <div className="flex flex-wrap gap-2 mb-3">
        <Badge 
          variant="outline" 
          className="text-xs font-medium bg-background/50 backdrop-blur-sm"
        >
          <span className="mr-1.5">{domainIcon}</span>
          {domainLabel}
          {domainConfidence && domainConfidence < 0.95 && (
            <span className="ml-1.5 text-muted-foreground">
              ({Math.round(domainConfidence * 100)}%)
            </span>
          )}
        </Badge>
        
        <Badge 
          className={cn(
            "text-xs font-medium",
            INTENT_COLORS[intent] || "bg-muted text-foreground"
          )}
        >
          {intent.replace(/_/g, ' ')}
        </Badge>
        
        <Badge 
          variant="outline"
          className={cn(
            "text-xs font-medium",
            URGENCY_COLORS[urgency] || "bg-muted"
          )}
        >
          <AlertCircle className="mr-1 h-3 w-3" />
          {urgency}
        </Badge>
      </div>
      
      {/* Title */}
      <h2 className="text-xl font-semibold text-foreground leading-tight mb-2">
        {title}
      </h2>
      
      {/* Summary */}
      {summary && (
        <p className="text-sm text-muted-foreground leading-relaxed mb-3">
          {summary}
        </p>
      )}
      
      {/* Deadline - Prominent Display */}
      {deadlineDate && timeUntil && (
        <div className={cn(
          "flex items-center gap-2 px-3 py-2 rounded-lg border",
          timeUntil.urgent 
            ? "bg-orange-50 border-orange-200 dark:bg-orange-950 dark:border-orange-800" 
            : "bg-blue-50 border-blue-200 dark:bg-blue-950 dark:border-blue-800"
        )}>
          <Calendar className={cn(
            "h-4 w-4",
            timeUntil.urgent ? "text-orange-600" : "text-blue-600"
          )} />
          <div className="flex-1">
            <div className="flex items-baseline gap-2">
              <span className={cn(
                "text-sm font-semibold",
                timeUntil.urgent ? "text-orange-900 dark:text-orange-100" : "text-blue-900 dark:text-blue-100"
              )}>
                {deadlineDate.toLocaleDateString('en-US', { 
                  weekday: 'short',
                  month: 'short', 
                  day: 'numeric',
                  year: deadlineDate.getFullYear() !== new Date().getFullYear() ? 'numeric' : undefined
                })}
              </span>
              {deadlineDate.getHours() !== 0 && (
                <span className={cn(
                  "text-xs",
                  timeUntil.urgent ? "text-orange-700 dark:text-orange-300" : "text-blue-700 dark:text-blue-300"
                )}>
                  {deadlineDate.toLocaleTimeString('en-US', { 
                    hour: 'numeric',
                    minute: '2-digit'
                  })}
                </span>
              )}
            </div>
            <div className="flex items-center gap-1.5 mt-0.5">
              <Clock className={cn(
                "h-3 w-3",
                timeUntil.urgent ? "text-orange-500" : "text-blue-500"
              )} />
              <span className={cn(
                "text-xs font-medium",
                timeUntil.urgent ? "text-orange-700 dark:text-orange-300" : "text-blue-700 dark:text-blue-300"
              )}>
                {timeUntil.text}
              </span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
