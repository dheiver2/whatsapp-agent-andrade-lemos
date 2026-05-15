"use client";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useParams } from "next/navigation";
import { useState } from "react";
import Link from "next/link";
import { motion } from "framer-motion";
import { ArrowLeft, CheckCheck, Calendar, Send, Pause, Play, Tag } from "lucide-react";
import { toast } from "sonner";
import { api, CENARIO_LABEL, CENARIO_COLOR, LEAD_STATUSES } from "@/lib/api";
import { PageHeader } from "@/components/page-header";
import { Card, CardContent } from "@/components/ui/card";
import { Badge, Skeleton, Input } from "@/components/ui/index";
import { Button } from "@/components/ui/button";

export default function ConvDetailPage() {
  const { phone } = useParams<{ phone: string }>();
  const decoded = decodeURIComponent(phone);
  const qc = useQueryClient();
  const { data, isLoading } = useQuery({
    queryKey: ["conversation", decoded],
    queryFn: () => api.conversation(decoded),
    refetchInterval: 15_000,
  });

  const [manualMsg, setManualMsg] = useState("");

  const send = useMutation({
    mutationFn: (m: string) => api.leadSend(decoded, m),
    onSuccess: () => { toast.success("Mensagem enviada"); setManualMsg(""); qc.invalidateQueries({ queryKey: ["conversation", decoded] }); },
    onError: (e: any) => toast.error(e.message),
  });

  const setStatus = useMutation({
    mutationFn: (s: string) => api.leadStatus(decoded, s),
    onSuccess: () => { toast.success("Status atualizado"); qc.invalidateQueries({ queryKey: ["conversation", decoded] }); },
    onError: (e: any) => toast.error(e.message),
  });

  const pause = useMutation({
    mutationFn: () => api.leadPause(decoded),
    onSuccess: () => { toast.success("IA pausada para este lead"); qc.invalidateQueries({ queryKey: ["conversation", decoded] }); },
    onError: (e: any) => toast.error(e.message),
  });

  const resume = useMutation({
    mutationFn: () => api.leadResume(decoded),
    onSuccess: () => { toast.success("IA retomada"); qc.invalidateQueries({ queryKey: ["conversation", decoded] }); },
    onError: (e: any) => toast.error(e.message),
  });

  const paused = data?.profile?.lead_status === "waiting_human";

  return (
    <>
      <PageHeader
        title={data?.profile?.name || decoded}
        description={decoded}
        action={
          <Link href="/conversations">
            <Button variant="ghost" size="sm" className="gap-1">
              <ArrowLeft className="size-4" /> Voltar
            </Button>
          </Link>
        }
      />

      <div className="p-6 grid lg:grid-cols-3 gap-6">
        <div className="space-y-4 lg:order-2">
          {/* AÇÕES POR LEAD */}
          <Card className="border-primary/30">
            <CardContent className="p-5 space-y-3">
              <h3 className="text-xs uppercase text-muted-foreground font-semibold">Ações</h3>
              <div className="flex flex-wrap gap-2">
                {paused ? (
                  <Button size="sm" onClick={() => resume.mutate()} disabled={resume.isPending}>
                    <Play className="size-3.5 mr-1" /> Retomar IA
                  </Button>
                ) : (
                  <Button size="sm" variant="outline" onClick={() => pause.mutate()} disabled={pause.isPending}>
                    <Pause className="size-3.5 mr-1" /> Pausar IA
                  </Button>
                )}
                <Button size="sm" variant="outline" onClick={() => setStatus.mutate("won")} disabled={setStatus.isPending}>
                  <Tag className="size-3.5 mr-1" /> Ganho
                </Button>
                <Button size="sm" variant="outline" onClick={() => setStatus.mutate("sem_interesse")} disabled={setStatus.isPending}>
                  <Tag className="size-3.5 mr-1" /> Sem interesse
                </Button>
              </div>
              <div>
                <label className="text-xs text-muted-foreground">Alterar status:</label>
                <select
                  className="w-full mt-1 p-2 text-sm border rounded-md bg-background"
                  value={data?.profile?.lead_status || ""}
                  onChange={(e) => setStatus.mutate(e.target.value)}
                >
                  {LEAD_STATUSES.map((s) => <option key={s} value={s}>{s}</option>)}
                </select>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-5">
              <h3 className="text-xs uppercase text-muted-foreground font-semibold mb-3">Dados coletados</h3>
              <DataRow label="Valor atual" value={data?.profile?.valor_atual} prefix="R$ " />
              <DataRow label="Operadora" value={data?.profile?.operadora} />
              <DataRow label="Data adesão" value={data?.profile?.data_adesao} />
              <DataRow label="Modalidade" value={data?.profile?.tipo_plano} />
            </CardContent>
          </Card>

          {data?.cenario && data.cenario !== "indefinido" && (
            <Card className="border-2" style={{ borderColor: "hsl(var(--primary))" }}>
              <CardContent className="p-5">
                <h3 className="text-xs uppercase text-muted-foreground font-semibold mb-2">Diagnóstico Natasha</h3>
                <Badge variant={(CENARIO_COLOR[data.cenario] || "secondary") as any} className="text-sm">
                  {CENARIO_LABEL[data.cenario] || data.cenario}
                </Badge>
              </CardContent>
            </Card>
          )}

          {(data?.profile?.name_full || data?.profile?.email) && (
            <Card>
              <CardContent className="p-5">
                <h3 className="text-xs uppercase text-muted-foreground font-semibold mb-3">Contato confirmado</h3>
                {data.profile.name_full && <DataRow label="Nome completo" value={data.profile.name_full} />}
                {data.profile.email && <DataRow label="Email" value={data.profile.email} />}
              </CardContent>
            </Card>
          )}

          <Card>
            <CardContent className="p-5">
              <h3 className="text-xs uppercase text-muted-foreground font-semibold mb-3">Estado</h3>
              <DataRow label="Etapa" value={data?.stage} />
              <DataRow label="Status" value={data?.profile?.lead_status} />
              <DataRow label="Follow-up D+" value={String(data?.profile?.last_followup_day || 0)} />
              <DataRow label="Pós-reunião Dia" value={String(data?.profile?.post_meeting_day || 0)} />
              <DataRow label="Telefone" value={decoded} mono />
            </CardContent>
          </Card>

          {data?.profile?.confirmed_slot ? (
            <Card className="border-emerald-500/40 bg-emerald-500/5">
              <CardContent className="p-5">
                <h3 className="text-xs uppercase text-emerald-500 font-semibold mb-2 flex items-center gap-1.5">
                  <Calendar className="size-3.5" /> Consulta agendada
                </h3>
                <div className="text-lg font-semibold">{data?.slot_str || "—"}</div>
              </CardContent>
            </Card>
          ) : null}

          {data?.profile?.ai_summary && (
            <Card>
              <CardContent className="p-5">
                <h3 className="text-xs uppercase text-muted-foreground font-semibold mb-2">Resumo IA</h3>
                <p className="text-sm">{data.profile.ai_summary}</p>
              </CardContent>
            </Card>
          )}
        </div>

        <div className="lg:col-span-2 lg:order-1">
          <Card className="overflow-hidden">
            <div className="bg-primary/90 text-primary-foreground p-3 flex items-center gap-3">
              <div className="size-9 rounded-full bg-white/20 grid place-items-center font-semibold">
                {(data?.profile?.name?.[0] || "?").toUpperCase()}
              </div>
              <div className="flex-1 min-w-0">
                <div className="font-medium truncate">{data?.profile?.name || decoded}</div>
                <div className="text-xs opacity-80 flex items-center gap-1.5">
                  <Badge variant="secondary" className="text-[10px] bg-white/20 text-white border-0">
                    {data?.stage || "..."}
                  </Badge>
                  {data?.history && <span className="opacity-80">{data.history.length} mensagens</span>}
                  {paused && <Badge variant="warning" className="text-[10px]">IA PAUSADA</Badge>}
                </div>
              </div>
            </div>

            <div className="whatsapp-bg-light dark:whatsapp-bg p-4 max-h-[60vh] overflow-y-auto">
              {isLoading ? (
                <div className="space-y-3">
                  <Skeleton className="h-16 w-2/3" />
                  <Skeleton className="h-12 w-1/2 ml-auto" />
                </div>
              ) : !data?.history?.length ? (
                <div className="text-center text-sm text-muted-foreground py-12">Sem mensagens.</div>
              ) : (
                <div className="space-y-2">
                  {data.history.map((m: any, i: number) => (
                    <motion.div
                      key={i}
                      initial={{ opacity: 0, y: 4 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: i * 0.01 }}
                      className={m.role === "user" ? "flex justify-start" : "flex justify-end"}
                    >
                      <div
                        className={
                          m.role === "user"
                            ? "max-w-[75%] bg-white dark:bg-zinc-800 rounded-lg rounded-tl-none px-3 py-2 shadow-sm"
                            : "max-w-[75%] bg-[#d9fdd3] dark:bg-emerald-900/40 rounded-lg rounded-tr-none px-3 py-2 shadow-sm"
                        }
                      >
                        <p className="text-sm whitespace-pre-wrap text-zinc-900 dark:text-zinc-100">{m.content}</p>
                        <div className="flex items-center justify-end gap-1 mt-0.5 text-[10px] text-muted-foreground">
                          {m.manual_by && <span className="text-amber-600">manual:{m.manual_by}</span>}
                          {m.role !== "user" && <CheckCheck className="size-3 text-blue-500" />}
                        </div>
                      </div>
                    </motion.div>
                  ))}
                </div>
              )}
            </div>

            {/* Envio manual */}
            <div className="border-t p-3 flex gap-2 bg-card">
              <Input
                placeholder="Digite uma mensagem manual..."
                value={manualMsg}
                onChange={(e) => setManualMsg(e.target.value)}
                onKeyDown={(e) => { if (e.key === "Enter" && manualMsg.trim()) send.mutate(manualMsg.trim()); }}
              />
              <Button
                onClick={() => manualMsg.trim() && send.mutate(manualMsg.trim())}
                disabled={send.isPending || !manualMsg.trim()}
              >
                <Send className="size-4" />
              </Button>
            </div>
          </Card>
        </div>
      </div>
    </>
  );
}

function DataRow({ label, value, mono, prefix }: { label: string; value?: any; mono?: boolean; prefix?: string }) {
  return (
    <div className="flex items-center justify-between py-1.5 text-sm border-b last:border-0 border-border/50">
      <span className="text-muted-foreground text-xs">{label}</span>
      <span className={mono ? "font-mono text-xs" : ""}>
        {value ? (prefix ? prefix + value : value) : "—"}
      </span>
    </div>
  );
}
