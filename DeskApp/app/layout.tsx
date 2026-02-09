import React from "react"
import type { Metadata, Viewport } from 'next'
import { Geist, Geist_Mono } from 'next/font/google'
import { Analytics } from '@vercel/analytics/next'
import './globals.css'
import { ThemeProvider } from '@/components/theme-provider';


const _geist = Geist({ subsets: ["latin"] });
const _geistMono = Geist_Mono({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: 'Mnemos - Memory Meets Intelligence',
  description: 'Your personal knowledge operating system. Capture anything, organize automatically, and surface insights when you need them.',
  generator: 'v0.app',
  icons: {
  icon:
    process.env.NEXT_PUBLIC_APP_LOGO_PUBLIC_PATH ||
    "/logo.png",
},
}

export const viewport: Viewport = {
  themeColor: '#171717',
  colorScheme: 'dark',
}

// export default function RootLayout({
//   children,
// }: Readonly<{
//   children: React.ReactNode
// }>) {
//   return (
//     <html lang="en" className="dark">
//       <body className="font-sans antialiased">
//         {children}
//         <Analytics />
//       </body>
//     </html>
//   )
// }

export default function RootLayout({ children, }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body>
        <ThemeProvider attribute="class" defaultTheme="light" enableSystem>
          {children}
        </ThemeProvider>
      </body>
    </html>
  );
}