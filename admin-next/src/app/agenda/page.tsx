"use client";
import { useQuery } from "@tanstack/react-query";
import { useState, useMemo } from "react";
import { motion } from "framer-motion";
import { ChevronLeft, ChevronRight, ExternalLink, Calendar as CalIcon } from "lucide-react";
import { api, AgendaEvent } from "@/lib/api";
import { PageHeader } from "@/components/page-header";
import { Card, CardContent } from "@/components/ui/card";
import { Badge, Skeleton } from "@/components/ui/index";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

const DAYS_PT = ["Dom", "Seg", "Ter", "Qua", "Qui", "Sex", "Sáb"];
const MONTHS_PT = [
  "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
  "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro",
];

export default function AgendaPage() {
  const { data, isLoading } = useQuery({ queryKey: ["agenda"], queryFn: () => api.agenda(60) });
  const [cursor, setCursor] = useState(new Date());

  const month = cursor.getMonth();
  const year = cursor.getFullYear();
  const firstDay = new Date(year, month, 1);
  const lastDay = new Date(year, month + 1, 0);
  const startWeekday = firstDay.getDay();
  const daysInMonth = lastDay.getDate();

  // Group events by date (YYYY-MM-DD)
  const eventsByDay = useMemo(() => {
    const m: Record<string, AgendaEvent[]> = {};
    (data || []).forEach((e) => {
      const date = (e.inicio || "").slice(0, 10);
      if (!date) return;
      m[date] = m[date] || [];
      m[date].push(e);
    });
    return m;
  }, [data]);

  // Build calendar cells (42 cells, 6 weeks)
  const cells: { date: Date | null; isCurrentMonth: boolean }[] = [];
  for (let i = 0; i < startWeekday; i++) cells.push({ date: null, isCurrentMonth: false });
  for (let d = 1; d <= daysInMonth; d++) cells.push({ date: new Date(year, month, d), isCurrentMonth: true });
  while (cells.length % 7 !== 0) cells.push({ date: null, isCurrentMonth: false });

  const today = new Date();
  const isToday = (d: Date) =>
    d.getDate() === today.getDate() && d.getMonth() === today.getMonth() && d.getFullYear() === today.getFullYear();

  return (
    <>
      <PageHeader
        title="Agenda"
        description="Compromissos do Dr. Filipe — visualização mensal"
        action={
          <div className="flex items-center gap-2">
            <Button variant="outline" size="icon" onClick={() => setCursor(new Date(year, month - 1, 1))}>
              <ChevronLeft className="size-4" />
            </Button>
            <div className="font-medium min-w-[180px] text-center text-sm">
              {MONTHS_PT[month]} {year}
            </div>
            <Button variant="outline" size="icon" onClick={() => setCursor(new Date(year, month + 1, 1))}>
              <ChevronRight className="size-4" />
            </Button>
            <Button variant="outline" size="sm" onClick={() => setCursor(new Date())}>
              Hoje
            </Button>
          </div>
        }
      />

      <div className="p-6 space-y-4">
        <Card>
          <CardContent className="p-0">
            {/* Header dias */}
            <div className="grid grid-cols-7 border-b">
              {DAYS_PT.map((d) => (
                <div key={d} className="px-2 py-2 text-xs text-muted-foreground font-medium text-center">
                  {d}
                </div>
              ))}
            </div>
            {/* Grid */}
            <div className="grid grid-cols-7 auto-rows-fr">
              {cells.map((c, i) => {
                if (!c.date) return <div key={i} className="min-h-24 border-t border-l first:border-l-0" />;
                const key = c.date.toISOString().slice(0, 10);
                const events = eventsByDay[key] || [];
                const today_ = isToday(c.date);
                return (
                  <motion.div
                    key={i}
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    transition={{ delay: (i % 7) * 0.01 }}
                    className={cn(
                      "min-h-24 border-t border-l first:border-l-0 p-1.5 relative",
                      today_ && "bg-primary/5"
                    )}
                  >
                    <div className={cn("text-xs font-medium mb-1", today_ && "text-primary")}>
                      {c.date.getDate()}
                      {today_ && (
                        <span className="ml-1 text-[9px] text-primary font-semibold uppercase">hoje</span>
                      )}
                    </div>
                    <div className="space-y-0.5">
                      {events.slice(0, 3).map((e, j) => (
                        <a
                          key={j}
                          href={e.html_link}
                          target="_blank"
                          rel="noreferrer"
                          className={cn(
                            "block px-1.5 py-0.5 rounded text-[10px] truncate hover:opacity-90",
                            e.criado_pelo_bot
                              ? "bg-primary/15 text-primary"
                              : "bg-blue-500/15 text-blue-600 dark:text-blue-400"
                          )}
                          title={e.titulo}
                        >
                          {!e.all_day && (e.inicio || "").slice(11, 16) + " "}
                          {e.titulo}
                        </a>
                      ))}
                      {events.length > 3 && (
                        <div className="text-[10px] text-muted-foreground px-1.5">+{events.length - 3}</div>
                      )}
                    </div>
                  </motion.div>
                );
              })}
            </div>
          </CardContent>
        </Card>

        {/* Próximos eventos lista */}
        <Card>
          <CardContent className="p-4">
            <h3 className="text-sm font-semibold flex items-center gap-2 mb-3">
              <CalIcon className="size-4 text-primary" /> Próximos eventos
            </h3>
            {isLoading ? (
              <div className="space-y-2">
                <Skeleton className="h-12" />
                <Skeleton className="h-12" />
              </div>
            ) : (data || []).length === 0 ? (
              <p className="text-sm text-muted-foreground">Sem eventos.</p>
            ) : (
              <div className="space-y-1">
                {(data || []).slice(0, 12).map((e, i) => (
                  <div
                    key={i}
                    className="flex items-center gap-3 p-2 rounded-md hover:bg-accent/50 transition"
                  >
                    <div className="w-16 text-xs text-muted-foreground tabular-nums">
                      {(e.inicio || "").slice(0, 10)}
                    </div>
                    <div className="w-16 text-xs font-mono">
                      {e.all_day ? "—" : (e.inicio || "").slice(11, 16)}
                    </div>
                    <div className="flex-1 text-sm truncate">{e.titulo}</div>
                    {e.criado_pelo_bot ? (
                      <Badge variant="success" className="text-[10px]">🤖 Bot</Badge>
                    ) : (
                      <Badge variant="secondary" className="text-[10px]">manual</Badge>
                    )}
                    {e.html_link && (
                      <a href={e.html_link} target="_blank" rel="noreferrer" className="text-primary">
                        <ExternalLink className="size-3" />
                      </a>
                    )}
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </>
  );
}
