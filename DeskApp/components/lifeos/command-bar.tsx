/**
 * components/lifeos/command-bar.tsx
 * 
 * Top header bar with search and user profile menu
 * 
 * Features:
 * - Search input (opens command palette)
 * - User profile dropdown with Google-style menu
 * - Logout functionality
 */

"use client";

import { Search, Plus, LogOut, User } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Kbd } from "@/components/ui/kbd";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { Moon, Sun } from 'lucide-react';
import { useTheme } from 'next-themes';
import { ChevronDown } from "lucide-react";

interface CommandBarProps {
  onOpenCommandPalette: () => void;
}

export function CommandBar({ onOpenCommandPalette }: CommandBarProps) {
  const router = useRouter();
  const [user, setUser] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const { theme, setTheme } = useTheme();

  // Fetch user info on mount
  useEffect(() => {
    fetchUser();
  }, []);

  const fetchUser = async () => {
    try {
      if (typeof window !== 'undefined' && (window as any).electronAPI) {
        const result = await (window as any).electronAPI.getCurrentUser();
        setUser(result);
      }
    } catch (error) {
      console.error('Failed to fetch user:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = async () => {
    try {
      if (typeof window !== 'undefined' && (window as any).electronAPI) {
        await (window as any).electronAPI.logout();
        router.push('/login');
      }
    } catch (error) {
      console.error('Logout failed:', error);
    }
  };

  return (
    <header className="flex h-14 items-center justify-between border-b border-border bg-background px-6">
      {/* Search */}
      <div className="relative flex-1 max-w-md">
        <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" aria-hidden="true" />
        <Input
          type="search"
          placeholder="Search captures..."
          className="h-9 w-full bg-muted/50 pl-9 pr-16 text-sm placeholder:text-muted-foreground focus:bg-muted"
          onClick={onOpenCommandPalette}
          readOnly
          aria-label="Open search"
        />
        <div className="absolute right-2 top-1/2 -translate-y-1/2 flex items-center gap-1">
          <Kbd>Ctrl</Kbd>
          <Kbd>K</Kbd>
        </div>
      </div>


      {/* Actions */}
      <div className="flex items-center gap-3">
        {/* More Actions Dropdown */}
        {/* <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button
              variant="outline"
              size="sm"
              className="gap-2 transition-colors hover:bg-[var(--color-bg-tertiary)]"
            >
              More Actions
              <ChevronDown className="h-3.5 w-3.5" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            <DropdownMenuItem>Export Data</DropdownMenuItem>
            <DropdownMenuItem>Settings</DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu> */}

        {/* Theme Toggle */}
        <Button
          variant="ghost"
          size="sm"
          onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}
          className="h-9 w-9 rounded-full"
          aria-label="Toggle theme"
        >
          {theme === 'dark' ? (
            <Sun className="h-4 w-4" />
          ) : (
            <Moon className="h-4 w-4" />
          )}
        </Button>

        {/* User Profile Menu */}
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button
              variant="ghost"
              size="sm"
              className="relative h-9 w-9 rounded-full"
              aria-label="User menu"
            >
              <Avatar className="h-8 w-8">
                <AvatarImage src={user?.picture} alt={user?.name || 'User'} />
                <AvatarFallback className="text-white text-sm" style={{ backgroundColor: 'var(--color-accent-blue)' }}>
                  {user?.name?.charAt(0) || user?.email?.charAt(0) || 'U'}
                </AvatarFallback>
              </Avatar>
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="w-56">
            <DropdownMenuLabel className="font-normal">
              <div className="flex flex-col space-y-1">
                <p className="text-sm font-medium leading-none">{user?.name || 'User'}</p>
                <p className="text-xs leading-none text-muted-foreground">
                  {user?.email || 'Loading...'}
                </p>
              </div>
            </DropdownMenuLabel>
            <DropdownMenuSeparator />
            <DropdownMenuItem onClick={handleLogout} className="text-red-600 focus:text-red-600 cursor-pointer">
              <LogOut className="mr-2 h-4 w-4" />
              <span>Log out</span>
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    </header>
  );
}