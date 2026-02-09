"use client";

import { Info, Eye, Brain, Search, Zap, CheckCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

interface GeminiProcessingInfoProps {
  captureData: {
    input?: {
      screenshot_url?: string;
      audio_url?: string;
      text_note?: string;
    };
    classification?: {
      domain?: string;
      intent?: string;
      domain_confidence?: number;
      processing_time_ms?: number;
    };
    research?: {
      triggered?: boolean;
      sources_count?: number;
      processing_time_ms?: number;
    };
    resources?: {
      triggered?: boolean;
      resources_count?: number;
      processing_time_ms?: number;
    };
    execution?: {
      total_actions?: number;
      successful?: number;
      processing_time_ms?: number;
    };
    proactive?: {
      triggered?: boolean;
      processing_time_ms?: number;
    };
  };
}

export function GeminiProcessingInfo({ captureData }: GeminiProcessingInfoProps) {
  const hasScreenshot = !!captureData.input?.screenshot_url;
  const hasAudio = !!captureData.input?.audio_url;
  const hasText = !!captureData.input?.text_note;
  
  const stages = [
    {
      icon: Eye,
      label: "Perception",
      description: hasScreenshot ? "Vision model extracted text from screenshot" : hasAudio ? "Audio model transcribed voice recording" : "Text analysis",
      active: hasScreenshot || hasAudio || hasText,
      time: null,
    },
    {
      icon: Brain,
      label: "Classification",
      description: `Identified as ${captureData.classification?.domain || 'unknown'} domain with ${captureData.classification?.intent || 'unknown'} intent`,
      active: !!captureData.classification,
      time: captureData.classification?.processing_time_ms,
      confidence: captureData.classification?.domain_confidence,
    },
    {
      icon: Search,
      label: "Research",
      description: captureData.research?.triggered 
        ? `Grounded search found ${captureData.research.sources_count || 0} sources`
        : "Not triggered for this capture",
      active: captureData.research?.triggered || false,
      time: captureData.research?.processing_time_ms,
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
          className="h-7 gap-1.5 text-xs backdrop-blur-sm bg-background/50 border border-border/50 hover:bg-background/80 transition-all"
        >
          <Info className="h-3.5 w-3.5" />
          <span>Powered by Gemini 3</span>
        </Button>
      </PopoverTrigger>
      <PopoverContent 
        className="w-96 backdrop-blur-xl bg-background/95 border-border/50" 
        align="start"
      >
        <div className="space-y-4">
          <div>
            <h4 className="font-semibold text-sm mb-1">AI Processing Pipeline</h4>
            <p className="text-xs text-muted-foreground">
              Multi-agent orchestration powered by Google Gemini 3
            </p>
          </div>

          <div className="space-y-3">
            {stages.map((stage, idx) => (
              <div 
                key={idx}
                className={cn(
                  "flex items-start gap-3 p-2.5 rounded-lg transition-all",
                  stage.active 
                    ? "bg-accent/10 border border-accent/20" 
                    : "opacity-40"
                )}
              >
                <div className={cn(
                  "p-1.5 rounded-md",
                  stage.active ? "bg-accent/20" : "bg-muted"
                )}>
                  <stage.icon className={cn(
                    "h-3.5 w-3.5",
                    stage.active ? "text-accent" : "text-muted-foreground"
                  )} />
                </div>
                
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-0.5">
                    <span className="text-xs font-medium">{stage.label}</span>
                    {stage.active && (
                      <CheckCircle className="h-3 w-3 text-green-500" />
                    )}
                  </div>
                  <p className="text-xs text-muted-foreground leading-relaxed">
                    {stage.description}
                  </p>
                  
                  {stage.active && (
                    <div className="flex items-center gap-2 mt-1.5">
                      {stage.time && (
                        <Badge variant="outline" className="text-[10px] h-4 px-1.5">
                          {stage.time}ms
                        </Badge>
                      )}
                      {stage.confidence && (
                        <Badge variant="outline" className="text-[10px] h-4 px-1.5">
                          {Math.round(stage.confidence * 100)}% confidence
                        </Badge>
                      )}
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>

          <div className="pt-3 border-t border-border/50">
            <div className="text-[10px] text-muted-foreground space-y-1">
              <div className="flex items-center gap-1.5">
                <div className="w-1 h-1 rounded-full bg-accent" />
                <span>1M token context window</span>
              </div>
              <div className="flex items-center gap-1.5">
                <div className="w-1 h-1 rounded-full bg-accent" />
                <span>Multimodal understanding (vision + audio + text)</span>
              </div>
              <div className="flex items-center gap-1.5">
                <div className="w-1 h-1 rounded-full bg-accent" />
                <span>Function calling for structured outputs</span>
              </div>
            </div>
          </div>
        </div>
      </PopoverContent>
    </Popover>
  );
}