"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import {
  Inbox,
  Search,
  FolderOpen,
  Sparkles,
  FileText,
  Bell,
  Settings,
  Zap,
} from "lucide-react";

const navItems = [
  { href: "/inbox", label: "Inbox", icon: Inbox },
  { href: "/search", label: "Search", icon: Search },
  { href: "/collections", label: "Collections", icon: FolderOpen },
  { href: "/synthesis", label: "Synthesis", icon: Sparkles },
  { href: "/digest", label: "Digest", icon: FileText },
  { href: "/notifications", label: "Notifications", icon: Bell },
  { href: "/settings", label: "Settings", icon: Settings },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="flex h-full w-56 flex-col border-r border-sidebar-border bg-sidebar">
      {/* Logo */}
      <div className="flex h-14 items-center gap-2 border-b border-sidebar-border px-4">
        <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-accent">
          <Zap className="h-4 w-4 text-accent-foreground" />
        </div>
        <span className="text-lg font-semibold text-sidebar-foreground">LifeOS</span>
      </div>

      {/* Navigation */}
      <nav className="flex-1 space-y-1 p-3">
        {navItems.map((item) => {
          const isActive = pathname === item.href || pathname.startsWith(`${item.href}/`);
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors",
                "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-sidebar-ring",
                isActive
                  ? "bg-sidebar-accent text-sidebar-accent-foreground"
                  : "text-sidebar-foreground/70 hover:bg-sidebar-accent/50 hover:text-sidebar-foreground"
              )}
              aria-current={isActive ? "page" : undefined}
            >
              <item.icon className="h-4 w-4" aria-hidden="true" />
              {item.label}
            </Link>
          );
        })}
      </nav>

      {/* Bottom section */}
      <div className="border-t border-sidebar-border p-3">
        <div className="rounded-md bg-sidebar-accent/50 p-3">
          <p className="text-xs text-sidebar-foreground/60">
            Local-first storage enabled
          </p>
          <p className="mt-1 text-xs font-medium text-sidebar-foreground/80">
            All data stays on your device
          </p>
        </div>
      </div>
    </aside>
  );
}
