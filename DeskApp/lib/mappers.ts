// lib/mappers.ts
import type { CaptureItem, Intent, CaptureStatus } from "@/types/lifeos";

/**
 * Maps backend memory data to frontend CaptureItem format
 */
export function mapMemoryToCaptureItem(memory: any): CaptureItem {
  return {
    id: memory.id,
    title: memory.title || 'Untitled',
    createdAt: memory.created_at ? new Date(memory.created_at) : new Date(),
    sourceApp: memory.source_app || 'Unknown',
    windowTitle: memory.window_title || '',
    url: memory.url || undefined,
    previewUrl: memory.screenshot_url || '/placeholder.svg',
    summary: memory.one_line_summary || '',
    extractedText: memory.full_transcript || '',
    entities: [],
    tags: memory.tags || [],
    intent: mapIntent(memory.intent),
    intentConfidence: 0.9,
    urgency: mapPriorityToUrgency(memory.priority),
    priorityScore: mapPriorityToScore(memory.priority),
    status: mapStatus(memory.status),
    deadline: memory.deadline ? new Date(memory.deadline) : undefined,
  };
}

/**
 * Map backend intent to frontend Intent type
 */
function mapIntent(intent: string = 'remember'): Intent {
  const validIntents: Intent[] = ['learn', 'buy', 'apply', 'remember', 'share', 'research', 'watch', 'read', 'reference'];
  return validIntents.includes(intent as Intent) ? (intent as Intent) : 'remember';
}

/**
 * Map priority (1-5) to urgency level
 */
function mapPriorityToUrgency(priority: number = 3): 'low' | 'medium' | 'high' {
  if (priority >= 4) return 'high';
  if (priority >= 3) return 'medium';
  return 'low';
}

/**
 * Map priority (1-5) to score (0-100)
 */
function mapPriorityToScore(priority: number = 3): number {
  return priority * 20;
}

/**
 * Map backend status to frontend CaptureStatus
 */
function mapStatus(status: string = 'active'): CaptureStatus {
  const statusMap: Record<string, CaptureStatus> = {
    'active': 'unreviewed',
    'reviewed': 'reviewed',
    'snoozed': 'snoozed',
    'archived': 'done',
    'deleted': 'done',
  };
  
  return statusMap[status] || 'unreviewed';
}