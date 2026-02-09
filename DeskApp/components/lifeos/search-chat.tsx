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
    { value: "work_career", label: "Work & Career", icon: Briefcase, color: "blue" },
    { value: "education_learning", label: "Learning", icon: GraduationCap, color: "green" },
    { value: "money_finance", label: "Finance", icon: DollarSign, color: "green" },
    { value: "health_wellbeing", label: "Health", icon: Heart, color: "red" },
    { value: "shopping_consumption", label: "Shopping", icon: ShoppingCart, color: "purple" },
    { value: "entertainment_leisure", label: "Entertainment", icon: Film, color: "orange" },
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
        <div className="flex h-full flex-col items-center justify-center max-w-3xl mx-auto px-6">
            {/* Add spacer div to push content down */}
            <div className="flex-1 max-h-24"></div>
            
            <h3 className="text-3xl font-semibold mb-4" style={{ color: 'var(--color-text-primary)' }}>
                Ask me anything
            </h3>
            {/* Subtitle */}
            <p className="text-base text-center mb-12" style={{ color: 'var(--color-text-secondary)' }}>
                I can answer questions about your captures, find information, and help you discover connections.
            </p>

                        {/* Large Search Input */}
                        <div className="w-full max-w-2xl mb-8">
                            <form onSubmit={handleSubmit} className="relative">
                                <div className="relative">
                                    <div className="absolute left-5 top-1/2 -translate-y-1/2" style={{ color: 'var(--color-text-muted)' }}>
                                        <svg className="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                            <circle cx="11" cy="11" r="8" />
                                            <path d="m21 21-4.35-4.35" />
                                        </svg>
                                    </div>
                                    <Input
                                        value={input}
                                        onChange={(e) => setInput(e.target.value)}
                                        placeholder="Ask a question about your captures..."
                                        disabled={isLoading}
                                        className="w-full h-14 pl-14 pr-14 text-base rounded-full shadow-sm border"
                                        style={{
                                            backgroundColor: 'var(--color-bg-card)',
                                            borderColor: 'var(--color-border-light)'
                                        }}
                                    />
                                    <Button
                                        type="submit"
                                        disabled={isLoading || !input.trim()}
                                        className="absolute right-2 top-1/2 -translate-y-1/2 h-10 w-10 p-0 rounded-full"
                                        style={{
                                            backgroundColor: 'var(--color-accent-blue)',
                                            color: '#ffffff'
                                        }}
                                    >
                                        {isLoading ? (
                                            <Loader2 className="h-5 w-5 animate-spin" />
                                        ) : (
                                            <Send className="h-5 w-5" />
                                        )}
                                    </Button>
                                </div>
                            </form>
                        </div>

                        {/* Domain Filter Pills */}
                        <div className="w-full max-w-2xl mb-12">
  <div className="flex flex-col items-center gap-3">
    {/* First row - 4 pills */}
    <div className="flex items-center gap-3">
      {DOMAIN_FILTERS.slice(0, 4).map((domain) => {
        const Icon = domain.icon;
        const isSelected = selectedDomain === domain.value;

        const colors: Record<string, { bg: string, text: string }> = {
          blue: { bg: 'var(--color-accent-blue-light)', text: 'var(--color-accent-blue)' },
          green: { bg: 'var(--color-accent-green-light)', text: 'var(--color-accent-green)' },
          red: { bg: 'var(--color-accent-red-light)', text: 'var(--color-accent-red)' },
          orange: { bg: 'var(--color-accent-orange-light)', text: 'var(--color-accent-orange)' },
          purple: { bg: '#f3e8ff', text: '#9333ea' }
        };

        const colorScheme = colors[domain.color];

        return (
          <button
            key={domain.value}
            onClick={() => toggleDomain(domain.value)}
            className="flex items-center gap-2 px-4 py-2 rounded-full text-sm font-medium transition-all"
            style={{
              backgroundColor: isSelected ? colorScheme.bg : 'transparent',
              color: colorScheme.text,
              border: isSelected ? 'none' : '1px solid var(--color-border-light)'
            }}
            onMouseEnter={(e) => {
              if (!isSelected) {
                e.currentTarget.style.backgroundColor = 'var(--color-bg-tertiary)';
              }
            }}
            onMouseLeave={(e) => {
              if (!isSelected) {
                e.currentTarget.style.backgroundColor = 'transparent';
              }
            }}
          >
            <Icon className="h-4 w-4" />
            {domain.label}
          </button>
        );
      })}
    </div>

    {/* Second row - 2 pills */}
    <div className="flex items-center gap-3">
      {DOMAIN_FILTERS.slice(4, 6).map((domain) => {
        const Icon = domain.icon;
        const isSelected = selectedDomain === domain.value;

        const colors: Record<string, { bg: string, text: string }> = {
          blue: { bg: 'var(--color-accent-blue-light)', text: 'var(--color-accent-blue)' },
          green: { bg: 'var(--color-accent-green-light)', text: 'var(--color-accent-green)' },
          red: { bg: 'var(--color-accent-red-light)', text: 'var(--color-accent-red)' },
          orange: { bg: 'var(--color-accent-orange-light)', text: 'var(--color-accent-orange)' },
          purple: { bg: '#f3e8ff', text: '#9333ea' }
        };

        const colorScheme = colors[domain.color];

        return (
          <button
            key={domain.value}
            onClick={() => toggleDomain(domain.value)}
            className="flex items-center gap-2 px-4 py-2 rounded-full text-sm font-medium transition-all"
            style={{
              backgroundColor: isSelected ? colorScheme.bg : 'transparent',
              color: colorScheme.text,
              border: isSelected ? 'none' : '1px solid var(--color-border-light)'
            }}
            onMouseEnter={(e) => {
              if (!isSelected) {
                e.currentTarget.style.backgroundColor = 'var(--color-bg-tertiary)';
              }
            }}
            onMouseLeave={(e) => {
              if (!isSelected) {
                e.currentTarget.style.backgroundColor = 'transparent';
              }
            }}
          >
            <Icon className="h-4 w-4" />
            {domain.label}
          </button>
        );
      })}
    </div>
  </div>
