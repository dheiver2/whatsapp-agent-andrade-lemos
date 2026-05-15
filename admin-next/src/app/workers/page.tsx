"use client";
import { useQuery } from "@tanstack/react-query";
import { Cpu, Clock, FileText, CheckCircle2, AlertTriangle } from "lucide-react";
import { api } from "@/lib/api";
import { PageHeader } from "@/components/page-header";
import { Card, CardContent } from "@/components/ui/card";
import { Badge, Skeleton } from "@/components/ui/index";

export default function WorkersPage() {
  const { data, isLoading } = useQuery({
    queryKey: ["workers"],
    queryFn: api.workers,
    refetchInterval: 30_000,
  });

  return (
    <>
      <PageHeader
        title="Workers & Cron"
        description="Jobs agendados que mantêm o sistema funcionando"
      />
      <div className="p-6 space-y-4">
        {isLoading ? (
          <div className="space-y-3">
            {[...Array(5)].map((_, i) => <Skeleton key={i} className="h-24" />)}
          </div>
        ) : (
          <div className="grid gap-3">
            {data?.map((w) => {
              const ok = !!w.last_line && !w.last_line.toLowerCase().includes("error") && !w.last_line.toLowerCase().includes("falh");
              return (
                <Card key={w.name}>
                  <CardContent className="p-5">
                    <div className="flex items-start justify-between gap-4 flex-wrap">
                      <div className="flex items-center gap-3">
                        <div className={`size-10 rounded-lg grid place-items-center ${ok ? "bg-emerald-500/10 text-emerald-500" : "bg-amber-500/10 text-amber-500"}`}>
                          {ok ? <CheckCircle2 className="size-5" /> : <AlertTriangle className="size-5" />}
                        </div>
                        <div>
                          <div className="font-semibold">{w.name}</div>
                          <div className="text-xs text-muted-foreground flex items-center gap-2 mt-0.5">
                            <Clock className="size-3" /> <code className="font-mono">{w.schedule}</code>
                            <span>·</span>
                            <code className="font-mono">{w.script}</code>
                          </div>
                        </div>
                      </div>
                      <div className="text-right">
                        <Badge variant={ok ? "success" : "warning"}>{ok ? "OK" : "Atenção"}</Badge>
                        {w.last_mod && <div className="text-xs text-muted-foreground mt-1">{w.last_mod}</div>}
                      </div>
                    </div>
                    {w.last_line && (
                      <div className="mt-3 text-xs font-mono bg-muted/50 rounded p-2 overflow-x-auto">
                        <FileText className="size-3 inline mr-1 text-muted-foreground" />
                        {w.last_line}
                      </div>
                    )}
                  </CardContent>
                </Card>
              );
            })}
          </div>
        )}
      </div>
    </>
  );
}
