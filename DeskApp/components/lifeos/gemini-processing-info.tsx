"use client";

import { Info, Eye, Brain, Search, Zap, CheckCircle, BookOpen } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

interface GeminiProcessingInfoProps {
  captureData: any;
}

export function GeminiProcessingInfo({ captureData }: GeminiProcessingInfoProps) {
  const hasScreenshot = !!captureData.input?.screenshot_path || !!captureData.input?.screenshot_url;
  const hasAudio = !!captureData.input?.audio_path || !!captureData.input?.audio_url;
  const hasText = !!captureData.input?.text_note;
  const hasOCR = !!captureData.perception?.ocr_text;
  const hasTranscript = !!captureData.perception?.audio_transcript;

  const stages = [
    {
      icon: Eye,
      label: "Perception",
      description: hasOCR 
        ? "Vision model extracted text from screenshot" 
        : hasTranscript 
          ? "Audio model transcribed voice recording" 
          : hasText
            ? "Text analysis"
            : "Multi-modal input processed",
      active: hasScreenshot || hasAudio || hasText || hasOCR || hasTranscript,
      time: captureData.perception?.processing_time_ms,
    },
    {
      icon: Brain,
      label: "Classification",
      description: `Identified as ${captureData.classification?.domain?.replace(/_/g, ' ') || 'unknown'} domain with ${captureData.classification?.primary_intent || captureData.classification?.intent || 'unknown'} intent`,
      active: !!captureData.classification,
      time: captureData.classification?.processing_time_ms,
      confidence: captureData.classification?.domain_confidence,
    },
    {
      icon: Search,
      label: "Research",
      description: captureData.research?.has_data 
        ? `Grounded search found ${captureData.research.sources_count || 0} sources`
        : "Not triggered for this capture",
      active: captureData.research?.has_data || false,
      time: captureData.research?.processing_time_ms,
    },
    {
      icon: BookOpen,
      label: "Resources",
      description: captureData.resources?.has_data
        ? `Found ${captureData.resources.resources_count || 0} learning resources`
        : "Not triggered for this capture",
      active: captureData.resources?.has_data || false,
      time: captureData.resources?.processing_time_ms,
    },
    {
      icon: Zap,
      label: "Execution",
      description: captureData.execution?.total_actions 
        ? `Created ${captureData.execution.successful || 0} actions via function calling`
        : "No actions executed",
      active: (captureData.execution?.total_actions || 0) > 0,
      time: captureData.execution?.processing_time_ms,
    },
  ];

  return (
    <Popover>
      <PopoverTrigger asChild>
        <Button
          variant="ghost"
          size="sm"
          className="h-7 gap-1.5 text-xs border transition-all"
          style={{
            backgroundColor: 'var(--color-accent-blue-light)',
            borderColor: 'var(--color-accent-blue)',
            color: 'var(--color-accent-blue)'
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.transform = 'scale(1.08)';
            e.currentTarget.style.boxShadow = '0 4px 12px rgba(26, 115, 232, 0.2)';
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.transform = 'scale(1)';
            e.currentTarget.style.boxShadow = 'none';
          }}
        >
          <Info className="h-3.5 w-3.5" />
          <span className="font-medium">Powered by Gemini 3</span>
        </Button>
      </PopoverTrigger>
      <PopoverContent 
        className="w-96 backdrop-blur-xl border rounded-xl"
        style={{
          backgroundColor: 'var(--color-bg-card)',
          borderColor: 'var(--color-border-light)'
        }}
        align="start"
      >
        <div className="space-y-4">
          <div>
            <h4 className="font-semibold text-sm mb-1" style={{ color: 'var(--color-text-primary)' }}>
              AI Processing Pipeline
            </h4>
            <p className="text-xs" style={{ color: 'var(--color-text-secondary)' }}>
              Multi-agent orchestration powered by Google Gemini 3
            </p>
          </div>

          <div className="space-y-3">
            {stages.map((stage, idx) => (
              <div 
                key={idx}
                className={cn(
                  "flex items-start gap-3 p-2.5 rounded-lg transition-all border",
                  stage.active 
                    ? "" 
                    : "opacity-40"
                )}
                style={{
                  backgroundColor: stage.active ? 'var(--color-accent-blue-light)' : 'var(--color-bg-secondary)',
                  borderColor: stage.active ? 'var(--color-accent-blue)' : 'var(--color-border-light)'
                }}
              >
                <div 
                  className="p-1.5 rounded-md"
                  style={{
                    backgroundColor: stage.active ? 'rgba(26, 115, 232, 0.2)' : 'var(--color-bg-tertiary)'
                  }}
                >
                  <stage.icon 
                    className="h-3.5 w-3.5"
                    style={{ 
                      color: stage.active ? 'var(--color-accent-blue)' : 'var(--color-text-muted)' 
                    }}
                  />
                </div>
                
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-0.5">
                    <span className="text-xs font-medium" style={{ color: 'var(--color-text-primary)' }}>
                      {stage.label}
                    </span>
                    {stage.active && (
                      <CheckCircle className="h-3 w-3" style={{ color: 'var(--color-accent-green)' }} />
                    )}
                  </div>
                  <p className="text-xs leading-relaxed" style={{ color: 'var(--color-text-secondary)' }}>
                    {stage.description}
                  </p>
                  
                  {stage.active && (stage.time || stage.confidence) && (
                    <div className="flex items-center gap-2 mt-1.5">
                      {stage.time !== null && stage.time !== undefined && stage.time > 0 && (
                        <Badge 
                          className="text-[10px] h-4 px-1.5 border-0"
                          style={{
                            backgroundColor: 'var(--color-bg-tertiary)',
                            color: 'var(--color-text-secondary)'
                          }}
                        >
                          {stage.time}ms
                        </Badge>
                      )}
                      {stage.confidence && (
                        <Badge 
                          className="text-[10px] h-4 px-1.5 border-0"
                          style={{
                            backgroundColor: 'var(--color-accent-green-light)',
                            color: 'var(--color-accent-green)'
                          }}
                        >
                          {Math.round(stage.confidence * 100)}% confidence
                        </Badge>
                      )}
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>

          <div className="pt-3 border-t" style={{ borderColor: 'var(--color-border-light)' }}>
            <div className="text-[10px] space-y-1" style={{ color: 'var(--color-text-muted)' }}>
              <div className="flex items-center gap-1.5">
                <div className="w-1 h-1 rounded-full" style={{ backgroundColor: 'var(--color-accent-blue)' }} />
                <span>1M token context window</span>
              </div>
              <div className="flex items-center gap-1.5">
                <div className="w-1 h-1 rounded-full" style={{ backgroundColor: 'var(--color-accent-blue)' }} />
                <span>Multimodal understanding (vision + audio + text)</span>
              </div>
              <div className="flex items-center gap-1.5">
                <div className="w-1 h-1 rounded-full" style={{ backgroundColor: 'var(--color-accent-blue)' }} />
                <span>Function calling for structured outputs</span>
              </div>
            </div>
          </div>
        </div>
      </PopoverContent>
    </Popover>
  );
}