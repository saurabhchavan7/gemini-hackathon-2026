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
    <aside className="flex h-full w-[72px] flex-col items-center border-r py-4" style={{ backgroundColor: 'var(--color-bg-primary)', borderColor: 'var(--color-border-light)' }}>
      {/* Logo */}
      <div className="mb-6">
        <div className="flex h-10 w-10 items-center justify-center rounded-full" style={{ background: 'linear-gradient(135deg, var(--color-accent-blue) 0%, var(--color-accent-orange) 100%)' }}>
          <span className="text-lg font-bold text-white">L</span>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex flex-1 flex-col items-center gap-2">
        {navItems.map((item) => {
          const isActive = pathname === item.href || pathname.startsWith(`${item.href}/`);
          return (
            <Link
  key={item.href}
  href={item.href}
  className="flex h-12 w-12 items-center justify-center rounded-xl transition-all duration-200 hover:scale-105"
  style={{
    backgroundColor: isActive ? 'var(--color-accent-blue-light)' : 'transparent',
    color: isActive ? 'var(--color-accent-blue)' : 'var(--color-text-secondary)',
  }}
  onMouseEnter={(e) => {
    if (!isActive) {
      e.currentTarget.style.backgroundColor = 'var(--color-bg-tertiary)';
    }
  }}
  onMouseLeave={(e) => {
    if (!isActive) {
      e.currentTarget.style.backgroundColor = 'transparent';
    }
  }}
              title={item.label}
              aria-label={item.label}
              aria-current={isActive ? "page" : undefined}
            >
              <item.icon className="h-5 w-5" aria-hidden="true" />
            </Link>
          );
        })}
      </nav>

      {/* Settings at bottom */}
      <div className="mt-auto">
        <div className="h-8 w-8 rounded-full" style={{ backgroundColor: 'var(--color-bg-tertiary)' }}>
          <span className="flex h-full w-full items-center justify-center text-xs font-medium" style={{ color: 'var(--color-text-primary)' }}>
            U
          </span>
        </div>
      </div>
    </aside>
  );
}