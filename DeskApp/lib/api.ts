'use client';

import type {
  CaptureItem,
  ThemeCluster,
  ConnectionEdge,
  NotificationItem,
  DigestReport,
  SmartCollection,
  UserSettings,
  CaptureStatus,
} from "@/types/lifeos";
import { getInbox, getCaptureById , getCaptureByIdV2} from './api-client';
import { mapMemoryToCaptureItem } from './mappers';


// Mock Data
const mockCaptures: CaptureItem[] = [
  {
    id: "1",
    title: "React Server Components Deep Dive",
    createdAt: new Date("2026-01-15T10:30:00"),
    sourceApp: "Chrome",
    windowTitle: "React Documentation",
    url: "https://react.dev/reference/rsc/server-components",
    previewUrl: "/placeholder.svg",
    summary: "Comprehensive guide to React Server Components architecture and best practices",
    extractedText: "Server Components allow you to write UI that can be rendered and optionally cached on the server...",
    entities: [
      { type: "company", value: "Meta", confidence: 0.95 },
      { type: "date", value: "2026-01-15", confidence: 1 },
    ],
    tags: ["react", "frontend", "architecture"],
    intent: "learn",
    intentConfidence: 0.92,
    urgency: "medium",
    priorityScore: 78,
    status: "unreviewed",
  },
  {
    id: "2",
    title: "Q1 Planning Meeting Notes",
    createdAt: new Date("2026-01-14T14:00:00"),
    sourceApp: "Notion",
    windowTitle: "Team Workspace - Q1 Planning",
    previewUrl: "/placeholder.svg",
    summary: "Key decisions from Q1 planning: focus on AI features, hire 3 engineers",
    entities: [
      { type: "deadline", value: "2026-03-31", confidence: 0.88 },
      { type: "person", value: "Sarah Chen", confidence: 0.91 },
      { type: "price", value: "$150,000", confidence: 0.85 },
    ],
    tags: ["work", "planning", "q1-2026"],
    intent: "reference",
    intentConfidence: 0.88,
    urgency: "high",
    deadline: new Date("2026-01-20T17:00:00"),
    priorityScore: 92,
    status: "unreviewed",
  },
  {
    id: "3",
    title: "Noise Cancelling Headphones Comparison",
    createdAt: new Date("2026-01-13T19:45:00"),
    sourceApp: "Chrome",
    windowTitle: "Amazon - Electronics",
    url: "https://amazon.com/headphones",
    previewUrl: "/placeholder.svg",
    summary: "Comparing Sony WH-1000XM5 vs Bose QC Ultra for work setup",
    entities: [
      { type: "company", value: "Sony", confidence: 0.97 },
      { type: "company", value: "Bose", confidence: 0.97 },
      { type: "price", value: "$399", confidence: 0.92 },
    ],
    tags: ["shopping", "electronics", "wfh"],
    intent: "buy",
    intentConfidence: 0.95,
    urgency: "low",
    priorityScore: 45,
    status: "reviewed",
  },
  {
    id: "4",
    title: "Machine Learning Fundamentals Course",
    createdAt: new Date("2026-01-12T08:00:00"),
    sourceApp: "Chrome",
    windowTitle: "Coursera - ML Course",
    url: "https://coursera.org/ml-fundamentals",
    previewUrl: "/placeholder.svg",
    summary: "Andrew Ng's updated ML course with new transformer architecture section",
    entities: [
      { type: "person", value: "Andrew Ng", confidence: 0.99 },
      { type: "company", value: "Coursera", confidence: 0.98 },
    ],
    tags: ["learning", "ml", "ai", "career"],
    intent: "learn",
    intentConfidence: 0.97,
    urgency: "medium",
    deadline: new Date("2026-02-28T23:59:00"),
    priorityScore: 72,
    status: "unreviewed",
  },
  {
    id: "5",
    title: "Startup Pitch Deck Template",
    createdAt: new Date("2026-01-11T16:20:00"),
    sourceApp: "Google Drive",
    windowTitle: "Pitch Deck v3.pptx",
    previewUrl: "/placeholder.svg",
    summary: "Latest version of pitch deck with updated metrics and roadmap",
    entities: [
      { type: "price", value: "$2M", confidence: 0.89 },
      { type: "date", value: "2026-Q2", confidence: 0.85 },
    ],
    tags: ["startup", "fundraising", "presentation"],
    intent: "share",
    intentConfidence: 0.82,
    urgency: "high",
    deadline: new Date("2026-01-18T09:00:00"),
    priorityScore: 88,
    status: "snoozed",
  },
  {
    id: "6",
    title: "Documentary: The Social Dilemma",
    createdAt: new Date("2026-01-10T21:00:00"),
    sourceApp: "Netflix",
    windowTitle: "Netflix - Documentary",
    url: "https://netflix.com/title/social-dilemma",
    previewUrl: "/placeholder.svg",
    summary: "Documentary about social media's impact on society and mental health",
    entities: [
      { type: "company", value: "Netflix", confidence: 0.99 },
      { type: "company", value: "Facebook", confidence: 0.88 },
    ],
    tags: ["documentary", "tech", "social-media"],
    intent: "watch",
    intentConfidence: 0.94,
    urgency: "low",
    priorityScore: 35,
    status: "done",
  },
  {
    id: "7",
    title: "TypeScript 5.4 Release Notes",
    createdAt: new Date("2026-01-09T11:15:00"),
    sourceApp: "Chrome",
    windowTitle: "TypeScript Blog",
    url: "https://devblogs.microsoft.com/typescript",
    previewUrl: "/placeholder.svg",
    summary: "New features in TS 5.4: improved inference, new utility types",
    entities: [
      { type: "company", value: "Microsoft", confidence: 0.96 },
    ],
    tags: ["typescript", "programming", "updates"],
    intent: "read",
    intentConfidence: 0.91,
    urgency: "medium",
    priorityScore: 65,
    status: "unreviewed",
  },
  {
    id: "8",
    title: "Job Application: Senior Engineer at Vercel",
    createdAt: new Date("2026-01-08T09:30:00"),
    sourceApp: "Gmail",
    windowTitle: "Gmail - Applications",
    previewUrl: "/placeholder.svg",
    summary: "Application submitted, awaiting response. Follow up if no reply by Jan 22",
    entities: [
      { type: "company", value: "Vercel", confidence: 0.99 },
      { type: "deadline", value: "2026-01-22", confidence: 0.75 },
    ],
    tags: ["career", "job-search", "applications"],
    intent: "apply",
    intentConfidence: 0.96,
    urgency: "high",
    deadline: new Date("2026-01-22T17:00:00"),
    priorityScore: 85,
    status: "unreviewed",
  },
];

