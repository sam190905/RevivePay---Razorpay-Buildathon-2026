import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { Sidebar } from "./components/sidebar";

const inter = Inter({
  variable: "--font-inter",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "RevivePay — AI Revenue Recovery",
  description:
    "AI-powered revenue recovery system. Detect failed payments, diagnose causes, and recover revenue within deterministic guardrails.",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="en" className={`${inter.variable} h-full`}>
      <body className="h-full bg-gray-950 text-gray-100 font-[family-name:var(--font-inter)]">
        <div className="flex h-full">
          <Sidebar />
          <main className="flex-1 overflow-y-auto">
            <div className="px-8 py-6">{children}</div>
          </main>
        </div>
      </body>
    </html>
  );
}
