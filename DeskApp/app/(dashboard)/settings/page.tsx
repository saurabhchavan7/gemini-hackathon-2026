"use client";

import { useState, useEffect } from "react";
import {
  Settings,
  Keyboard,
  Moon,
  Bell,
  Shield,
  Eye,
  Chrome,
  MessageSquare,
  Mail,
  FileText,
  Camera,
} from "lucide-react";
import { Card } from "@/components/ui/card";
import { Switch } from "@/components/ui/switch";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Kbd } from "@/components/ui/kbd";
import { getSettings, updateSettings } from "@/lib/api";
import type { UserSettings } from "@/types/lifeos";

export default function SettingsPage() {
  const [settings, setSettings] = useState<UserSettings | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    async function loadSettings() {
      setIsLoading(true);
      const data = await getSettings();
      setSettings(data);
      setIsLoading(false);
    }
    loadSettings();
  }, []);

  const handleToggle = async (key: keyof UserSettings, value: boolean) => {
    if (!settings) return;
    const updated = await updateSettings({ [key]: value });
    setSettings(updated);
  };

  const handleSourceToggle = async (source: keyof UserSettings["captureSources"], value: boolean) => {
    if (!settings) return;
    const updated = await updateSettings({
      captureSources: { ...settings.captureSources, [source]: value },
    });
    setSettings(updated);
  };

  const handleNotificationCapChange = async (value: string) => {
    if (!settings) return;
    const cap = parseInt(value, 10);
    if (isNaN(cap) || cap < 1) return;
    const updated = await updateSettings({ notificationCap: cap });
    setSettings(updated);
  };

  if (isLoading || !settings) {
    return (
      <div className="flex h-full items-center justify-center">
        <div className="flex flex-col items-center gap-3 text-muted-foreground">
          <div className="h-8 w-8 animate-spin rounded-full border-2 border-muted border-t-accent" />
          <span className="text-sm">Loading settings...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="flex h-full flex-col">
      {/* Header */}
      <div className="border-b border-border px-6 py-4">
        <div className="flex items-center gap-3">
          <Settings className="h-5 w-5 text-muted-foreground" />
          <h1 className="text-xl font-semibold text-foreground">Settings</h1>
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-auto p-6">
        <div className="max-w-2xl space-y-6">
          {/* Hotkey Section */}
          <Card className="bg-card p-6">
            <div className="flex items-center gap-3 mb-4">
              <Keyboard className="h-5 w-5 text-accent" />
              <h2 className="text-lg font-semibold text-card-foreground">Keyboard Shortcuts</h2>
            </div>
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-foreground">Global Capture</p>
                  <p className="text-xs text-muted-foreground">
                    Capture current screen from anywhere
                  </p>
                </div>
                <div className="flex items-center gap-1">
                  <Kbd>Ctrl</Kbd>
                  <Kbd>Shift</Kbd>
                  <Kbd>L</Kbd>
                </div>
              </div>
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-foreground">Command Palette</p>
                  <p className="text-xs text-muted-foreground">
                    Quick navigation and commands
                  </p>
                </div>
                <div className="flex items-center gap-1">
                  <Kbd>Ctrl</Kbd>
                  <Kbd>K</Kbd>
                </div>
              </div>
            </div>
          </Card>

          {/* Quiet Hours & DND */}
          <Card className="bg-card p-6">
            <div className="flex items-center gap-3 mb-4">
              <Moon className="h-5 w-5 text-accent" />
              <h2 className="text-lg font-semibold text-card-foreground">Quiet Hours</h2>
            </div>
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-foreground">Do Not Disturb</p>
                  <p className="text-xs text-muted-foreground">
                    Pause all notifications
                  </p>
                </div>
                <Switch
                  checked={settings.dndEnabled}
                  onCheckedChange={(checked) => handleToggle("dndEnabled", checked)}
                  aria-label="Toggle do not disturb"
                />
              </div>
              <div className="grid gap-4 sm:grid-cols-2">
                <div className="space-y-2">
                  <Label htmlFor="quiet-start" className="text-sm">Quiet hours start</Label>
                  <Input
                    id="quiet-start"
                    type="time"
                    value={settings.quietHoursStart}
                    onChange={(e) => updateSettings({ quietHoursStart: e.target.value })}
                    className="bg-muted/50"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="quiet-end" className="text-sm">Quiet hours end</Label>
                  <Input
                    id="quiet-end"
                    type="time"
                    value={settings.quietHoursEnd}
                    onChange={(e) => updateSettings({ quietHoursEnd: e.target.value })}
                    className="bg-muted/50"
                  />
                </div>
              </div>
            </div>
          </Card>

          {/* Notifications */}
          <Card className="bg-card p-6">
            <div className="flex items-center gap-3 mb-4">
              <Bell className="h-5 w-5 text-accent" />
              <h2 className="text-lg font-semibold text-card-foreground">Notifications</h2>
            </div>
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-foreground">Daily notification limit</p>
                  <p className="text-xs text-muted-foreground">
                    Maximum notifications per day
                  </p>
                </div>
                <Input
                  type="number"
                  min={1}
                  max={50}
                  value={settings.notificationCap}
                  onChange={(e) => handleNotificationCapChange(e.target.value)}
                  className="w-20 bg-muted/50"
                  aria-label="Notification cap"
                />
              </div>
            </div>
          </Card>

          {/* Capture Sources */}
          <Card className="bg-card p-6">
            <div className="flex items-center gap-3 mb-4">
              <Camera className="h-5 w-5 text-accent" />
              <h2 className="text-lg font-semibold text-card-foreground">Capture Sources</h2>
            </div>
            <div className="space-y-4">
              {[
                { key: "browser" as const, label: "Browser", icon: Chrome, description: "Capture from web browsers" },
                { key: "slack" as const, label: "Slack", icon: MessageSquare, description: "Capture Slack messages" },
                { key: "email" as const, label: "Email", icon: Mail, description: "Capture email content" },
                { key: "documents" as const, label: "Documents", icon: FileText, description: "Capture from documents" },
                { key: "screenshots" as const, label: "Screenshots", icon: Camera, description: "Auto-capture screenshots" },
              ].map((source) => (
                <div key={source.key} className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <source.icon className="h-4 w-4 text-muted-foreground" />
                    <div>
                      <p className="text-sm font-medium text-foreground">{source.label}</p>
                      <p className="text-xs text-muted-foreground">{source.description}</p>
                    </div>
                  </div>
                  <Switch
                    checked={settings.captureSources[source.key]}
                    onCheckedChange={(checked) => handleSourceToggle(source.key, checked)}
                    aria-label={`Toggle ${source.label} capture`}
                  />
                </div>
              ))}
            </div>
          </Card>

          {/* Privacy */}
          <Card className="bg-card p-6">
            <div className="flex items-center gap-3 mb-4">
              <Shield className="h-5 w-5 text-accent" />
              <h2 className="text-lg font-semibold text-card-foreground">Privacy</h2>
            </div>
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <div className="flex items-center gap-2">
                    <p className="text-sm font-medium text-foreground">Local-First Storage</p>
                    <Badge variant="secondary" className="text-xs">Recommended</Badge>
                  </div>
                  <p className="text-xs text-muted-foreground">
                    Keep all data on your device. Nothing is sent to external servers.
                  </p>
                </div>
                <Switch
                  checked={settings.localFirst}
                  onCheckedChange={(checked) => handleToggle("localFirst", checked)}
                  aria-label="Toggle local-first storage"
                />
              </div>
            </div>
          </Card>

          {/* Accessibility */}
          <Card className="bg-card p-6">
            <div className="flex items-center gap-3 mb-4">
              <Eye className="h-5 w-5 text-accent" />
              <h2 className="text-lg font-semibold text-card-foreground">Accessibility</h2>
            </div>
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-foreground">Reduce Motion</p>
                  <p className="text-xs text-muted-foreground">
                    Minimize animations and transitions
                  </p>
                </div>
                <Switch
                  checked={settings.accessibilityReducedMotion}
                  onCheckedChange={(checked) => handleToggle("accessibilityReducedMotion", checked)}
                  aria-label="Toggle reduced motion"
                />
              </div>
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-foreground">High Contrast</p>
                  <p className="text-xs text-muted-foreground">
                    Increase contrast for better visibility
                  </p>
                </div>
                <Switch
                  checked={settings.accessibilityHighContrast}
                  onCheckedChange={(checked) => handleToggle("accessibilityHighContrast", checked)}
                  aria-label="Toggle high contrast"
                />
              </div>
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
}