const mockClusters: ThemeCluster[] = [
  {
    id: "c1",
    name: "Career Development",
    description: "Job applications, skills learning, and professional growth",
    captureIds: ["4", "8"],
    createdAt: new Date("2026-01-10"),
    updatedAt: new Date("2026-01-15"),
    color: "#3B82F6",
  },
  {
    id: "c2",
    name: "Tech Research",
    description: "Frontend frameworks, programming languages, and tools",
    captureIds: ["1", "7"],
    createdAt: new Date("2026-01-08"),
    updatedAt: new Date("2026-01-15"),
    color: "#10B981",
  },
  {
    id: "c3",
    name: "Startup & Business",
    description: "Fundraising, pitch materials, and business planning",
    captureIds: ["2", "5"],
    createdAt: new Date("2026-01-05"),
    updatedAt: new Date("2026-01-14"),
    color: "#F59E0B",
  },
  {
    id: "c4",
    name: "Personal Interests",
    description: "Shopping, entertainment, and lifestyle content",
    captureIds: ["3", "6"],
    createdAt: new Date("2026-01-01"),
    updatedAt: new Date("2026-01-13"),
    color: "#8B5CF6",
  },
];

const mockConnections: ConnectionEdge[] = [
  {
    id: "e1",
    sourceId: "1",
    targetId: "7",
    relationshipType: "related-technology",
    strength: 0.85,
    discoveredAt: new Date("2026-01-15"),
  },
  {
    id: "e2",
    sourceId: "4",
    targetId: "8",
    relationshipType: "career-goal",
    strength: 0.92,
    discoveredAt: new Date("2026-01-14"),
  },
  {
    id: "e3",
    sourceId: "2",
    targetId: "5",
    relationshipType: "project-related",
    strength: 0.78,
    discoveredAt: new Date("2026-01-13"),
  },
];

const mockNotifications: NotificationItem[] = [
  {
    id: "n1",
    type: "deadline",
    title: "Deadline Approaching",
    message: "Startup Pitch Deck is due in 2 days",
    relatedCaptureId: "5",
    createdAt: new Date("2026-01-16T08:00:00"),
    read: false,
    actionLabel: "Review Now",
    actionType: "review",
  },
  {
    id: "n2",
    type: "connection",
    title: "New Connection Found",
    message: "React Server Components links to your TypeScript notes",
    relatedCaptureId: "1",
    createdAt: new Date("2026-01-15T14:30:00"),
    read: false,
    actionLabel: "View Connection",
    actionType: "review",
  },
  {
    id: "n3",
    type: "suggestion",
    title: "Review Suggested",
    message: "You have 4 unreviewed items from this week",
    createdAt: new Date("2026-01-15T09:00:00"),
    read: true,
    actionLabel: "Review All",
    actionType: "review",
  },
  {
    id: "n4",
    type: "reminder",
    title: "Follow-up Reminder",
    message: "Check on Vercel application status",
    relatedCaptureId: "8",
    createdAt: new Date("2026-01-14T10:00:00"),
    read: false,
    actionLabel: "Remind Later",
    actionType: "remind",
  },
];

