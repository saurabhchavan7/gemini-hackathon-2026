// Core Types for LifeOS

export type Intent =
  | "learn"
  | "buy"
  | "apply"
  | "remember"
  | "share"
  | "research"
  | "watch"
  | "read"
  | "reference";

export type Urgency = "low" | "medium" | "high";

export type CaptureStatus = "unreviewed" | "reviewed" | "snoozed" | "done";

export interface Entity {
  type: "person" | "company" | "date" | "price" | "deadline";
  value: string;
  confidence?: number;
}

export interface CaptureItem {
  id: string;
  title: string;
  createdAt: Date;
  sourceApp: string;
  windowTitle: string;
  url?: string;
  previewUrl: string;
  summary?: string;
  extractedText?: string;
  entities?: Entity[];
  tags: string[];
  intent: Intent;
  intentConfidence: number;
  urgency: Urgency;
  deadline?: Date;
  priorityScore: number;
  status: CaptureStatus;
}

export interface ThemeCluster {
  id: string;
  name: string;
  description: string;
  captureIds: string[];
  createdAt: Date;
  updatedAt: Date;
  color: string;
}

export interface ConnectionEdge {
  id: string;
  sourceId: string;
  targetId: string;
  relationshipType: string;
  strength: number;
  discoveredAt: Date;
}

export interface NotificationItem {
  id: string;
  type: "deadline" | "connection" | "digest" | "suggestion" | "reminder";
  title: string;
  message: string;
  relatedCaptureId?: string;
  createdAt: Date;
  read: boolean;
  actionLabel?: string;
  actionType?: "review" | "remind" | "dismiss";
}

export interface DigestSection {
  title: string;
  items: string[];
}

export interface DigestReport {
  id: string;
  weekStart: Date;
  weekEnd: Date;
  summary: string;
  themes: ThemeCluster[];
  missedConnections: ConnectionEdge[];
  expiringItems: CaptureItem[];
  suggestedActions: string[];
  createdAt: Date;
}

export interface SmartCollection {
  id: string;
  name: string;
  description: string;
  icon: string;
  filter: {
    tags?: string[];
    intents?: Intent[];
    urgency?: Urgency[];
    status?: CaptureStatus[];
    dateRange?: { start: Date; end: Date };
  };
  captureIds: string[];
  order: number;
}

export interface UserSettings {
  hotkey: string;
  quietHoursStart: string;
  quietHoursEnd: string;
  dndEnabled: boolean;
  notificationCap: number;
  captureSources: {
    browser: boolean;
    slack: boolean;
    email: boolean;
    documents: boolean;
    screenshots: boolean;
  };
  localFirst: boolean;
  accessibilityReducedMotion: boolean;
  accessibilityHighContrast: boolean;
}
