import React from "react"
import { ShellLayout } from "@/components/lifeos/shell-layout";

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return <ShellLayout>{children}</ShellLayout>;
}
