"use client";

import { useState, useEffect } from "react";
import { Sparkles, Link2, Network, ChevronRight } from "lucide-react";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { listClusters, listConnections, listCaptures } from "@/lib/api";
import type { ThemeCluster, ConnectionEdge, CaptureItem } from "@/types/lifeos";

export default function SynthesisPage() {
  const [clusters, setClusters] = useState<ThemeCluster[]>([]);
  const [connections, setConnections] = useState<ConnectionEdge[]>([]);
  const [captures, setCaptures] = useState<CaptureItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    async function loadData() {
      setIsLoading(true);
      const [clustersData, connectionsData, capturesData] = await Promise.all([
        listClusters(),
        listConnections(),
        listCaptures(),
      ]);
      setClusters(clustersData);
      setConnections(connectionsData);
      setCaptures(capturesData);
      setIsLoading(false);
    }
    loadData();
  }, []);

  const getCaptureById = (id: string) => captures.find((c) => c.id === id);

  if (isLoading) {
    return (
      <div className="flex h-full items-center justify-center">
        <div className="flex flex-col items-center gap-3 text-muted-foreground">
          <div className="h-8 w-8 animate-spin rounded-full border-2 border-muted border-t-accent" />
          <span className="text-sm">Analyzing patterns...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="flex h-full flex-col">
      {/* Header */}
      <div className="border-b border-border px-6 py-4">
        <div className="flex items-center gap-3">
          <Sparkles className="h-5 w-5 text-muted-foreground" />
          <h1 className="text-xl font-semibold text-foreground">Synthesis</h1>
        </div>
        <p className="mt-1 text-sm text-muted-foreground">
          Discover patterns, themes, and connections in your captured knowledge
        </p>
      </div>

      {/* Content */}
      <Tabs defaultValue="clusters" className="flex-1 flex flex-col">
        <div className="border-b border-border px-6">
          <TabsList className="h-12 bg-transparent p-0 gap-6">
            <TabsTrigger
              value="clusters"
              className="h-12 gap-2 rounded-none border-b-2 border-transparent px-0 data-[state=active]:border-accent data-[state=active]:bg-transparent data-[state=active]:shadow-none"
            >
              <Sparkles className="h-4 w-4" />
              Theme Clusters
              <Badge variant="secondary" className="ml-1">
                {clusters.length}
              </Badge>
            </TabsTrigger>
            <TabsTrigger
              value="connections"
              className="h-12 gap-2 rounded-none border-b-2 border-transparent px-0 data-[state=active]:border-accent data-[state=active]:bg-transparent data-[state=active]:shadow-none"
            >
              <Link2 className="h-4 w-4" />
              Connections
              <Badge variant="secondary" className="ml-1">
                {connections.length}
              </Badge>
            </TabsTrigger>
            <TabsTrigger
              value="map"
              className="h-12 gap-2 rounded-none border-b-2 border-transparent px-0 data-[state=active]:border-accent data-[state=active]:bg-transparent data-[state=active]:shadow-none"
            >
              <Network className="h-4 w-4" />
              Knowledge Map
            </TabsTrigger>
          </TabsList>
        </div>

        {/* Theme Clusters */}
        <TabsContent value="clusters" className="flex-1 overflow-auto p-6 mt-0">
          <div className="grid gap-4 md:grid-cols-2">
            {clusters.map((cluster) => (
              <Card key={cluster.id} className="bg-card p-5">
                <div className="flex items-start gap-3">
                  <div
                    className="h-3 w-3 rounded-full mt-1.5"
                    style={{ backgroundColor: cluster.color }}
                  />
                  <div className="flex-1">
                    <h3 className="text-base font-medium text-card-foreground">
                      {cluster.name}
                    </h3>
                    <p className="mt-1 text-sm text-muted-foreground">
                      {cluster.description}
                    </p>
                    <div className="mt-4 space-y-2">
                      <p className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
                        Related Captures
                      </p>
                      {cluster.captureIds.map((captureId) => {
                        const capture = getCaptureById(captureId);
                        if (!capture) return null;
                        return (
                          <div
                            key={captureId}
                            className="flex items-center gap-2 rounded-md bg-muted/50 px-3 py-2"
                          >
                            <span className="text-sm text-foreground truncate">
                              {capture.title}
                            </span>
                            <ChevronRight className="h-3 w-3 ml-auto text-muted-foreground" />
                          </div>
                        );
                      })}
                    </div>
                    <div className="mt-4 flex items-center gap-2 text-xs text-muted-foreground">
                      <span>Updated {cluster.updatedAt.toLocaleDateString()}</span>
                    </div>
                  </div>
                </div>
              </Card>
            ))}
          </div>
        </TabsContent>

        {/* Connections */}
        <TabsContent value="connections" className="flex-1 overflow-auto p-6 mt-0">
          <div className="space-y-3">
            {connections.map((connection) => {
              const source = getCaptureById(connection.sourceId);
              const target = getCaptureById(connection.targetId);
              if (!source || !target) return null;

              return (
                <Card key={connection.id} className="bg-card p-4">
                  <div className="flex items-center gap-4">
                    {/* Source */}
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-card-foreground truncate">
                        {source.title}
                      </p>
                      <p className="text-xs text-muted-foreground">{source.sourceApp}</p>
                    </div>

                    {/* Connection indicator */}
                    <div className="flex flex-col items-center gap-1 px-4">
                      <div className="flex items-center gap-2">
                        <div className="h-px w-8 bg-border" />
                        <Badge variant="outline" className="text-xs whitespace-nowrap">
                          {connection.relationshipType.replace("-", " ")}
                        </Badge>
                        <div className="h-px w-8 bg-border" />
                      </div>
                      <div className="flex items-center gap-1">
                        <div
                          className="h-1.5 rounded-full bg-accent"
                          style={{ width: `${connection.strength * 40}px` }}
                        />
                        <span className="text-xs text-muted-foreground">
                          {Math.round(connection.strength * 100)}%
                        </span>
                      </div>
                    </div>

                    {/* Target */}
                    <div className="flex-1 min-w-0 text-right">
                      <p className="text-sm font-medium text-card-foreground truncate">
                        {target.title}
                      </p>
                      <p className="text-xs text-muted-foreground">{target.sourceApp}</p>
                    </div>
                  </div>
                </Card>
              );
            })}
          </div>
        </TabsContent>

        {/* Knowledge Map Placeholder */}
        <TabsContent value="map" className="flex-1 overflow-auto p-6 mt-0">
          <Card className="bg-card h-full min-h-[400px] flex flex-col items-center justify-center">
            <div className="relative w-full max-w-md aspect-square">
              {/* Simple node visualization */}
              <div className="absolute inset-0">
                {/* Center node */}
                <div className="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2">
                  <div className="h-16 w-16 rounded-full bg-accent/20 flex items-center justify-center">
                    <Network className="h-8 w-8 text-accent" />
                  </div>
                </div>

                {/* Orbiting nodes */}
                {clusters.map((cluster, i) => {
                  const angle = (i / clusters.length) * 2 * Math.PI - Math.PI / 2;
                  const radius = 120;
                  const x = Math.cos(angle) * radius;
                  const y = Math.sin(angle) * radius;

                  return (
                    <div
                      key={cluster.id}
                      className="absolute left-1/2 top-1/2"
                      style={{
                        transform: `translate(calc(-50% + ${x}px), calc(-50% + ${y}px))`,
                      }}
                    >
                      {/* Connection line */}
                      <svg
                        className="absolute"
                        style={{
                          left: "50%",
                          top: "50%",
                          width: `${Math.abs(x) + 20}px`,
                          height: `${Math.abs(y) + 20}px`,
                          transform: `translate(${x < 0 ? x : -10}px, ${y < 0 ? y : -10}px)`,
                          overflow: "visible",
                        }}
                      >
                        <line
                          x1={x < 0 ? Math.abs(x) + 10 : 10}
                          y1={y < 0 ? Math.abs(y) + 10 : 10}
                          x2={x < 0 ? 10 : Math.abs(x) + 10}
                          y2={y < 0 ? 10 : Math.abs(y) + 10}
                          stroke="currentColor"
                          strokeWidth="1"
                          className="text-border"
                          strokeDasharray="4 4"
                        />
                      </svg>

                      {/* Node */}
                      <div
                        className="h-12 w-12 rounded-full flex items-center justify-center cursor-pointer transition-transform hover:scale-110"
                        style={{ backgroundColor: `${cluster.color}20` }}
                        title={cluster.name}
                      >
                        <div
                          className="h-4 w-4 rounded-full"
                          style={{ backgroundColor: cluster.color }}
                        />
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
            <div className="mt-8 text-center">
              <h3 className="text-lg font-medium text-card-foreground">Knowledge Map</h3>
              <p className="mt-1 text-sm text-muted-foreground max-w-sm">
                Visual representation of how your captured knowledge connects. Click on nodes to explore themes.
              </p>
            </div>

            {/* Legend */}
            <div className="mt-6 flex flex-wrap justify-center gap-4">
              {clusters.map((cluster) => (
                <div key={cluster.id} className="flex items-center gap-2">
                  <div
                    className="h-3 w-3 rounded-full"
                    style={{ backgroundColor: cluster.color }}
                  />
                  <span className="text-xs text-muted-foreground">{cluster.name}</span>
                </div>
              ))}
            </div>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
