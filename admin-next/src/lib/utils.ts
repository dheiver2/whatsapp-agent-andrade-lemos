import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatRelativeTime(iso: string): string {
  if (!iso) return "—";
  const d = new Date(iso);
  const now = new Date();
  const diff = Math.floor((now.getTime() - d.getTime()) / 1000);
  if (diff < 60) return "agora";
  if (diff < 3600) return `${Math.floor(diff / 60)}min`;
  if (diff < 86400) return `${Math.floor(diff / 3600)}h`;
  return d.toLocaleDateString("pt-BR");
}

export function formatBR(iso: string, options?: Intl.DateTimeFormatOptions): string {
  if (!iso) return "—";
  try {
    return new Date(iso).toLocaleString("pt-BR", options ?? { day: "2-digit", month: "2-digit", hour: "2-digit", minute: "2-digit" });
  } catch {
    return iso;
  }
}

export function formatBRL(v: string | number | null | undefined): string {
  if (!v) return "—";
  const num = typeof v === "string" ? parseFloat(v.replace(",", ".")) : v;
  if (isNaN(num)) return String(v);
  return num.toLocaleString("pt-BR", { style: "currency", currency: "BRL" });
}
