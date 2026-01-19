"use client";

import React from "react"

import { useState, useEffect } from "react";
import {
  Bell,
  Calendar,
  Link2,
  Lightbulb,
  Clock,
  Eye,
  AlarmClock,
  X,
  CheckCircle,
} from "lucide-react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { listNotifications, markNotificationRead } from "@/lib/api";
import { cn } from "@/lib/utils";
import type { NotificationItem } from "@/types/lifeos";

const typeIcons: Record<string, React.ComponentType<{ className?: string }>> = {
  deadline: Calendar,
  connection: Link2,
  suggestion: Lightbulb,
  reminder: Clock,
  digest: Bell,
};

const typeColors: Record<string, string> = {
  deadline: "bg-destructive/10 text-destructive",
  connection: "bg-accent/10 text-accent",
  suggestion: "bg-warning/10 text-warning",
  reminder: "bg-info/10 text-info",
  digest: "bg-muted text-muted-foreground",
};

export default function NotificationsPage() {
  const [notifications, setNotifications] = useState<NotificationItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    async function loadData() {
      setIsLoading(true);
      const data = await listNotifications();
      setNotifications(data);
      setIsLoading(false);
    }
    loadData();
  }, []);

  const handleAction = async (notification: NotificationItem, action: "review" | "remind" | "dismiss") => {
    // Mark as read
    await markNotificationRead(notification.id);
    
    // Update local state
    setNotifications((prev) =>
      prev.map((n) => (n.id === notification.id ? { ...n, read: true } : n))
    );

    // Simulate action feedback
    if (action === "dismiss") {
      setNotifications((prev) => prev.filter((n) => n.id !== notification.id));
    }
  };

  const unreadCount = notifications.filter((n) => !n.read).length;

  if (isLoading) {
    return (
      <div className="flex h-full items-center justify-center">
        <div className="flex flex-col items-center gap-3 text-muted-foreground">
          <div className="h-8 w-8 animate-spin rounded-full border-2 border-muted border-t-accent" />
          <span className="text-sm">Loading notifications...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="flex h-full flex-col">
      {/* Header */}
      <div className="border-b border-border px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Bell className="h-5 w-5 text-muted-foreground" />
            <h1 className="text-xl font-semibold text-foreground">Notifications</h1>
            {unreadCount > 0 && (
              <Badge variant="default">{unreadCount} new</Badge>
            )}
          </div>
          {unreadCount > 0 && (
            <Button
              variant="ghost"
              size="sm"
              onClick={() => {
                notifications.forEach((n) => markNotificationRead(n.id));
                setNotifications((prev) => prev.map((n) => ({ ...n, read: true })));
              }}
              className="text-muted-foreground"
            >
              <CheckCircle className="h-4 w-4 mr-2" />
              Mark all as read
            </Button>
          )}
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-auto p-6">
        {notifications.length === 0 ? (
          <div className="flex h-64 flex-col items-center justify-center text-center">
            <Bell className="h-12 w-12 text-muted-foreground/50" />
            <h3 className="mt-4 text-lg font-medium text-foreground">No notifications</h3>
            <p className="mt-1 text-sm text-muted-foreground">
              {"You're all caught up!"}
            </p>
          </div>
        ) : (
          <div className="space-y-3 max-w-2xl">
            {notifications.map((notification) => {
              const Icon = typeIcons[notification.type] || Bell;
              const colorClass = typeColors[notification.type] || typeColors.digest;

              return (
                <Card
                  key={notification.id}
                  className={cn(
                    "bg-card p-4 transition-all",
                    !notification.read && "ring-1 ring-accent/50"
                  )}
                >
                  <div className="flex gap-4">
                    {/* Icon */}
                    <div className={cn("h-10 w-10 shrink-0 rounded-lg flex items-center justify-center", colorClass)}>
                      <Icon className="h-5 w-5" />
                    </div>

                    {/* Content */}
                    <div className="flex-1 min-w-0">
                      <div className="flex items-start justify-between gap-2">
                        <div>
                          <h3 className="text-sm font-medium text-card-foreground">
                            {notification.title}
                          </h3>
                          <p className="mt-1 text-sm text-muted-foreground">
                            {notification.message}
                          </p>
                        </div>
                        {!notification.read && (
                          <div className="h-2 w-2 shrink-0 rounded-full bg-accent mt-1.5" />
                        )}
                      </div>

                      {/* Actions */}
                      <div className="mt-3 flex items-center gap-2">
                        {notification.actionType === "review" && (
                          <Button
                            size="sm"
                            onClick={() => handleAction(notification, "review")}
                            className="gap-2"
                          >
                            <Eye className="h-3 w-3" />
                            {notification.actionLabel || "Review Now"}
                          </Button>
                        )}
                        {notification.actionType === "remind" && (
                          <Button
                            size="sm"
                            variant="secondary"
                            onClick={() => handleAction(notification, "remind")}
                            className="gap-2"
                          >
                            <AlarmClock className="h-3 w-3" />
                            {notification.actionLabel || "Remind Later"}
                          </Button>
                        )}
                        <Button
                          size="sm"
                          variant="ghost"
                          onClick={() => handleAction(notification, "dismiss")}
                          className="gap-2 text-muted-foreground"
                        >
                          <X className="h-3 w-3" />
                          Dismiss
                        </Button>
                        <span className="ml-auto text-xs text-muted-foreground">
                          {formatRelativeTime(notification.createdAt)}
                        </span>
                      </div>
                    </div>
                  </div>
                </Card>
              );
            })}
          </div>
        )}
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
