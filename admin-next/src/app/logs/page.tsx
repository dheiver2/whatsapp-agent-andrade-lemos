"use client";
import { useQuery } from "@tanstack/react-query";
import { motion } from "framer-motion";
import { ScrollText } from "lucide-react";
import { api } from "@/lib/api";
import { PageHeader } from "@/components/page-header";
import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/index";

export default function LogsPage() {
  const { data, isLoading } = useQuery({
    queryKey: ["logs"],
    queryFn: api.logs,
    refetchInterval: 10_000,
  });

  return (
    <>
      <PageHeader title="Logs do sistema" description="Atualiza a cada 10s" />
      <div className="p-6 space-y-4">
        {isLoading
          ? [...Array(3)].map((_, i) => <Skeleton key={i} className="h-48" />)
          : (data || []).map((log, i) => (
              <motion.div
                key={log.path}
                initial={{ opacity: 0, y: 6 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.05 }}
              >
                <Card>
                  <CardContent className="p-0">
                    <div className="flex items-center justify-between p-3 border-b">
                      <h3 className="text-sm font-semibold flex items-center gap-2">
                        <ScrollText className="size-4 text-primary" /> {log.label}
                      </h3>
                      <div className="text-[10px] text-muted-foreground font-mono">{log.path}</div>
                    </div>
                    <pre className="p-3 text-xs font-mono whitespace-pre-wrap max-h-80 overflow-y-auto text-muted-foreground">
                      {log.content || "(vazio)"}
                    </pre>
                  </CardContent>
                </Card>
              </motion.div>
            ))}
      </div>
    </>
  );
}
