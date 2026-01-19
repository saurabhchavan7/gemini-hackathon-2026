"use client";

import { useState, useEffect } from "react";
import {
  FileText,
  Download,
  Share2,
  Calendar,
  Sparkles,
  Link2,
  AlertTriangle,
  CheckCircle2,
  ChevronRight,
} from "lucide-react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { listDigestReports, listCaptures } from "@/lib/api";
import type { DigestReport, CaptureItem } from "@/types/lifeos";

export default function DigestPage() {
  const [reports, setReports] = useState<DigestReport[]>([]);
  const [captures, setCaptures] = useState<CaptureItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    async function loadData() {
      setIsLoading(true);
      const [reportsData, capturesData] = await Promise.all([
        listDigestReports(),
        listCaptures(),
      ]);
      setReports(reportsData);
      setCaptures(capturesData);
      setIsLoading(false);
    }
    loadData();
  }, []);

  const currentReport = reports[0];

  const handleExport = (format: "pdf" | "markdown") => {
    // UI-only export simulation
    alert(`Export to ${format.toUpperCase()} - Feature coming soon!`);
  };

  if (isLoading) {
    return (
      <div className="flex h-full items-center justify-center">
        <div className="flex flex-col items-center gap-3 text-muted-foreground">
          <div className="h-8 w-8 animate-spin rounded-full border-2 border-muted border-t-accent" />
          <span className="text-sm">Generating digest...</span>
        </div>
      </div>
    );
  }

  if (!currentReport) {
    return (
      <div className="flex h-full flex-col items-center justify-center text-center">
        <FileText className="h-12 w-12 text-muted-foreground/50" />
        <h3 className="mt-4 text-lg font-medium text-foreground">No digests yet</h3>
        <p className="mt-1 text-sm text-muted-foreground">
          Weekly digests will appear here once you have enough captures
        </p>
      </div>
    );
  }

  return (
    <div className="flex h-full flex-col">
      {/* Header */}
      <div className="border-b border-border px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <FileText className="h-5 w-5 text-muted-foreground" />
            <h1 className="text-xl font-semibold text-foreground">Weekly Digest</h1>
          </div>
          <div className="flex items-center gap-2">
            <Button variant="outline" size="sm" className="gap-2 bg-transparent" onClick={() => handleExport("pdf")}>
              <Download className="h-3.5 w-3.5" />
              Export PDF
            </Button>
            <Button variant="outline" size="sm" className="gap-2 bg-transparent" onClick={() => handleExport("markdown")}>
              <Share2 className="h-3.5 w-3.5" />
              Export Markdown
            </Button>
          </div>
        </div>
        <div className="mt-2 flex items-center gap-2 text-sm text-muted-foreground">
          <Calendar className="h-4 w-4" />
          <span>
            {currentReport.weekStart.toLocaleDateString()} - {currentReport.weekEnd.toLocaleDateString()}
          </span>
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-auto p-6">
        <div className="max-w-3xl space-y-6">
          {/* Summary Section */}
          <Card className="bg-card p-6">
            <div className="flex items-start gap-4">
              <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-accent/10">
                <FileText className="h-5 w-5 text-accent" />
              </div>
              <div>
                <h2 className="text-lg font-semibold text-card-foreground">Weekly Summary</h2>
                <p className="mt-2 text-sm text-muted-foreground leading-relaxed">
                  {currentReport.summary}
                </p>
              </div>
            </div>
          </Card>

          {/* Themes Section */}
          <Card className="bg-card p-6">
            <div className="flex items-center gap-3 mb-4">
              <Sparkles className="h-5 w-5 text-accent" />
              <h2 className="text-lg font-semibold text-card-foreground">Key Themes</h2>
            </div>
            <div className="grid gap-3 sm:grid-cols-2">
              {currentReport.themes.map((theme) => (
                <div
                  key={theme.id}
                  className="flex items-center gap-3 rounded-lg bg-muted/50 p-3"
                >
                  <div
                    className="h-3 w-3 rounded-full shrink-0"
                    style={{ backgroundColor: theme.color }}
                  />
                  <div className="min-w-0">
                    <p className="text-sm font-medium text-foreground">{theme.name}</p>
                    <p className="text-xs text-muted-foreground truncate">
                      {theme.captureIds.length} captures
                    </p>
                  </div>
                  <ChevronRight className="h-4 w-4 ml-auto text-muted-foreground" />
                </div>
              ))}
            </div>
          </Card>

          {/* Missed Connections */}
          {currentReport.missedConnections.length > 0 && (
            <Card className="bg-card p-6">
              <div className="flex items-center gap-3 mb-4">
                <Link2 className="h-5 w-5 text-warning" />
                <h2 className="text-lg font-semibold text-card-foreground">
                  Potential Connections
                </h2>
                <Badge variant="secondary">{currentReport.missedConnections.length}</Badge>
              </div>
              <p className="text-sm text-muted-foreground mb-4">
                We found potential links between your captures that you might have missed
              </p>
              {currentReport.missedConnections.map((conn) => {
                const source = captures.find((c) => c.id === conn.sourceId);
                const target = captures.find((c) => c.id === conn.targetId);
                if (!source || !target) return null;
                return (
                  <div
                    key={conn.id}
                    className="flex items-center gap-3 rounded-lg bg-muted/50 p-3"
                  >
                    <span className="text-sm text-foreground truncate flex-1">
                      {source.title}
                    </span>
                    <Badge variant="outline" className="shrink-0 text-xs">
                      {conn.relationshipType}
                    </Badge>
                    <span className="text-sm text-foreground truncate flex-1 text-right">
                      {target.title}
                    </span>
                  </div>
                );
              })}
            </Card>
          )}

          {/* Expiring Items */}
          {currentReport.expiringItems.length > 0 && (
            <Card className="bg-card p-6">
              <div className="flex items-center gap-3 mb-4">
                <AlertTriangle className="h-5 w-5 text-destructive" />
                <h2 className="text-lg font-semibold text-card-foreground">
                  Expiring Soon
                </h2>
                <Badge variant="destructive">{currentReport.expiringItems.length}</Badge>
              </div>
              <div className="space-y-2">
                {currentReport.expiringItems.map((item) => (
                  <div
                    key={item.id}
                    className="flex items-center justify-between rounded-lg bg-destructive/10 p-3"
                  >
                    <span className="text-sm text-foreground">{item.title}</span>
                    <span className="text-xs text-destructive">
                      Due {item.deadline?.toLocaleDateString()}
                    </span>
                  </div>
                ))}
              </div>
            </Card>
          )}

          {/* Suggested Actions */}
          <Card className="bg-card p-6">
            <div className="flex items-center gap-3 mb-4">
              <CheckCircle2 className="h-5 w-5 text-success" />
              <h2 className="text-lg font-semibold text-card-foreground">
                Suggested Actions
              </h2>
            </div>
            <div className="space-y-2">
              {currentReport.suggestedActions.map((action, i) => (
                <div
                  key={i}
                  className="flex items-start gap-3 rounded-lg bg-success/10 p-3"
                >
                  <div className="h-5 w-5 shrink-0 rounded-full bg-success/20 flex items-center justify-center text-xs font-medium text-success">
                    {i + 1}
                  </div>
                  <span className="text-sm text-foreground">{action}</span>
                </div>
              ))}
            </div>
          </Card>

          {/* Generation Info */}
          <p className="text-xs text-muted-foreground text-center">
            Generated on {currentReport.createdAt.toLocaleDateString()} at{" "}
            {currentReport.createdAt.toLocaleTimeString()}
          </p>
        </div>
      </div>
    </div>
  );
}
