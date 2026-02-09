"use client";

import { useEffect, useCallback, useState } from "react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import { updateCapture, getCaptureDetails } from "@/lib/api";
import { getCaptureDetailsV2 } from "@/lib/api";
import type { CaptureItem, CaptureStatus, } from "@/types/lifeos";
import type { EnhancedCaptureDetails, ExecutionActionV2 } from "@/types/lifeos";
import { AskGeminiButton } from "./ask-gemini-button";
import { HeroSection } from "./hero-section";
import { ExecutionResults } from "./execution-results";
import { CollapsibleSection } from "./collapsible-section";
import { MarkdownContent } from "./markdown-content";
import { GeminiProcessingInfo } from "./gemini-processing-info";
import { X, ExternalLink, Clock, Tag, AlertCircle, Calendar, Check, Moon, Image, Mic, FileText, Paperclip, Download, Play, Pause, Volume2, Brain, FileSearch, Search, BookOpen, CheckCircle } from "lucide-react";
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import rehypeRaw from 'rehype-raw';
import { Sparkles, Info, Briefcase, CheckSquare } from "lucide-react";
import { log } from "console";

interface DetailDrawerProps {
  item: CaptureItem | null;
  isOpen: boolean;
  onClose: () => void;
  onUpdate: (item: CaptureItem) => void;
}

interface CaptureDetails {
  id: string;
  created_at?: string;

  // Raw input with signed URLs
  input?: {
    screenshot_path?: string;
    screenshot_url?: string;
    screenshot_signed_url?: string;
    audio_path?: string;
    audio_url?: string;
    audio_signed_url?: string;
    text_note?: string;
    full_transcript?: string;
    context?: {
      app_name?: string;
      window_title?: string;
      url?: string;
    };
  };

  attached_files?: Array<{
    name: string;
    url: string;
    signed_url?: string;
    size_bytes: number;
    file_type: string;
  }>;

  // AI Generated - from classification
  classification?: {
    domain?: string;
    domain_confidence?: number;
    context_type?: string;
    primary_intent?: string;
    intent?: string;
    urgency?: string;
    overall_summary?: string;
    deadline?: string;
    entities?: Array<{
      type: string;
      value: string;
      confidence: number;
    }>;
    tags?: string[];
    actions?: Array<{
      intent?: string;
      summary?: string;
      status?: string;
      due_date?: string;
      priority?: number | string;
    }>;
  };

  // Execution results
  execution?: {
    total_actions?: number;
    successful?: number;
    failed?: number;
    skipped?: number;
    actions_executed?: Array<{
      intent: string;
      summary: string;
      status: string;
      tool_used?: string;
      tool_params?: any;
      result_data?: any;
      google_calendar_link?: string;
      google_task_id?: string;
      created_task_id?: string;
      created_event_id?: string;
      created_note_id?: string;
      invites_sent_to?: string[];
      error_message?: string;
    }>;
  };

  // Research results
  research?: {
    triggered?: boolean;
    summary?: string;
    sources?: Array<{
      title: string;
      url?: string;
      relevance?: number;
    }>;
    sources_count?: number;
  };

  // Learning resources
  resources?: {
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
      thumbnail_url?: string;
    }>;
    learning_path?: string;
    summary?: string;
  };

  // Proactive suggestions
  proactive?: {
    triggered?: boolean;
    suggestions?: Array<{
      type: string;
      title: string;
      description: string;
      confidence?: number;
      trigger_time?: string;
    }>;
  };

  [key: string]: any;
}

const urgencyColors = {
  low: "bg-muted text-muted-foreground",
  medium: "bg-warning/20 text-warning",
  high: "bg-destructive/20 text-destructive",
};

const intentLabels: Record<string, string> = {
  learn: "Learning",
  buy: "Purchase",
  apply: "Application",
  remember: "Remember",
  share: "Share",
  research: "Research",
  watch: "Watch",
  read: "Read",
  reference: "Reference",
  act: "Action",
  follow_up: "Follow Up",
};

