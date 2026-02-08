"use client";

import { useEffect, useCallback, useState } from "react";
import { X, ExternalLink, Clock, Tag, AlertCircle, Calendar, Check, Moon, Image, Mic, FileText, Paperclip, Download, Play, Pause, Volume2, Brain, FileSearch, Search, BookOpen } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import { updateCapture, getCaptureDetails } from "@/lib/api";
import { getCaptureDetailsV2 } from "@/lib/api";
import type { CaptureItem, CaptureStatus } from "@/types/lifeos";
import { AskGeminiButton } from "./ask-gemini-button";
import { HeroSection } from "./hero-section";
import { ExecutionResults } from "./execution-results";
import { CollapsibleSection } from "./collapsible-section";

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
  const [captureDetails, setCaptureDetails] = useState<CaptureDetails | null>(null);
  const [isLoadingDetails, setIsLoadingDetails] = useState(false);
  const [audioPlaying, setAudioPlaying] = useState(false);
  const [audioElement, setAudioElement] = useState<HTMLAudioElement | null>(null);

  // Fetch full capture details when drawer opens
  useEffect(() => {
    if (isOpen && item?.id) {
      setIsLoadingDetails(true);
      getCaptureDetailsV2(item.id)  // CHANGE FROM getCaptureDetails
        .then((details: any) => {
          console.log('📥 [DetailDrawer V2] Fetched enhanced details:', details);
          console.log('🔬 Research sources:', details?.research?.sources?.length || 0);
          console.log('📚 Learning resources:', details?.resources?.resources?.length || 0);
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
  const hasResearch = research?.triggered && research?.sources && research.sources.length > 0;

  const resources = captureDetails?.resources;
  const hasResources = resources?.triggered && resources?.needs_resources && resources?.resources && resources.resources.length > 0;

  const proactive = captureDetails?.proactive;
  const hasProactive = proactive?.triggered && proactive?.suggestions && proactive.suggestions.length > 0;

  return (
    <>
      {/* Backdrop */}
      <div
        className={cn(
          "fixed inset-0 z-40 bg-background/80 backdrop-blur-sm transition-opacity",
          isOpen ? "opacity-100" : "pointer-events-none opacity-0"
        )}
        onClick={onClose}
        aria-hidden="true"
      />

      {/* Drawer */}
      <aside
        className={cn(
          "fixed right-0 top-0 z-50 h-full w-full max-w-[90vw] transform border-l border-border bg-background shadow-xl transition-transform duration-300 ease-in-out",
          isOpen ? "translate-x-0" : "translate-x-full"
        )}
        role="dialog"
        aria-modal="true"
        aria-labelledby="drawer-title"
      >
        {/* Header */}
        <header className="flex items-center justify-between border-b border-border p-4">
          <h2 id="drawer-title" className="text-lg font-semibold text-foreground">
            Capture Details
          </h2>
          <Button
            variant="ghost"
            size="icon"
            onClick={onClose}
            aria-label="Close drawer"
          >
            <X className="h-4 w-4" />
          </Button>
        </header>

        {/* Content - 70/30 Split */}
        <div className="flex h-full">
          {/* LEFT SIDE - AI Generated Information (70%) */}
          <div className="w-[70%] border-r border-border overflow-y-auto p-6" style={{ height: "calc(100% - 65px)" }}>

            {isLoadingDetails ? (
              <div className="flex items-center justify-center h-32">
                <div className="h-6 w-6 animate-spin rounded-full border-2 border-muted border-t-accent" />
              </div>
            ) : (
              <div className="space-y-6">

                {/* Hero Section - NEW */}
                {captureDetails?.classification && (
                  <HeroSection
                    title={item.title}
                    summary={captureDetails.classification.overall_summary}
                    domain={captureDetails.classification.domain || 'ideas_thoughts'}
                    intent={captureDetails.classification.primary_intent || captureDetails.classification.intent || 'remember'}
                    urgency={captureDetails.classification.urgency || 'medium'}
                    deadline={captureDetails.classification.deadline}
                    domainConfidence={captureDetails.classification.domain_confidence}
                  />
                )}

                {/* Ask Gemini Button */}
                <div>
                  <AskGeminiButton captureId={item.id} variant="button" />
                </div>

                {/* Execution Results - NEW */}
                {hasExecution && (
                  <ExecutionResults
                    actions={execution.actions_executed || []}
                    successCount={execution.successful || 0}
                    failedCount={execution.failed || 0}
                    skippedCount={execution.skipped || 0}
                  />
                )}

                {/* Research Results - IMPROVED */}
                {hasResearch && (
                  <CollapsibleSection
                    title="Research Results"
                    subtitle={research.summary ? research.summary.substring(0, 100) + '...' : undefined}
                    icon={Search}
                    badge={research.sources_count || research.sources?.length}
                    defaultOpen={true}
                  >
                    <div className="space-y-4">
                      {/* Research Summary */}
                      {research.summary && (
                        <div className="bg-muted/30 rounded-lg p-3">
                          <p className="text-sm text-foreground leading-relaxed">
                            {research.summary}
                          </p>
                        </div>
                      )}

                      {/* Sources */}
                      {research.sources && research.sources.length > 0 && (
                        <div className="space-y-2">
                          <h4 className="text-xs font-semibold text-muted-foreground uppercase tracking-wide">
                            Sources ({research.sources.length})
                          </h4>
                          <div className="space-y-2">
                            {research.sources.slice(0, 5).map((source, idx) => (
                              <div
                                key={idx}
                                className="flex items-start gap-3 p-3 rounded-lg border border-border bg-card hover:bg-muted/50 transition-colors"
                              >
                                <FileSearch className="h-4 w-4 text-muted-foreground mt-0.5 flex-shrink-0" />
                                <div className="flex-1 min-w-0">
                                  <h4 className="text-sm font-medium text-foreground mb-1">
                                    {source.title}
                                  </h4>
                                  {source.url && (
                                    <a
                                      href={source.url}
                                      target="_blank"
                                      rel="noopener noreferrer"
                                      className="inline-flex items-center gap-1 text-xs text-accent hover:underline"
                                    >
                                      <ExternalLink className="h-3 w-3" />
                                      View source
                                    </a>
                                  )}
                                </div>
                                {source.relevance && (
                                  <Badge variant="outline" className="text-xs shrink-0">
                                    {Math.round(source.relevance * 100)}%
                                  </Badge>
                                )}
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  </CollapsibleSection>
                )}

                {/* Learning Resources - NEW */}
                {hasResources && (
                  <CollapsibleSection
                    title="Learning Resources"
                    subtitle={resources.ai_reasoning}
                    icon={BookOpen}
                    badge={resources.resources?.length}
                    defaultOpen={true}
                  >
                    <div className="space-y-4">
                      {/* Learning Path */}
                      {resources.learning_path && (
                        <div className="bg-blue-50/50 border border-blue-200 rounded-lg p-3 dark:bg-blue-950/20 dark:border-blue-800">
                          <p className="text-xs font-semibold text-blue-900 dark:text-blue-100 mb-1">
                            Suggested Learning Path
                          </p>
                          <p className="text-sm text-blue-700 dark:text-blue-300">
                            {resources.learning_path}
                          </p>
                        </div>
                      )}

                      {/* Resources Grid */}
                      {resources.resources && resources.resources.length > 0 && (
                        <div className="space-y-2">
                          {resources.resources.map((resource, idx) => (
                            <a
                              key={idx}
                              href={resource.url}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="block p-3 rounded-lg border border-border bg-card hover:bg-muted/50 transition-colors group"
                            >
                              <div className="flex items-start gap-3">
                                <div className="text-2xl flex-shrink-0">
                                  {resource.type === 'video' && '🎥'}
                                  {resource.type === 'article' && '📄'}
                                  {resource.type === 'course' && '📚'}
                                  {resource.type === 'documentation' && '📖'}
                                </div>
                                <div className="flex-1 min-w-0">
                                  <h4 className="text-sm font-medium text-foreground group-hover:text-accent transition-colors mb-1">
                                    {resource.title}
                                  </h4>
                                  <p className="text-xs text-muted-foreground mb-2">
                                    {resource.description}
                                  </p>
                                  <div className="flex items-center gap-2">
                                    <span className="text-xs text-muted-foreground">
                                      {resource.source}
                                    </span>
                                    {resource.relevance_score && (
                                      <Badge variant="outline" className="text-xs">
                                        {Math.round(resource.relevance_score * 100)}% relevant
                                      </Badge>
                                    )}
                                  </div>
                                </div>
                              </div>
                            </a>
                          ))}
                        </div>
                      )}
                    </div>
                  </CollapsibleSection>
                )}

                {/* Show message if no AI data */}
                {!hasExecution && !hasResearch && !hasResources && !hasProactive && (
                  <div className="flex flex-col items-center justify-center py-12 text-center text-muted-foreground">
                    <Brain className="h-12 w-12 mb-3 opacity-30" />
                    <p className="text-sm">No AI-generated insights available yet</p>
                    <p className="text-xs mt-1">Processing may still be in progress</p>
                  </div>
                )}

                {/* Action Buttons */}
                <div className="border-t border-border pt-4">
                  <h4 className="mb-3 text-sm font-medium text-foreground">Quick Actions</h4>
                  <div className="flex flex-col gap-2">
                    {item.status !== "reviewed" && (
                      <Button
                        size="sm"
                        onClick={() => handleStatusChange("reviewed")}
                        className="gap-2 h-9"
                      >
                        <Check className="h-4 w-4" />
                        Mark Reviewed
                      </Button>
                    )}
                    {item.status !== "snoozed" && (
                      <Button
                        size="sm"
                        variant="secondary"
                        onClick={() => handleStatusChange("snoozed")}
                        className="gap-2 h-9"
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
                        className="gap-2 h-9"
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
          <div className="w-[30%] overflow-y-auto p-4 bg-muted/20" style={{ height: "calc(100% - 65px)" }}>
            <h3 className="text-sm font-semibold text-foreground mb-4 flex items-center gap-2">
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
                              {formatFileSize(file.size_bytes)} • {file.file_type}
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
      </aside>
    </>
  );
}