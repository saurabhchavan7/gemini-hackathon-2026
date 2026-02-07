"use client";

import { useState } from "react";
import { Sparkles, Send, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card } from "@/components/ui/card";
import { askAboutCapture } from "@/lib/api-client";

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
          className="gap-1 p-2 hover:bg-blue-500/10 rounded-lg transition-colors"
          title="Ask Gemini"
        >
          <Sparkles className="h-5 w-5 text-blue-500" />
        </Button>

        {isOpen && (
          <div 
            className="fixed inset-0 z-50 flex items-center justify-center bg-black/50"
            onClick={(e) => {
              e.stopPropagation();
              handleClose();
            }}
            onMouseDown={(e) => e.stopPropagation()}
            onMouseUp={(e) => e.stopPropagation()}
          >
            <Card 
              className="w-full max-w-lg p-6 space-y-4"
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
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Sparkles className="h-5 w-5 text-accent" />
                  <h3 className="font-semibold">Ask Gemini</h3>
                </div>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={(e) => {
                    e.stopPropagation();
                    handleClose();
                  }}
                >
                  <X className="h-4 w-4" />
                </Button>
              </div>

              <div className="flex gap-2">
                <Input
                  placeholder="Ask a question about this capture..."
                  value={question}
                  onChange={(e) => setQuestion(e.target.value)}
                  onKeyDown={(e) => {
                    e.stopPropagation();
                  }}
                  onKeyPress={(e) => {
                    if (e.key === 'Enter' && !isLoading) {
                      handleAsk();
                    }
                    e.stopPropagation();
                  }}
                  disabled={isLoading}
                />
                <Button
                  onClick={(e) => {
                    e.stopPropagation();
                    handleAsk();
                  }}
                  disabled={isLoading || !question.trim()}
                >
                  <Send className="h-4 w-4" />
                </Button>
              </div>

              {isLoading && (
                <div className="text-sm text-muted-foreground">
                  Thinking...
                </div>
              )}

              {answer && !isLoading && (
                <div className="rounded-lg bg-muted p-4 text-sm">
                  {answer}
                </div>
              )}
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
      >
        <Sparkles className="h-4 w-4" />
        Ask Gemini
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
            />
            <Button
              onClick={handleAsk}
              disabled={isLoading || !question.trim()}
            >
              <Send className="h-4 w-4" />
            </Button>
          </div>

          {isLoading && (
            <div className="text-sm text-muted-foreground">
              Thinking...
            </div>
          )}

          {answer && !isLoading && (
            <div className="rounded-lg bg-muted p-4 text-sm">
              {answer}
            </div>
          )}
        </div>
      )}
    </div>
  );
}