export function DetailDrawer({ item, isOpen, onClose, onUpdate }: DetailDrawerProps) {
  const [captureDetails, setCaptureDetails] = useState<EnhancedCaptureDetails | null>(null);
  const [isLoadingDetails, setIsLoadingDetails] = useState(false);
  const [audioPlaying, setAudioPlaying] = useState(false);
  const [audioElement, setAudioElement] = useState<HTMLAudioElement | null>(null);

  // Fetch full capture details when drawer opens
  useEffect(() => {
    if (isOpen && item?.id) {
      setIsLoadingDetails(true);
      getCaptureDetailsV2(item.id)  // CHANGE FROM getCaptureDetails
        .then((details: any) => {
          console.log("✅ Raw details from API:", item);
          console.log("✅ captureDetails", captureDetails);
          console.log("✅ captureDetails.classification", captureDetails?.classification);
          console.log("✅ captureDetails.research", captureDetails?.research);
          console.log("✅ captureDetails.resources", captureDetails?.resources);
          console.log("✅ captureDetails.execution", captureDetails?.execution);
          setCaptureDetails(details);
        })
        .catch((err: Error) => {
          console.error('❌ [DetailDrawer] Failed to load:', err);
        })
        .finally(() => {
          setIsLoadingDetails(false);
        });
    }
  }, [isOpen, item?.id]);


  // Close on escape
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape" && isOpen) {
        onClose();
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isOpen, onClose]);

  // Cleanup audio on unmount
  useEffect(() => {
    return () => {
      if (audioElement) {
        audioElement.pause();
        audioElement.src = '';
      }
    };
  }, [audioElement]);

  const handleStatusChange = useCallback(async (newStatus: CaptureStatus) => {
    if (!item) return;
    const updated = await updateCapture(item.id, { status: newStatus });
    if (updated) {
      onUpdate(updated);
    }
  }, [item, onUpdate]);

  const toggleAudio = useCallback(() => {
    const audioUrl = captureDetails?.input?.audio_signed_url
      || captureDetails?.input?.audio_url;

    if (!audioUrl) return;

    if (!audioElement) {
      const audio = new Audio(audioUrl);
      audio.onended = () => setAudioPlaying(false);
      audio.onerror = () => {
        console.error('❌ Audio failed to load:', audioUrl);
        setAudioPlaying(false);
      };
      setAudioElement(audio);
      audio.play();
      setAudioPlaying(true);
    } else {
      if (audioPlaying) {
        audioElement.pause();
        setAudioPlaying(false);
      } else {
        audioElement.play();
        setAudioPlaying(true);
      }
    }
  }, [captureDetails?.input, audioElement, audioPlaying]);

  const formatFileSize = (bytes: number): string => {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
  };

  if (!item) return null;

  // Use signed URLs for direct GCS access
  const screenshotUrl = captureDetails?.input?.screenshot_signed_url
    || captureDetails?.input?.screenshot_url;

  const audioUrl = captureDetails?.input?.audio_signed_url
    || captureDetails?.input?.audio_url;

  const textNote = captureDetails?.input?.text_note
    || captureDetails?.input?.full_transcript;

  const hasScreenshot = !!screenshotUrl;
  const hasAudio = !!audioUrl;
  const hasText = !!textNote;
  const hasFiles = captureDetails?.attached_files && captureDetails.attached_files.length > 0;
  const hasOriginalInputs = hasScreenshot || hasAudio || hasText || hasFiles;

  // Extract AI data
  const execution = captureDetails?.execution;
  const hasExecution = execution && execution.actions_executed && execution.actions_executed.length > 0;

  const research = captureDetails?.research;
  const hasResearch = captureDetails?.research?.has_data === true &&
    (captureDetails.research.results || captureDetails?.research?.sources_count > 0);
  const resources = captureDetails?.resources;
  const hasResources = resources?.triggered && resources?.needs_resources && resources?.resources && resources.resources.length > 0;

  const proactive = captureDetails?.proactive;
  const hasProactive = proactive?.triggered && proactive?.suggestions && proactive.suggestions.length > 0;

  return (
    <>
      {/* Backdrop */}
      <div
        className={cn(
          "fixed inset-0 z-40 transition-opacity",
          isOpen ? "opacity-100" : "pointer-events-none opacity-0"
        )}
        style={{ backgroundColor: 'rgba(0, 0, 0, 0.4)' }}
        onClick={onClose}
        aria-hidden="true"
      />

      {/* Drawer */}
      <aside
        className={cn(
          "fixed right-0 top-0 z-50 h-full w-full max-w-[90vw] transform shadow-xl transition-transform duration-300 ease-in-out",
          isOpen ? "translate-x-0" : "translate-x-full"
        )}
        style={{
          backgroundColor: 'var(--color-bg-primary)',
          borderLeft: '1px solid var(--color-border-light)'
        }}
        role="dialog"
        aria-modal="true"
        aria-labelledby="drawer-title"
      >
        {/* Header */}
        <header className="flex items-start justify-between gap-4 p-6" style={{
          borderBottom: '1px solid var(--color-border-light)',
          backgroundColor: 'var(--color-bg-card)'
        }}>
          <div className="flex items-start gap-3 flex-1 min-w-0">
            <FileText className="h-5 w-5 mt-0.5 flex-shrink-0" style={{ color: 'var(--color-accent-blue)' }} />
            <div className="flex-1 min-w-0">
              <h2 id="drawer-title" className="text-lg font-semibold mb-1" style={{ color: 'var(--color-text-primary)' }}>
                {item.title}
              </h2>
              <div className="flex items-center gap-2 text-xs" style={{ color: 'var(--color-text-secondary)' }}>
                <span>{new Date(item.createdAt).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}</span>
                <span>•</span>
                <span>{item.intent}</span>
              </div>
            </div>
          </div>

          <div className="flex items-center gap-2 flex-shrink-0">

            <Button
              variant="ghost"
              size="icon"
              onClick={onClose}
              aria-label="Close drawer"
            >
              <X className="h-4 w-4" />
            </Button>
          </div>
        </header>

        {/* Content - 70/30 Split */}
        <div className="flex h-full">

          {/* LEFT SIDE - AI Generated Information (70%) */}
          <div className="w-[70%] border-r overflow-y-auto p-6" style={{
            height: "calc(100% - 65px)",
            backgroundColor: 'var(--color-bg-secondary)',
            borderColor: 'var(--color-border-light)'
          }}>
            {isLoadingDetails ? (
              <div className="flex items-center justify-center h-32">
                <div className="h-6 w-6 animate-spin rounded-full border-2 border-muted border-t-accent" />
              </div>
            ) : (
              <div className="space-y-6">

                {/* Hero Section - Enhanced */}
                <div className="rounded-xl border p-6 shadow-sm hover:shadow-md transition-shadow" style={{
                  backgroundColor: 'var(--color-bg-card)',
                  borderColor: 'var(--color-border-light)'
                }}>
                  {/* Badges */}
                  <div className="flex flex-wrap items-center gap-2 mb-3">
                    <Badge className="text-xs font-medium px-3 py-1 rounded-full border-0" style={{
                      backgroundColor: 'var(--color-accent-blue-light)',
                      color: 'var(--color-accent-blue)'
                    }}>
                      <Briefcase className="h-3 w-3 mr-1 inline" />
                      {captureDetails?.classification?.domain?.replace(/_/g, ' ') || 'Unknown'} {captureDetails?.classification?.domain_confidence && `${Math.round(captureDetails.classification.domain_confidence * 100)}%`}
                    </Badge>

                    <Badge className="text-xs font-medium px-3 py-1 rounded-full border-0" style={{
                      backgroundColor: 'var(--color-accent-blue-light)',
                      color: 'var(--color-accent-blue)'
                    }}>
                      {captureDetails?.classification?.primary_intent || captureDetails?.classification?.intent || 'reference'}
                    </Badge>

                    <Badge className="text-xs font-medium px-3 py-1 rounded-full border-0" style={{
                      backgroundColor: (captureDetails?.classification?.urgency === 'high' || captureDetails?.classification?.urgency === 'critical')
                        ? 'var(--color-accent-red-light)'
                        : captureDetails?.classification?.urgency === 'medium'
                          ? 'var(--color-accent-orange-light)'
                          : 'var(--color-accent-green-light)',
                      color: (captureDetails?.classification?.urgency === 'high' || captureDetails?.classification?.urgency === 'critical')
                        ? 'var(--color-accent-red)'
                        : captureDetails?.classification?.urgency === 'medium'
                          ? 'var(--color-accent-orange)'
                          : 'var(--color-accent-green)'
                    }}>
                      <AlertCircle className="h-3 w-3 mr-1 inline" />
                      {captureDetails?.classification?.urgency || 'low'}
                    </Badge>
                  </div>

                  {/* Summary */}
                  <p className="text-sm leading-relaxed mb-4" style={{
                    color: 'var(--color-text-primary)',
                    fontWeight: 500
                  }}>
                    {captureDetails?.classification?.overall_summary || item.summary || "Processing..."}
                  </p>

                  {/* Additional metadata row */}
                  {captureDetails?.classification?.total_actions > 0 && (
                    <div className="flex items-center gap-3 mb-4 text-xs" style={{ color: 'var(--color-text-secondary)' }}>
                      <span className="flex items-center gap-1">
                        <CheckSquare className="h-3 w-3" />
                        {captureDetails?.classification.total_actions} action{captureDetails?.classification.total_actions !== 1 ? 's' : ''} identified
                      </span>
                      {captureDetails?.classification?.context_type && (
                        <>
                          <span>•</span>
                          <span>{captureDetails.classification.context_type.replace(/_/g, ' ')}</span>
                        </>
                      )}
                    </div>
                  )}

                  {/* Powered by Gemini 3 - hover effect without white background */}
                  <div className="flex justify-end">
                    <div className="inline-flex">
                      <GeminiProcessingInfo captureData={captureDetails || {}} />
                    </div>
                  </div>
                </div>



                {captureDetails?.execution?.actions_executed && captureDetails.execution.actions_executed.length > 0 && (
                  <ExecutionResults
                    actions={captureDetails.execution.actions_executed}
                    successCount={captureDetails.execution.successful ?? 0}
                    failedCount={captureDetails.execution.failed ?? 0}
                    skippedCount={captureDetails.execution.skipped ?? 0}
                  />
                )}

                {/* Research Results */}
                {captureDetails?.research?.has_data && captureDetails?.research.sources_count > 0 && (
                  <CollapsibleSection
                    title="Research Insights"
                    subtitle={`${captureDetails.research.sources_count} sources via grounded search`}
                    icon={Search}
                    badge={captureDetails.research.sources_count}
                    defaultOpen={true}
                  >
                    <div className="space-y-3">
                      {/* Grounded Search Badge */}
                      <div className="flex items-center gap-2 px-3 py-2 rounded-lg" style={{
                        backgroundColor: 'var(--color-accent-green-light)',
                        borderColor: 'var(--color-accent-green)',
                        borderWidth: '1px'
                      }}>
                        <CheckCircle className="h-3.5 w-3.5" style={{ color: 'var(--color-accent-green)' }} />
                        <span className="text-xs font-medium" style={{ color: 'var(--color-accent-green)' }}>
                          Grounded with Google Search
                        </span>
                        <span className="text-xs" style={{ color: 'var(--color-text-secondary)' }}>
                          • {captureDetails.research.sources_count} authoritative sources
                        </span>
                      </div>

                      {/* Research Results - Markdown formatted */}
                      {captureDetails.research.results && (
                        <div className="rounded-lg border p-4" style={{
                          backgroundColor: 'var(--color-bg-card)',
                          borderColor: 'var(--color-border-light)'
                        }}>
                          <MarkdownContent content={captureDetails.research.results} />
                        </div>
                      )}
                    </div>
                  </CollapsibleSection>
                )}

                {/* Learning Resources */}
                {captureDetails?.resources?.has_data && captureDetails.resources.resources_count > 0 && (
                  <CollapsibleSection
                    title="Learning Resources"
                    subtitle={captureDetails.resources.ai_reasoning || "Curated by AI"}
                    icon={BookOpen}
                    badge={captureDetails.resources.resources_count}
                    defaultOpen={false}
                  >
                    <div className="space-y-4">
                      {/* Learning Path */}
                      {captureDetails.resources.learning_path && (
                        <div className="rounded-lg border p-4" style={{
                          backgroundColor: 'var(--color-bg-card)',
                          borderColor: 'var(--color-border-light)'
                        }}>
                          <div className="flex items-start gap-2 mb-2">
                            <BookOpen className="h-4 w-4 mt-0.5" style={{ color: 'var(--color-accent-blue)' }} />
                            <span className="text-xs font-semibold" style={{ color: 'var(--color-text-primary)' }}>
                              Suggested Learning Path
                            </span>
                          </div>
                          <p className="text-xs leading-relaxed" style={{ color: 'var(--color-text-secondary)' }}>
                            {captureDetails.resources.learning_path}
                          </p>
                        </div>
                      )}

                      {/* Resources List */}
                      {captureDetails.resources.resources && captureDetails.resources.resources.length > 0 && (
                        <div className="space-y-3">
                          {captureDetails.resources.resources.map((resource, idx) => (
                            <a
                              key={idx}
                              href={resource.url}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="group flex items-start gap-3 p-4 rounded-lg border shadow-sm transition-all hover:shadow-md"
                              style={{
                                backgroundColor: 'var(--color-bg-card)',
                                borderColor: 'var(--color-border-light)'
                              }}
                            >
                              {/* Icon */}
                              <div className="flex-shrink-0 p-2 rounded-lg" style={{
                                backgroundColor: resource.type === 'Video Tutorial' || resource.type === 'video'
                                  ? 'var(--color-accent-red-light)'
                                  : 'var(--color-accent-blue-light)'
                              }}>
                                {(resource.type === 'Video Tutorial' || resource.type === 'video') &&
                                  <Play className="h-4 w-4" style={{ color: 'var(--color-accent-red)' }} />
                                }
                                {resource.type === 'Article' &&
                                  <FileText className="h-4 w-4" style={{ color: 'var(--color-accent-blue)' }} />
                                }
                                {!['Video Tutorial', 'video', 'Article'].includes(resource.type) &&
                                  <BookOpen className="h-4 w-4" style={{ color: 'var(--color-accent-blue)' }} />
                                }
                              </div>

                              {/* Content */}
                              <div className="flex-1 min-w-0">
                                <h4 className="text-sm font-semibold mb-1 group-hover:text-blue-600 transition-colors" style={{
                                  color: 'var(--color-text-primary)'
                                }}>
                                  {resource.title}
                                </h4>
                                <p className="text-xs mb-2 line-clamp-2 leading-relaxed" style={{
                                  color: 'var(--color-text-secondary)'
                                }}>
                                  {resource.description}
                                </p>

                                {/* Metadata */}
                                <div className="flex items-center gap-2 flex-wrap">
                                  <span className="text-xs" style={{ color: 'var(--color-text-secondary)' }}>
                                    {resource.source}
                                  </span>
                                  {resource.relevance_score && (
                                    <>
                                      <span style={{ color: 'var(--color-text-secondary)' }}>•</span>
                                      <Badge className="text-xs px-2 py-0.5 border-0" style={{
                                        backgroundColor: 'var(--color-accent-green-light)',
                                        color: 'var(--color-accent-green)'
                                      }}>
                                        {Math.round(resource.relevance_score)}% match
                                      </Badge>
                                    </>
                                  )}
                                  <span style={{ color: 'var(--color-text-secondary)' }}>•</span>
                                  <Badge className="text-xs px-2 py-0.5 border-0 capitalize" style={{
                                    backgroundColor: 'var(--color-accent-blue-light)',
                                    color: 'var(--color-accent-blue)'
                                  }}>
                                    {resource.type}
                                  </Badge>
                                </div>
                              </div>

                              {/* External link icon */}
                              <ExternalLink className="h-4 w-4 flex-shrink-0 mt-1 opacity-0 group-hover:opacity-100 transition-opacity"
                                style={{ color: 'var(--color-accent-blue)' }}
                              />
                            </a>
                          ))}
                        </div>
                      )}
                    </div>
                  </CollapsibleSection>
                )}

                {/* Show message if no AI data */}
                {!hasExecution && !hasResearch && !hasResources && !hasProactive && (
                  <div className="flex flex-col items-center justify-center py-12 text-center rounded-lg border" style={{
                    backgroundColor: 'var(--color-bg-card)',
                    borderColor: 'var(--color-border-light)'
                  }}>
                    <Brain className="h-12 w-12 mb-3 opacity-30" style={{ color: 'var(--color-text-secondary)' }} />
                    <p className="text-sm font-medium" style={{ color: 'var(--color-text-primary)' }}>
                      No AI-generated insights available yet
                    </p>
                    <p className="text-xs mt-1" style={{ color: 'var(--color-text-secondary)' }}>
                      Processing may still be in progress
                    </p>
                  </div>
                )}

                {/* Quick Actions */}
                <div className="rounded-lg border p-4 shadow-sm" style={{
                  backgroundColor: 'var(--color-bg-card)',
                  borderColor: 'var(--color-border-light)'
                }}>
                  <h4 className="mb-3 text-sm font-semibold" style={{ color: 'var(--color-text-primary)' }}>
                    Quick Actions
                  </h4>
                  <div className="flex flex-col gap-2">
                    {item.status !== "reviewed" && (
                      <Button
                        size="sm"
                        onClick={() => handleStatusChange("reviewed")}
                        className="gap-2 h-9 justify-start"
                        style={{
                          backgroundColor: 'var(--color-accent-blue)',
                          color: '#ffffff'
                        }}
                      >
                        <Check className="h-4 w-4" />
                        Mark Reviewed
                      </Button>
                    )}
                    {item.status !== "snoozed" && (
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => handleStatusChange("snoozed")}
                        className="gap-2 h-9 justify-start"
                        style={{
                          borderColor: 'var(--color-border-default)',
                          color: 'var(--color-text-primary)'
                        }}
                      >
                        <Moon className="h-4 w-4" />
                        Snooze
                      </Button>
                    )}
                    {item.status !== "done" && (
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => handleStatusChange("done")}
                        className="gap-2 h-9 justify-start"
                        style={{
                          borderColor: 'var(--color-accent-green)',
                          color: 'var(--color-accent-green)'
                        }}
                      >
                        <Check className="h-4 w-4" />
                        Mark Done
                      </Button>
                    )}
                  </div>
                </div>

              </div>
            )}
          </div>

          {/* RIGHT SIDE - Raw Input Data (30%) */}
          <div className="w-[30%] overflow-y-auto p-4" style={{
            height: "calc(100% - 65px)",
            backgroundColor: 'var(--color-bg-tertiary)'
          }}>            <h3 className="text-sm font-semibold text-foreground mb-4 flex items-center gap-2">
              <FileText className="h-4 w-4" />
              Raw Capture
            </h3>

            {isLoadingDetails ? (
              <div className="flex items-center justify-center h-32">
                <div className="h-6 w-6 animate-spin rounded-full border-2 border-muted border-t-accent" />
              </div>
            ) : !hasOriginalInputs ? (
              <div className="flex flex-col items-center justify-center h-32 text-center text-muted-foreground text-sm">
                <FileText className="h-8 w-8 mb-2 opacity-50" />
                <p>No raw inputs</p>
              </div>
            ) : (
              <div className="space-y-4">

                {/* Screenshot */}
                {hasScreenshot && (
                  <div className="space-y-2">
                    <div className="flex items-center gap-2 text-xs font-medium text-foreground">
                      <Image className="h-3 w-3" />
                      Screenshot
                    </div>
                    <div className="rounded-lg border border-border overflow-hidden bg-muted">
                      <img
                        src={screenshotUrl}
                        alt="Capture screenshot"
                        className="w-full h-auto"
                        onError={(e) => {
                          console.error('❌ Screenshot failed to load:', screenshotUrl);
                          const target = e.target as HTMLImageElement;
                          target.style.display = 'none';
                          const parent = target.parentElement;
                          if (parent) {
                            parent.innerHTML = '<div class="p-4 text-center text-xs text-muted-foreground">Screenshot not available</div>';
                          }
                        }}
                      />
                    </div>
                  </div>
                )}

                {/* Text Note */}
                {hasText && (
                  <div className="space-y-2">
                    <div className="flex items-center gap-2 text-xs font-medium text-foreground">
                      <FileText className="h-3 w-3" />
                      Text Content
                    </div>
                    <div className="rounded-lg border border-border p-3 bg-card">
                      <p className="text-xs text-foreground whitespace-pre-wrap leading-relaxed">
                        {textNote}
                      </p>
                    </div>
                  </div>
                )}

                {/* Audio Recording */}
                {hasAudio && (
                  <div className="space-y-2">
                    <div className="flex items-center gap-2 text-xs font-medium text-foreground">
                      <Mic className="h-3 w-3" />
                      Audio
                    </div>
                    <div className="rounded-lg border border-border p-3 bg-card">
                      <div className="flex items-center gap-2">
                        <Button
                          variant="ghost"
                          size="icon"
                          onClick={toggleAudio}
                          className="h-8 w-8 rounded-full"
                        >
                          {audioPlaying ? (
                            <Pause className="h-4 w-4" />
                          ) : (
                            <Play className="h-4 w-4" />
                          )}
                        </Button>
                        <div className="flex-1">
                          <div className="flex items-center gap-2">
                            <Volume2 className="h-3 w-3 text-muted-foreground" />
                            <div className="flex-1 h-1 bg-accent/20 rounded-full overflow-hidden">
                              <div className="h-full bg-accent w-0 animate-pulse" />
                            </div>
                          </div>
                        </div>
                        <a
                          href={audioUrl}
                          download
                          className="text-muted-foreground hover:text-foreground transition-colors"
                        >
                          <Download className="h-3 w-3" />
                        </a>
                      </div>
                    </div>
                  </div>
                )}

                {/* Attached Files */}
                {hasFiles && (
                  <div className="space-y-2">
                    <div className="flex items-center gap-2 text-xs font-medium text-foreground">
                      <Paperclip className="h-3 w-3" />
                      Files ({captureDetails?.attached_files?.length || 0})
                    </div>
                    <div className="space-y-2">
                      {captureDetails?.attached_files?.map((file, idx) => (
                        <a
                          key={idx}
                          href={file.signed_url || file.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="flex items-center gap-2 p-2 rounded-lg border border-border bg-card hover:bg-muted/50 transition-colors group text-xs"
                        >
                          <div className="flex-1 min-w-0">
                            <p className="font-medium text-foreground truncate group-hover:text-accent transition-colors">
                              {file.name}
                            </p>
                            <p className="text-muted-foreground">
                              {formatFileSize(file.size_bytes || file.file_size || 0)} • {file.file_type}

                            </p>
                          </div>
                          <Download className="h-3 w-3 text-muted-foreground group-hover:text-accent transition-colors flex-shrink-0" />
                        </a>
                      ))}
                    </div>
                  </div>
                )}

              </div>
            )}
          </div>

        </div>

        {/* {process.env.NODE_ENV === "development" && (
          <pre style={{
            position: "fixed",
            bottom: 10,
            right: 10,
            width: 500,
            height: 600,
            overflow: "auto",
            background: "#000",
            color: "#0f0",
            fontSize: 10,
            zIndex: 9999
          }}>
            {JSON.stringify(captureDetails, null, 2)}
          </pre>
        )} */}

      </aside>

    </>

  );
}