const mockDigestReports: DigestReport[] = [
  {
    id: "d1",
    weekStart: new Date("2026-01-06"),
    weekEnd: new Date("2026-01-12"),
    summary: "A productive week focused on career development and tech research. 8 new captures, 3 reviewed, 2 connections discovered.",
    themes: mockClusters.slice(0, 2),
    missedConnections: [mockConnections[2]],
    expiringItems: mockCaptures.filter(c => c.deadline && c.deadline < new Date("2026-01-20")),
    suggestedActions: [
      "Review Q1 Planning Meeting Notes before the deadline",
      "Complete ML Fundamentals Course enrollment",
      "Follow up on Vercel application",
    ],
    createdAt: new Date("2026-01-13T06:00:00"),
  },
];

const mockCollections: SmartCollection[] = [
  {
    id: "col1",
    name: "Learning Queue",
    description: "Items marked for learning",
    icon: "GraduationCap",
    filter: { intents: ["learn", "read", "watch"] },
    captureIds: ["1", "4", "6", "7"],
    order: 0,
  },
  {
    id: "col2",
    name: "High Priority",
    description: "Urgent items needing attention",
    icon: "AlertTriangle",
    filter: { urgency: ["high"] },
    captureIds: ["2", "5", "8"],
    order: 1,
  },
  {
    id: "col3",
    name: "Shopping List",
    description: "Items to purchase",
    icon: "ShoppingCart",
    filter: { intents: ["buy"] },
    captureIds: ["3"],
    order: 2,
  },
  {
    id: "col4",
    name: "Work Projects",
    description: "Work-related captures",
    icon: "Briefcase",
    filter: { tags: ["work", "startup", "career"] },
    captureIds: ["2", "5", "8"],
    order: 3,
  },
];

const mockSettings: UserSettings = {
  hotkey: "Ctrl+Shift+L",
  quietHoursStart: "22:00",
  quietHoursEnd: "08:00",
  dndEnabled: false,
  notificationCap: 10,
  captureSources: {
    browser: true,
    slack: true,
    email: true,
    documents: true,
    screenshots: false,
  },
  localFirst: true,
  accessibilityReducedMotion: false,
  accessibilityHighContrast: false,
};

// Simulated delay
const delay = (ms: number) => new Promise(resolve => setTimeout(resolve, ms));

// In-memory state for mutations
let capturesState = [...mockCaptures];
let notificationsState = [...mockNotifications];

// API Functions
// Replace the listCaptures function in lib/api.ts


// API Functions
export async function listCaptures(): Promise<CaptureItem[]> {
  try {
    console.log('📥 [API] Fetching captures from backend...');
    
    if (typeof window !== 'undefined') {
      try {
        const result = await getInbox({ limit: 50 });
        console.log(`✅ [API] Got ${result.items.length} items from backend`);
        return result.items.map(mapMemoryToCaptureItem);
      } catch (error) {
        console.error('❌ [API] Failed to fetch from backend:', error);
        console.log('⚠️ [API] Falling back to mock data');
        return mockCaptures;
      }
    }
    
    return mockCaptures;
  } catch (error) {
    console.error('❌ [API] Failed to fetch captures:', error);
    return [];
  }
}

export async function getCapture(id: string): Promise<CaptureItem | null> {
  try {
    if (typeof window !== 'undefined') {
      const result = await getCaptureById(id) as any;
      
      if (result.success && result.capture) {
        return mapMemoryToCaptureItem(result.capture);
      }
    }
    return mockCaptures.find(c => c.id === id) || null;
  } catch (error) {
    console.error('❌ [API] Failed to get capture:', error);
    return null;
  }
}

/**
 * Get full comprehensive capture details (including original inputs)
 * Used by detail drawer to show screenshot, audio, text notes, files
 */
export async function getCaptureDetails(id: string): Promise<any> {
  try {
    console.log('🔍 [API] Fetching full capture details:', id);
    
    if (typeof window !== 'undefined') {
      const result = await getCaptureById(id) as any;
      
      if (result.success && result.capture) {
        console.log('✅ [API] Got full capture details');
        return result.capture; // Return complete comprehensive capture with input data
      }
    }
    
    console.warn('⚠️ [API] No capture details found');
    return null;
    
  } catch (error) {
    console.error('❌ [API] Failed to get capture details:', error);
    return null;
  }
}

