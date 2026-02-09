"use client";

import { useState } from "react";
import { Sparkles, Send, X, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card } from "@/components/ui/card";
import { askAboutCapture } from "@/lib/api-client";
import { MarkdownContent } from "./markdown-content";

interface AskGeminiButtonProps {
  captureId: string;
  variant?: "icon" | "button";
}

export function AskGeminiButton({ captureId, variant = "button" }: AskGeminiButtonProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  const handleAsk = async () => {
    if (!question.trim()) return;

    setIsLoading(true);
    setAnswer(""); // Clear previous answer

    try {
      const result = await askAboutCapture(captureId, question);
      if (result.success) {
        setAnswer(result.answer);
      } else {
        setAnswer("Sorry, I couldn't answer that question.");
      }
    } catch (error) {
      setAnswer("Error asking question. Please try again.");
    } finally {
      setIsLoading(false);
    }
  };

  const handleClose = () => {
    setIsOpen(false);
    setQuestion("");
    setAnswer("");
  };

  if (variant === "icon") {
    return (
      <>
        <Button
          variant="ghost"
          size="sm"
          onClick={(e) => {
            e.stopPropagation();
            e.preventDefault();
            setIsOpen(true);
          }}
          className="gap-1 p-2 rounded-lg transition-colors"
          style={{
            color: 'var(--color-accent-blue)'
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.backgroundColor = 'var(--color-accent-blue-light)';
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.backgroundColor = 'transparent';
          }}
          title="Ask Gemini 3"
        >
          <Sparkles className="h-5 w-5" style={{ color: 'var(--color-accent-blue)' }} />
        </Button>

        {isOpen && (
          <div
            className="fixed inset-0 z-50 flex items-center justify-center"
            style={{ backgroundColor: 'rgba(0,0,0,0.5)' }}
            onClick={(e) => {
              e.stopPropagation();
              handleClose();
            }}
            onMouseDown={(e) => e.stopPropagation()}
            onMouseUp={(e) => e.stopPropagation()}
          >
            <Card
              className="w-full max-w-2xl flex flex-col rounded-2xl border-0 overflow-hidden"
              style={{
                backgroundColor: 'var(--color-bg-card)',
                maxHeight: '80vh',
                boxShadow: '0 20px 60px rgba(0,0,0,0.3)'
              }}
              onClick={(e) => {
                e.stopPropagation();
              }}
              onMouseDown={(e) => {
                e.stopPropagation();
              }}
              onMouseUp={(e) => {
                e.stopPropagation();
              }}
            >
              {/* Header */}
              <div className="flex items-center justify-between p-4 border-b" style={{ borderColor: 'var(--color-border-light)' }}>
                <div className="flex items-center gap-2">
                  <div className="h-8 w-8 rounded-lg flex items-center justify-center" style={{ backgroundColor: 'var(--color-accent-blue-light)' }}>
                    <Sparkles className="h-4 w-4" style={{ color: 'var(--color-accent-blue)' }} />
                  </div>
                  <h3 className="font-semibold text-base" style={{ color: 'var(--color-text-primary)' }}>Ask Gemini 3</h3>
                </div>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={(e) => {
                    e.stopPropagation();
                    handleClose();
                  }}
                  className="h-8 w-8 p-0 rounded-full"
                >
                  <X className="h-4 w-4" />
                </Button>
              </div>

              {/* Input */}
              <div className="p-4 border-b" style={{ borderColor: 'var(--color-border-light)' }}>
                <div className="flex gap-2">
                  <Input
                    placeholder="Ask a question about this capture..."
                    value={question}
                    onChange={(e) => setQuestion(e.target.value)}
                    onKeyDown={(e) => {
                      e.stopPropagation();
                      if (e.key === 'Enter' && !isLoading && question.trim()) {
                        handleAsk();
                      }
                    }}
                    disabled={isLoading}
                    className="flex-1"
                    style={{
                      backgroundColor: 'var(--color-bg-secondary)',
                      borderColor: 'var(--color-border-light)'
                    }}
                  />
                  <Button
                    onClick={(e) => {
                      e.stopPropagation();
                      handleAsk();
                    }}
                    disabled={isLoading || !question.trim()}
                    className="px-4"
                    style={{
                      backgroundColor: 'var(--color-accent-blue)',
                      color: '#ffffff'
                    }}
                  >
                    {isLoading ? (
                      <Loader2 className="h-4 w-4 animate-spin" />
                    ) : (
                      <Send className="h-4 w-4" />
                    )}
                  </Button>
                </div>
              </div>

              {/* Answer Area with Scrollbar */}
              <div className="flex-1 overflow-y-auto p-6" style={{
                backgroundColor: 'var(--color-bg-secondary)',
                minHeight: '200px',
                maxHeight: 'calc(80vh - 160px)'
              }}>
                {isLoading && (
                  <div className="flex items-center gap-2 text-sm" style={{ color: 'var(--color-text-secondary)' }}>
                    <Loader2 className="h-4 w-4 animate-spin" style={{ color: 'var(--color-accent-blue)' }} />
                    <span>Gemini 3 is thinking...</span>
                  </div>
                )}

                {!isLoading && !answer && (
                  <div className="flex flex-col items-center justify-center h-full text-center py-12">
                    <div className="h-16 w-16 rounded-full flex items-center justify-center mb-4" style={{ backgroundColor: 'var(--color-accent-blue-light)' }}>
                      <Sparkles className="h-8 w-8" style={{ color: 'var(--color-accent-blue)' }} />
                    </div>
                    <p className="text-sm" style={{ color: 'var(--color-text-secondary)' }}>
                      Ask me anything about this capture
                    </p>
                  </div>
                )}

                {answer && !isLoading && (
                  <div className="rounded-xl p-4" style={{ backgroundColor: 'var(--color-bg-card)' }}>
                    <MarkdownContent content={answer} />
                  </div>
                )}
              </div>
            </Card>
          </div>
        )}
      </>
    );
  }

  // Full button variant (for detail drawer)
  return (
    <div className="space-y-3">
      <Button
        variant="outline"
        className="w-full gap-2"
        onClick={() => setIsOpen(!isOpen)}
        style={{
          borderColor: 'var(--color-border-light)'
        }}
      >
        <Sparkles className="h-5 w-5" style={{ color: 'var(--color-accent-blue)' }} />
        Ask Gemini 3
      </Button>

      {isOpen && (
        <div className="space-y-3">
          <div className="flex gap-2">
            <Input
              placeholder="Ask a question about this capture..."
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              onKeyPress={(e) => {
                if (e.key === 'Enter' && !isLoading) {
                  handleAsk();
                }
              }}
              disabled={isLoading}
              className="flex-1"
            />
            <Button
              onClick={handleAsk}
              disabled={isLoading || !question.trim()}
              style={{
                backgroundColor: 'var(--color-accent-blue)',
                color: '#ffffff'
              }}
            >
              {isLoading ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Send className="h-4 w-4" />
              )}
            </Button>
          </div>

          {isLoading && (
            <div className="flex items-center gap-2 text-sm" style={{ color: 'var(--color-text-secondary)' }}>
              <Loader2 className="h-4 w-4 animate-spin" />
              Thinking...
            </div>
          )}

          {answer && !isLoading && (
            <div className="rounded-lg p-4 max-h-96 overflow-y-auto" style={{ backgroundColor: 'var(--color-bg-secondary)' }}>
              <MarkdownContent content={answer} />
            </div>
          )}
        </div>
      )}
    </div>
  );
}