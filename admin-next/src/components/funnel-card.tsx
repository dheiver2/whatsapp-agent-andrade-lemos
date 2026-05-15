"use client";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { Card, CardContent } from "@/components/ui/card";
import { TrendingUp, Target, CheckCircle2 } from "lucide-react";

export function FunnelCard() {
  const { data } = useQuery({ queryKey: ["funnel"], queryFn: api.funnel, refetchInterval: 60_000 });
  if (!data) return null;
  const max = Math.max(...data.etapas.map((e) => e.value), 1);
  return (
    <Card>
      <CardContent className="p-6">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h3 className="text-lg font-semibold flex items-center gap-2">
              <TrendingUp className="size-5 text-primary" /> Funil de Conversão
            </h3>
            <p className="text-xs text-muted-foreground">Jornada do lead até fechamento</p>
          </div>
          <div className="text-right text-xs space-y-0.5">
            <div className="flex items-center gap-1.5">
              <Target className="size-3" /> Agendamento: <span className="font-semibold">{data.conversao_agendamento}%</span>
            </div>
            <div className="flex items-center gap-1.5">
              <CheckCircle2 className="size-3 text-emerald-500" /> Fechamento: <span className="font-semibold text-emerald-500">{data.conversao_fechamento}%</span>
            </div>
          </div>
        </div>
        <div className="space-y-2">
          {data.etapas.map((e, i) => {
            const pct = (e.value / max) * 100;
            return (
              <div key={e.label} className="flex items-center gap-3">
                <div className="w-32 text-sm text-muted-foreground shrink-0">{e.label}</div>
                <div className="flex-1 h-8 rounded bg-muted/50 relative overflow-hidden">
                  <div
                    className="h-full bg-gradient-to-r from-primary to-brand-dark transition-all"
                    style={{ width: `${pct}%` }}
                  />
                  <div className="absolute inset-0 flex items-center px-3 text-sm font-semibold">
                    {e.value}
                  </div>
                </div>
              </div>
            );
          })}
          {data.perdidos > 0 && (
            <div className="text-xs text-amber-600 mt-2">⚠ {data.perdidos} leads marcados como "sem interesse"</div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
