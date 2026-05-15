"use client";
import * as React from "react";
import { Command } from "cmdk";
import { useRouter } from "next/navigation";
import {
  LayoutDashboard,
  MessagesSquare,
  Calendar,
  BookOpen,
  ScrollText,
  Settings2,
  QrCode,
  Search,
} from "lucide-react";

export function CommandPalette() {
  const [open, setOpen] = React.useState(false);
  const router = useRouter();

  React.useEffect(() => {
    const down = (e: KeyboardEvent) => {
      if ((e.key === "k" && (e.metaKey || e.ctrlKey))) {
        e.preventDefault();
        setOpen((o) => !o);
      }
    };
    document.addEventListener("keydown", down);
    return () => document.removeEventListener("keydown", down);
  }, []);

  const go = (path: string) => {
    setOpen(false);
    router.push(path);
  };

  if (!open) return null;
  return (
    <div className="fixed inset-0 z-50 bg-black/50 backdrop-blur-sm" onClick={() => setOpen(false)}>
      <div className="container max-w-xl mt-32" onClick={(e) => e.stopPropagation()}>
        <Command className="rounded-xl border bg-popover shadow-2xl overflow-hidden">
          <div className="flex items-center gap-2 px-3 border-b">
            <Search className="size-4 text-muted-foreground" />
            <Command.Input
              placeholder="Buscar páginas, comandos…"
              className="flex h-12 w-full bg-transparent text-sm outline-none placeholder:text-muted-foreground"
            />
          </div>
          <Command.List className="max-h-80 overflow-auto p-2">
            <Command.Empty className="p-4 text-sm text-muted-foreground text-center">
              Nada encontrado.
            </Command.Empty>
            <Command.Group heading="Navegação" className="text-xs text-muted-foreground px-2 py-1">
              {[
                { l: "Dashboard", h: "/dashboard", i: LayoutDashboard },
                { l: "Conversas", h: "/conversations", i: MessagesSquare },
                { l: "Agenda", h: "/agenda", i: Calendar },
                { l: "Knowledge", h: "/knowledge", i: BookOpen },
                { l: "Logs", h: "/logs", i: ScrollText },
                { l: "Controle", h: "/control", i: Settings2 },
                { l: "QR Code", h: "/qr", i: QrCode },
              ].map((it) => (
                <Command.Item
                  key={it.h}
                  onSelect={() => go(it.h)}
                  className="flex items-center gap-2 px-3 py-2 rounded-md text-sm cursor-pointer aria-selected:bg-accent"
                >
                  <it.i className="size-4 text-muted-foreground" />
                  {it.l}
                </Command.Item>
              ))}
            </Command.Group>
          </Command.List>
          <div className="border-t p-2 text-xs text-muted-foreground flex items-center justify-between">
            <span>↑↓ navegar · enter abrir · esc fechar</span>
            <kbd className="rounded border px-1.5 py-0.5 bg-muted text-[10px]">⌘K</kbd>
          </div>
        </Command>
      </div>
    </div>
  );
}