export async function getCaptureDetailsV2(id: string): Promise<any> {
  try {
    console.log('🔍 [API V2] Fetching enhanced capture details:', id);
    
    if (typeof window !== 'undefined') {
      const result = await getCaptureByIdV2(id) as any;
      
      if (result.success && result.capture) {
        console.log('✅ [API V2] Got enhanced capture with subcollections');
        console.log('🔬 [API V2] Research sources:', result.metadata?.research_sources_count || 0);
        console.log('📚 [API V2] Learning resources:', result.metadata?.resources_count || 0);
        return result.capture;
      }
    }
    
    console.warn('⚠️ [API V2] No capture details found');
    return null;
    
  } catch (error) {
    console.error('❌ [API V2] Failed to get capture details:', error);
    // Fallback to v1 if v2 fails
    console.log('🔄 [API V2] Falling back to v1 endpoint');
    return getCaptureDetails(id);
  }
}


export async function updateCapture(id: string, updates: Partial<CaptureItem>): Promise<CaptureItem | null> {
  await delay(100);
  const index = capturesState.findIndex(c => c.id === id);
  if (index === -1) return null;
  capturesState[index] = { ...capturesState[index], ...updates };
  return capturesState[index];
}

export async function deleteCapture(id: string): Promise<boolean> {
  await delay(100);
  const index = capturesState.findIndex(c => c.id === id);
  if (index === -1) return false;
  capturesState.splice(index, 1);
  return true;
}



export async function listConnections(): Promise<ConnectionEdge[]> {
  await delay(100);
  return [...mockConnections];
}

export async function listDigestReports(): Promise<DigestReport[]> {
  await delay(100);
  return [...mockDigestReports];
}

export async function listNotifications(): Promise<NotificationItem[]> {
  await delay(100);
  return [...notificationsState];
}

export async function markNotificationRead(id: string): Promise<boolean> {
  await delay(50);
  const notification = notificationsState.find(n => n.id === id);
  if (notification) {
    notification.read = true;
    return true;
  }
  return false;
}

// export async function listCollections(): Promise<SmartCollection[]> {
//   await delay(100);
//   return [...mockCollections];
// }

export async function getSettings(): Promise<UserSettings> {
  await delay(50);
  return { ...mockSettings };
}

export async function updateSettings(updates: Partial<UserSettings>): Promise<UserSettings> {
  await delay(100);
  Object.assign(mockSettings, updates);
  return { ...mockSettings };
}

// Helper to reset state (useful for testing)
export function resetState() {
  capturesState = [...mockCaptures];
  notificationsState = [...mockNotifications];
}

import { getCollections as apiGetCollections } from './api-client';

export async function listCollections(): Promise<SmartCollection[]> {
  try {
    console.log('📁 [API] Fetching collections...');
    
    if (typeof window !== 'undefined') {
      try {
        const result = await apiGetCollections();
        console.log(`✅ [API] Got ${result.collections.length} collections`);
        return result.collections;
      } catch (error) {
        console.error('❌ [API] Failed to fetch collections:', error);
        return [];
      }
    }
    
    return [];
  } catch (error) {
    console.error('❌ [API] Failed to fetch collections:', error);
    return [];
  }

}

import { getThemeClusters as apiGetThemeClusters } from './api-client';

export async function listClusters(): Promise<ThemeCluster[]> {
  try {
    console.log('🎨 [API] Fetching theme clusters...');
    
    if (typeof window !== 'undefined') {
      try {
        const result = await apiGetThemeClusters(4);
        
        if (result.clusters.length === 0 && result.message) {
          console.log('⚠️ [API]', result.message);
          return []; // Return empty, let UI show empty state
        }
        
        console.log(`✅ [API] Got ${result.clusters.length} theme clusters`);
        
        // Convert backend format to frontend ThemeCluster type
        return result.clusters.map((cluster: any) => ({
          id: cluster.id,
          name: cluster.name,
          description: cluster.description,
          captureIds: cluster.captureIds,
          createdAt: new Date(cluster.createdAt || Date.now()),
          updatedAt: new Date(cluster.updatedAt || Date.now()),
          color: cluster.color
        }));
        
      } catch (error) {
        console.error('❌ [API] Failed to fetch clusters:', error);
        return [];
      }
    }
    
    return [];
  } catch (error) {
    console.error('❌ [API] Failed to fetch clusters:', error);
    return [];
  }
}