</div>

                        {/* Try Asking Label */}
                        <p className="text-xs font-medium text-center uppercase tracking-wider mb-6" style={{ color: 'var(--color-text-muted)' }}>
                            TRY ASKING
                        </p>

                        {/* Starter Questions */}
                        <div className="w-full max-w-3xl">
                            <div className="grid grid-cols-2 gap-4">
                                {STARTER_QUESTIONS.map((question) => (
                                    <button
                                        key={question}
                                        onClick={() => setInput(question)}
                                        className="text-left px-5 py-4 rounded-xl transition-all text-sm"
                                        style={{
                                            backgroundColor: 'var(--color-bg-card)',
                                            color: 'var(--color-text-primary)',
                                            border: '1px solid var(--color-border-light)'
                                        }}
                                        onMouseEnter={(e) => {
                                            e.currentTarget.style.boxShadow = '0 2px 8px rgba(0,0,0,0.08)';
                                        }}
                                        onMouseLeave={(e) => {
                                            e.currentTarget.style.boxShadow = 'none';
                                        }}
                                    >
                                        {question}
                                    </button>
                                ))}
                            </div>
                        </div>
                    </div>
                ) : (
                    <div className="space-y-4 max-w-3xl mx-auto">
                        {messages.map((message) => (
                            <div
                                key={message.id}
                                className={`flex ${message.role === "user" ? "justify-end" : "justify-start"}`}
                            >
                                <div
                                    className="max-w-[80%] rounded-lg p-4"
                                    style={{
                                        backgroundColor: message.role === "user"
                                            ? 'var(--color-accent-blue)'
                                            : 'var(--color-bg-card)',
                                        color: message.role === "user"
                                            ? '#ffffff'
                                            : 'var(--color-text-primary)'
                                    }}
                                >
                                    <p className="text-sm whitespace-pre-wrap">{message.content}</p>

                                    {/* Sources */}
                                    {message.sources && message.sources.length > 0 && (
                                        <div className="mt-3 space-y-2">
                                            <p className="text-xs font-medium opacity-70">Sources:</p>
                                            {message.sources.map((source) => (
                                                <div key={source.id} className="p-2 rounded border" style={{
                                                    backgroundColor: 'var(--color-bg-secondary)',
                                                    borderColor: 'var(--color-border-light)'
                                                }}>
                                                    <p className="text-xs font-medium">{source.title}</p>
                                                    {source.summary && (
                                                        <p className="text-xs mt-1 line-clamp-2" style={{ color: 'var(--color-text-secondary)' }}>
                                                            {source.summary}
                                                        </p>
                                                    )}
                                                </div>
                                            ))}
                                        </div>
                                    )}
                                </div>
                            </div>
                        ))}

                        {isLoading && (
                            <div className="flex justify-start">
                                <div className="max-w-[80%] rounded-lg p-4" style={{ backgroundColor: 'var(--color-bg-card)' }}>
                                    <div className="flex items-center gap-2">
                                        <Loader2 className="h-4 w-4 animate-spin" style={{ color: 'var(--color-accent-blue)' }} />
                                        <p className="text-sm" style={{ color: 'var(--color-text-secondary)' }}>Searching your captures...</p>
                                    </div>
                                </div>
                            </div>
                        )}
                    </div>
                )}
            </div>

            {/* Bottom Input (when chat started) */}
            {messages.length > 0 && (
                <div className="p-4" style={{ borderTop: '1px solid var(--color-border-light)' }}>
                    <div className="max-w-3xl mx-auto">
                        <form onSubmit={handleSubmit} className="flex gap-2">
                            <Input
                                value={input}
                                onChange={(e) => setInput(e.target.value)}
                                placeholder="Ask a question about your captures..."
                                disabled={isLoading}
                                className="flex-1"
                            />
                            <Button type="submit" disabled={isLoading || !input.trim()} style={{
                                backgroundColor: 'var(--color-accent-blue)',
                                color: '#ffffff'
                            }}>
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