import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
// import { Sidebar } from "./components/sidebar"; // Kept for reference but no longer used
import { TopNav } from "./components/topnav";
import { ThemeProvider } from "./components/theme-provider";

const inter = Inter({
  variable: "--font-inter",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "RevivePay — AI Revenue Recovery",
  description:
    "AI-powered revenue recovery system. Detect failed payments, diagnose causes, and recover revenue within deterministic guardrails.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className={`${inter.variable} h-full`} suppressHydrationWarning>
      <body className="h-full font-[family-name:var(--font-inter)] antialiased bg-[var(--bg-base)] text-[var(--text-primary)]">
        <ThemeProvider>
          <div className="flex flex-col min-h-screen">
            <TopNav />
            <main className="flex-1 overflow-y-auto">
              <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 py-8">
                {children}
              </div>
            </main>
          </div>
        </ThemeProvider>
      </body>
    </html>
  );
}
