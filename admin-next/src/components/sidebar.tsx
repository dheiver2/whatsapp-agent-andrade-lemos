"use client";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import {
  LayoutDashboard,
  MessagesSquare,
  Calendar,
  BookOpen,
  ScrollText,
  Settings2,
  QrCode,
  Scale,
  LogOut,
  ExternalLink,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { ThemeToggle } from "./theme-toggle";
import { Button } from "./ui/button";

const items = [
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { href: "/conversations", label: "Conversas", icon: MessagesSquare },
  { href: "/agenda", label: "Agenda", icon: Calendar },
  { href: "/knowledge", label: "Knowledge", icon: BookOpen },
  { href: "/logs", label: "Logs", icon: ScrollText },
  { href: "/control", label: "Controle", icon: Settings2 },
  { href: "/qr", label: "QR Code", icon: QrCode },
];

export function Sidebar() {
  const pathname = usePathname();
  const router = useRouter();

  const logout = () => {
    sessionStorage.removeItem("admin_creds");
    router.push("/login");
  };

  return (
    <aside className="hidden lg:flex w-64 shrink-0 flex-col border-r bg-card/50 backdrop-blur">
      <div className="h-16 flex items-center gap-2 px-6 border-b">
        <div className="size-9 rounded-lg bg-gradient-to-br from-brand to-brand-dark grid place-items-center text-white">
          <Scale className="size-5" />
        </div>
        <div>
          <div className="font-semibold leading-tight">Andrade & Lemos</div>
          <div className="text-[10px] text-muted-foreground uppercase tracking-wide">Admin · Bot Natasha</div>
        </div>
      </div>
      <nav className="flex-1 p-3 space-y-1 overflow-y-auto">
        <div className="text-[10px] uppercase text-muted-foreground px-3 py-1.5 tracking-wider">Menu</div>
        {items.map((item) => {
          const Icon = item.icon;
          const active = pathname === item.href || pathname.startsWith(item.href + "/");
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "flex items-center gap-3 px-3 py-2 rounded-md text-sm transition-colors",
                active
                  ? "bg-primary/10 text-primary font-medium"
                  : "text-muted-foreground hover:text-foreground hover:bg-accent"
              )}
            >
              <Icon className="size-4" />
              {item.label}
            </Link>
          );
        })}
        <div className="text-[10px] uppercase text-muted-foreground px-3 py-1.5 tracking-wider mt-4">Atalhos</div>
        <a
          href="/"
          className="flex items-center gap-3 px-3 py-2 rounded-md text-sm text-muted-foreground hover:text-foreground hover:bg-accent"
        >
          <ExternalLink className="size-4" /> Ver landing
        </a>
      </nav>
      <div className="p-3 border-t flex items-center justify-between gap-2">
        <Button variant="ghost" size="sm" onClick={logout} className="text-muted-foreground hover:text-destructive">
          <LogOut className="size-4 mr-1.5" /> Sair
        </Button>
        <ThemeToggle />
      </div>
    </aside>
  );
}

export function MobileNav() {
  const pathname = usePathname();
  // mostra 4 principais no mobile (mais limpo)
  const mobileItems = items.slice(0, 4);
  return (
    <nav className="lg:hidden fixed bottom-0 inset-x-0 z-30 border-t bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="grid grid-cols-4">
        {mobileItems.map((item) => {
          const Icon = item.icon;
          const active = pathname === item.href || pathname.startsWith(item.href + "/");
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "flex flex-col items-center gap-1 py-3 text-[10px]",
                active ? "text-primary" : "text-muted-foreground"
              )}
            >
              <Icon className="size-5" />
              <span className="truncate">{item.label}</span>
            </Link>
          );
        })}
      </div>
    </nav>
  );
}
