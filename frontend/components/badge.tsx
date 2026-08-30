import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function Badge({ status }: { status: string }) {
  const styles: Record<string, string> = {
    open: "bg-blue-500/10 text-blue-400 border-blue-500/20",
    manual_review: "bg-amber-500/10 text-amber-400 border-amber-500/20",
    recovered: "bg-emerald-500/10 text-emerald-400 border-emerald-500/20",
    partially_recovered: "bg-lime-500/10 text-lime-400 border-lime-500/20",
    failed: "bg-red-500/10 text-red-400 border-red-500/20",
  };
  
  const style = styles[status] || "bg-gray-500/10 text-gray-400 border-gray-500/20";
  
  return (
    <span className={cn("inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border uppercase tracking-wider", style)}>
      {status.replace("_", " ")}
    </span>
  );
}
