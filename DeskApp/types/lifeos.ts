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

// ============================================
// ENHANCED CAPTURE TYPES (V2 API)
// ============================================

export interface InputData {
  text_note?: string;
  screenshot_url?: string;
  screenshot_signed_url?: string;
  screenshot_path?: string;
  audio_url?: string;
  audio_signed_url?: string;
  audio_path?: string;
  audio_transcript?: string;
  audio_duration_seconds?: number;
  full_transcript?: string;
  context?: any;
}

export interface ClassificationData {
  domain?: string;
  primary_intent?: string;
  intent?: string;
  context_type?: string;
  overall_summary?: string;
  total_actions?: number;
  actions?: any[];
  urgency?: string;
  deadline?: string;
  domain_confidence?: number;
  processing_time_ms?: number;
}

export interface ResearchData {
  has_data?: boolean;
  triggered?: boolean;
  completed_at?: string | null;
  query?: string;
  research_type?: string;
  results?: string;
  summary?: string;
  sources_count?: number;
  sources?: any[];
  processing_time_ms?: number;
  started_at?: string | null;
  trigger_reason?: string | null;
}

export interface ResourcesData {
  has_data?: boolean;
  triggered?: boolean;
  needs_resources?: boolean;
  ai_reasoning?: string;
  resources?: Array<{
    title: string;
    url: string;
    type: string;
    description: string;
    source: string;
    relevance_score?: number;
    authority_score?: number;
    verified?: boolean;
    thumbnail_url?: string;
  }>;
  resources_count?: number;
  learning_path?: string;
  summary?: string;
  completed_at?: string | null;
  processing_time_ms?: number;
}

export interface ExecutionActionV2 {
  type?: string;
  intent?: string;
  summary?: string;
  status?: string;
  title?: string;
  notes?: string;
  due_date?: string;
  start_time?: string;
  end_time?: string;
  location?: string;
  attendees?: string[];
  google_task_id?: string;
  google_calendar_id?: string;
  google_calendar_link?: string;
  firestore_doc_id?: string;
  created_at?: string;
  tool_used?: string;
  tool_params?: any;
  result_data?: any;
  error_message?: string;
  invites_sent_to?: string[];
  created_task_id?: string;
  created_event_id?: string;
  created_note_id?: string;
}

export interface ExecutionData {
  has_data?: boolean;
  actions_executed?: ExecutionActionV2[];
  total_actions?: number;
  successful?: number;
  failed?: number;
  skipped?: number;
  completed_at?: string | null;
  processing_time_ms?: number;
}

export interface PerceptionData {
  ocr_text?: string;
  audio_transcript?: string;
  visual_description?: string;
  completed_at?: string | null;
  processing_time_ms?: number;
  cache_key?: string | null;
}

export interface ProactiveData {
  triggered?: boolean;  // ADD THIS
  completed_at?: string | null;
  tips?: string[];
  suggestions?: string[];  // ADD THIS
  intents_analyzed?: string[];
  domain_analyzed?: string;
  trigger_reason?: string | null;
  processing_time_ms?: number;
}

export interface TimelineData {
  capture_received?: string;
  perception_started?: string;
  perception_completed?: string;
  classification_started?: string;
  classification_completed?: string;
  research_started?: string;
  research_completed?: string;
  resources_started?: string;
  resources_completed?: string;
  execution_started?: string;
  execution_completed?: string;
  proactive_started?: string;
  proactive_completed?: string;
  firestore_save_started?: string;
  firestore_save_completed?: string;
}

export interface AttachedFile {
  filename: string;
  name?: string;  // ADD THIS (alias for filename)
  filepath: string;
  file_type: string;
  file_size?: number;
  size_bytes?: number;  // ADD THIS (alias for file_size)
  public_url?: string;
  url?: string;  // ADD THIS (alias for public_url)
  signed_url?: string;  // ADD THIS
}

export interface EnhancedCaptureDetails {
  id: string;
  user_id?: string;
  memory_id?: string;
  created_at?: string;
  updated_at?: string;
  status?: string;
  capture_type?: string;
  
  // Input data
  input?: InputData;
  
  // Classification
  classification?: ClassificationData;
  
  // Agent results
  research?: ResearchData;
  resources?: ResourcesData;
  execution?: ExecutionData;
  perception?: PerceptionData;
  proactive?: ProactiveData;
  
  // Timeline
  timeline?: TimelineData;
  
  // Files
  attached_files?: AttachedFile[];
  
  // Errors
  errors?: any[];
}