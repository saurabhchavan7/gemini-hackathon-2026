// components/lifeos/search-chat.tsx
"use client";

import { useState } from "react";
import { Send, Sparkles, Loader2, Briefcase, GraduationCap, DollarSign, Heart, ShoppingCart, Film } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { askQuestion } from "@/lib/api-client";
import { cn } from "@/lib/utils";

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  sources?: Array<{
    id: string;
    title: string;
    summary: string;
    distance: number;
  }>;
  confidence?: string;
}

const DOMAIN_FILTERS = [
  { value: "work_career", label: "Work & Career", icon: Briefcase },
  { value: "education_learning", label: "Learning", icon: GraduationCap },
  { value: "money_finance", label: "Finance", icon: DollarSign },
  { value: "health_wellbeing", label: "Health", icon: Heart },
  { value: "shopping_consumption", label: "Shopping", icon: ShoppingCart },
  { value: "entertainment_leisure", label: "Entertainment", icon: Film },
];

const STARTER_QUESTIONS = [
  "What work tasks do I have?",
  "Show me items with upcoming deadlines",
  "What am I learning about?",
  "Find high priority items",
  "Show me recent captures about fitness",
  "What purchases am I planning?",
];

export function SearchChat() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [selectedDomain, setSelectedDomain] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      role: "user",
      content: input,
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setIsLoading(true);

    try {
      const result = await askQuestion(input, selectedDomain || undefined);

      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: result.answer,
        sources: result.sources,
        confidence: result.confidence,
      };

      setMessages((prev) => [...prev, assistantMessage]);
    } catch (error) {
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: "Sorry, I encountered an error. Please try again.",
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const toggleDomain = (domain: string) => {
    setSelectedDomain(prev => prev === domain ? null : domain);
  };

  return (
    <div className="flex h-full flex-col">
      {/* Chat Messages */}
      <div className="flex-1 overflow-auto p-6">
        {messages.length === 0 ? (
          <div className="flex h-full flex-col items-center justify-center max-w-3xl mx-auto">
            <Sparkles className="h-12 w-12 text-primary/50 mb-4" />
            <h3 className="text-xl font-semibold text-foreground">Ask me anything</h3>
            <p className="mt-2 text-sm text-muted-foreground text-center max-w-md">
              I can answer questions about your captures, find information, and help you discover connections.
            </p>
            
            {/* Prominent Search Input */}
            <div className="mt-8 w-full max-w-2xl">
              <form onSubmit={handleSubmit} className="relative">
                <Input
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  placeholder="Ask a question about your captures..."
                  disabled={isLoading}
                  className="w-full h-14 px-6 text-base pr-14 shadow-lg border-2 focus-visible:ring-2"
                />
                <Button 
                  type="submit" 
                  disabled={isLoading || !input.trim()}
                  size="lg"
                  className="absolute right-2 top-2 h-10"
                >
                  {isLoading ? (
                    <Loader2 className="h-5 w-5 animate-spin" />
                  ) : (
                    <Send className="h-5 w-5" />
                  )}
                </Button>
              </form>
            </div>

            {/* Domain Filter Buttons */}
            <div className="mt-10 w-full max-w-2xl">
              <div className="grid grid-cols-3 gap-3">
                {DOMAIN_FILTERS.map((domain) => {
                  const Icon = domain.icon;
                  return (
                    <button
                      key={domain.value}
                      onClick={() => toggleDomain(domain.value)}
                      className={cn(
                        "flex items-center gap-2 px-4 py-3 rounded-lg border text-sm font-medium transition-all",
                        selectedDomain === domain.value
                          ? "border-primary bg-primary/10 text-primary"
                          : "border-border bg-card hover:bg-accent hover:border-accent-foreground/20"
                      )}
                    >
                      <Icon className="h-4 w-4" />
                      {domain.label}
                    </button>
                  );
                })}
              </div>
              {selectedDomain && (
                <div className="mt-3 flex items-center justify-center gap-2">
                  <Badge variant="secondary" className="text-xs">
                    Searching in: {DOMAIN_FILTERS.find(d => d.value === selectedDomain)?.label}
                  </Badge>
                  <button
                    onClick={() => setSelectedDomain(null)}
                    className="text-xs text-muted-foreground hover:text-foreground"
                  >
                    Clear
                  </button>
                </div>
              )}
            </div>

            {/* Starter Questions */}
            <div className="mt-10 w-full max-w-2xl space-y-3">
              <p className="text-xs text-muted-foreground text-center">Try asking:</p>
              <div className="grid grid-cols-2 gap-2">
                {STARTER_QUESTIONS.map((question) => (
                  <Button
                    key={question}
                    variant="outline"
                    size="sm"
                    onClick={() => setInput(question)}
                    className="text-xs text-left justify-start h-auto py-2 px-3"
                  >
                    {question}
                  </Button>
                ))}
              </div>
            </div>
          </div>
        ) : (
          <div className="space-y-4 max-w-3xl mx-auto">
            {messages.map((message) => (
              <div
                key={message.id}
                className={`flex ${
                  message.role === "user" ? "justify-end" : "justify-start"
                }`}
              >
                <div
                  className={`max-w-[80%] rounded-lg p-4 ${
                    message.role === "user"
                      ? "bg-primary text-primary-foreground"
                      : "bg-muted"
                  }`}
                >
                  <p className="text-sm whitespace-pre-wrap">{message.content}</p>

                  {/* Sources */}
                  {message.sources && message.sources.length > 0 && (
                    <div className="mt-3 space-y-2">
                      <p className="text-xs font-medium opacity-70">Sources:</p>
                      {message.sources.map((source) => (
                        <Card key={source.id} className="p-2 bg-card/50">
                          <p className="text-xs font-medium">{source.title}</p>
                          {source.summary && (
                            <p className="text-xs text-muted-foreground mt-1 line-clamp-2">
                              {source.summary}
                            </p>
                          )}
                        </Card>
                      ))}
                    </div>
                  )}

                  {/* Confidence Badge */}
                  {message.confidence && (
                    <div className="mt-2">
                      <Badge
                        variant="outline"
                        className={cn(
                          "text-xs",
                          message.confidence === "high" && "border-green-500 text-green-700",
                          message.confidence === "medium" && "border-yellow-500 text-yellow-700",
                          message.confidence === "low" && "border-gray-500 text-gray-700"
                        )}
                      >
                        {message.confidence} confidence
                      </Badge>
                    </div>
                  )}
                </div>
              </div>
            ))}

            {isLoading && (
              <div className="flex justify-start">
                <div className="max-w-[80%] rounded-lg bg-muted p-4">
                  <div className="flex items-center gap-2">
                    <Loader2 className="h-4 w-4 animate-spin" />
                    <p className="text-sm text-muted-foreground">Searching your captures...</p>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Bottom Input (when chat started) */}
      {messages.length > 0 && (
        <div className="border-t border-border p-4">
          <div className="max-w-3xl mx-auto">
            {selectedDomain && (
              <div className="mb-3 flex items-center gap-2">
                <Badge variant="secondary" className="text-xs">
                  Searching in: {DOMAIN_FILTERS.find(d => d.value === selectedDomain)?.label}
                </Badge>
                <button
                  onClick={() => setSelectedDomain(null)}
                  className="text-xs text-muted-foreground hover:text-foreground"
                >
                  Clear
                </button>
              </div>
            )}
            <form onSubmit={handleSubmit} className="flex gap-2">
              <Input
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder="Ask a question about your captures..."
                disabled={isLoading}
                className="flex-1"
              />
              <Button type="submit" disabled={isLoading || !input.trim()}>
                {isLoading ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <Send className="h-4 w-4" />
                )}
              </Button>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}