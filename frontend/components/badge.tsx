import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function Badge({ status }: { status: string }) {
  const styles: Record<string, string> = {
    open: "bg-[var(--brand)]/10 text-[var(--brand)] border-[var(--brand)]/20",
    processing: "bg-[var(--brand)]/10 text-[var(--brand)] border-[var(--brand)]/20",
    manual_review: "bg-[var(--warning)]/10 text-[var(--warning)] border-[var(--warning)]/20",
    recovered: "bg-[var(--success)]/10 text-[var(--success)] border-[var(--success)]/20",
    partially_recovered: "bg-[var(--success)]/10 text-[var(--success)] border-[var(--success)]/20",
    failed: "bg-[var(--danger)]/10 text-[var(--danger)] border-[var(--danger)]/20",
  };
  
  const style = styles[status] || "bg-[var(--border-subtle)] text-[var(--text-secondary)] border-[var(--border-subtle)]";
  
  return (
    <span className={cn("inline-flex items-center px-2.5 py-1 rounded-full text-[10px] font-bold border uppercase tracking-widest", style)}>
      {status.replaceAll("_", " ")}
    </span>
  );
}

