"use client";

import React from "react"

import { useState, useEffect, useCallback, useRef } from "react";
import { Plus, Check, Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";

type ButtonState = "idle" | "hover" | "pressed" | "loading" | "success";

const STORAGE_KEY = "lifeos-capture-button-position";

export function FloatingCaptureButton() {
  const [state, setState] = useState<ButtonState>("idle");
  const [position, setPosition] = useState({ x: 0, y: 0 });
  const [isDragging, setIsDragging] = useState(false);
  const buttonRef = useRef<HTMLButtonElement>(null);
  const dragStartRef = useRef({ x: 0, y: 0 });
  const positionStartRef = useRef({ x: 0, y: 0 });

  // Load position from localStorage
  useEffect(() => {
    const saved = localStorage.getItem(STORAGE_KEY);
    if (saved) {
      try {
        const parsed = JSON.parse(saved);
        setPosition(parsed);
      } catch {
        // Default position: bottom right
        setPosition({ x: window.innerWidth - 100, y: window.innerHeight - 100 });
      }
    } else {
      setPosition({ x: window.innerWidth - 100, y: window.innerHeight - 100 });
    }
  }, []);

  // Save position to localStorage
  useEffect(() => {
    if (position.x !== 0 || position.y !== 0) {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(position));
    }
  }, [position]);

  const handleMouseDown = useCallback((e: React.MouseEvent) => {
    setIsDragging(true);
    setState("pressed");
    dragStartRef.current = { x: e.clientX, y: e.clientY };
    positionStartRef.current = { ...position };
  }, [position]);

  const handleMouseMove = useCallback((e: MouseEvent) => {
    if (!isDragging) return;
    
    const deltaX = e.clientX - dragStartRef.current.x;
    const deltaY = e.clientY - dragStartRef.current.y;
    
    const newX = Math.max(32, Math.min(window.innerWidth - 32, positionStartRef.current.x + deltaX));
    const newY = Math.max(32, Math.min(window.innerHeight - 32, positionStartRef.current.y + deltaY));
    
    setPosition({ x: newX, y: newY });
  }, [isDragging]);

  const handleMouseUp = useCallback(() => {
    setIsDragging(false);
    setState("idle");
  }, []);

  useEffect(() => {
    if (isDragging) {
      window.addEventListener("mousemove", handleMouseMove);
      window.addEventListener("mouseup", handleMouseUp);
    }
    return () => {
      window.removeEventListener("mousemove", handleMouseMove);
      window.removeEventListener("mouseup", handleMouseUp);
    };
  }, [isDragging, handleMouseMove, handleMouseUp]);

const handleClick = useCallback(async () => {
  if (isDragging) return;
  
  setState("loading");
  
  try {
    // Check if Electron API is available
    if (window.electron && window.electron.captureScreen) {
      const result = await window.electron.captureScreen();
      
      if (result.success) {
        setState("success");
        
        // TODO: Send to your Python backend
        // For now, just log it
        console.log('Screenshot captured:', {
          timestamp: result.timestamp,
          dataSize: result.screenshot?.length,
          window: result.windowContext
        });
        
        // Optional: Send to backend API
        try {
          const response = await fetch('http://localhost:8000/api/capture', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              screenshot: result.screenshot,
              timestamp: result.timestamp,
              windowContext: result.windowContext
            })
          });
          
          if (response.ok) {
            console.log('Sent to backend successfully');
          }
        } catch (apiError) {
          console.log('Backend not available yet:', apiError);
        }
        
        setTimeout(() => {
          setState("idle");
        }, 1500);
      } else {
        console.error('Capture failed:', result.error);
        setState("idle");
      }
    } else {
      // Fallback for browser (without Electron)
      console.warn('Electron API not available - running in browser mode');
      setState("success");
      setTimeout(() => {
        setState("idle");
      }, 1500);
    }
  } catch (error) {
    console.error('Error during capture:', error);
    setState("idle");
  }
}, [isDragging]);

  // Keyboard shortcut
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.ctrlKey && e.shiftKey && e.key === "L") {
        e.preventDefault();
        handleClick();
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [handleClick]);

  const Icon = state === "loading" ? Loader2 : state === "success" ? Check : Plus;

  return (
    <div
      className="group fixed z-50"
      style={{
        left: position.x,
        top: position.y,
        transform: "translate(-50%, -50%)",
      }}
    >
      {/* Tooltip */}
      <div
        className={cn(
          "absolute bottom-full left-1/2 mb-2 -translate-x-1/2 whitespace-nowrap rounded-md bg-popover px-3 py-1.5 text-xs text-popover-foreground shadow-md transition-opacity",
          "opacity-0 group-hover:opacity-100",
          isDragging && "opacity-0"
        )}
        role="tooltip"
      >
        Capture — Ctrl+Shift+L
      </div>

      {/* Button */}
      <button
        ref={buttonRef}
        onMouseDown={handleMouseDown}
        onMouseEnter={() => !isDragging && setState("hover")}
        onMouseLeave={() => !isDragging && setState("idle")}
        onClick={handleClick}
        disabled={state === "loading" || state === "success"}
        className={cn(
          "flex h-16 w-16 items-center justify-center rounded-full shadow-lg transition-all duration-200",
          "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2",
          state === "idle" && "bg-accent text-accent-foreground hover:scale-105",
          state === "hover" && "scale-105 bg-accent text-accent-foreground",
          state === "pressed" && "scale-95 bg-accent/80 text-accent-foreground",
          state === "loading" && "bg-accent text-accent-foreground",
          state === "success" && "bg-success text-success-foreground",
          isDragging && "cursor-grabbing"
        )}
        aria-label="Capture current screen"
      >
        <Icon
          className={cn(
            "h-6 w-6",
            state === "loading" && "animate-spin"
          )}
          aria-hidden="true"
        />
      </button>
    </div>
  );
}
