"use client";

import { useState, ReactNode } from "react";
import { ChevronDown, ChevronUp, LucideIcon } from "lucide-react";
import { cn } from "@/lib/utils";
import { Badge } from "@/components/ui/badge";

interface CollapsibleSectionProps {
  title: string;
  subtitle?: string;
  icon?: LucideIcon;
  badge?: string | number;
  badgeVariant?: "default" | "secondary" | "destructive" | "outline";
  defaultOpen?: boolean;
  children: ReactNode;
  className?: string;
  headerClassName?: string;
  isEmpty?: boolean;
  emptyMessage?: string;
}

export function CollapsibleSection({
  title,
  subtitle,
  icon: Icon,
  badge,
  badgeVariant = "outline",
  defaultOpen = false,
  children,
  className,
  headerClassName,
  isEmpty = false,
  emptyMessage = "No data available",
}: CollapsibleSectionProps) {
  const [isExpanded, setIsExpanded] = useState(defaultOpen);
  
  if (isEmpty) {
    return null;
  }
  
  return (
    <div className={cn("border border-border rounded-lg overflow-hidden", className)}>
      {/* Header */}
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className={cn(
          "w-full flex items-center justify-between p-4 transition-colors",
          "hover:bg-muted/50 focus:outline-none focus:ring-2 focus:ring-ring focus:ring-inset",
          headerClassName
        )}
      >
        <div className="flex items-center gap-3">
          {Icon && <Icon className="h-5 w-5 text-muted-foreground flex-shrink-0" />}
          <div className="text-left">
            <h3 className="text-sm font-semibold text-foreground">
              {title}
            </h3>
            {subtitle && (
              <p className="text-xs text-muted-foreground mt-0.5">
                {subtitle}
              </p>
            )}
          </div>
        </div>
        
        <div className="flex items-center gap-2">
          {badge !== undefined && (
            <Badge variant={badgeVariant} className="text-xs">
              {badge}
            </Badge>
          )}
          {isExpanded ? (
            <ChevronUp className="h-4 w-4 text-muted-foreground" />
          ) : (
            <ChevronDown className="h-4 w-4 text-muted-foreground" />
          )}
        </div>
      </button>
      
      {/* Content */}
      {isExpanded && (
        <div className="p-4 pt-0">
          {children}
        </div>
      )}
    </div>
  );
}
