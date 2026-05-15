"use client";
import { useQuery } from "@tanstack/react-query";
import { useParams } from "next/navigation";
import Link from "next/link";
import { motion } from "framer-motion";
import { ArrowLeft, Check, CheckCheck, Calendar, User } from "lucide-react";
import { api, CENARIO_LABEL, CENARIO_COLOR } from "@/lib/api";
import { PageHeader } from "@/components/page-header";
import { Card, CardContent } from "@/components/ui/card";
import { Badge, Skeleton } from "@/components/ui/index";
import { Button } from "@/components/ui/button";

export default function ConvDetailPage() {
  const { phone } = useParams<{ phone: string }>();
  const decoded = decodeURIComponent(phone);
  const { data, isLoading } = useQuery({
    queryKey: ["conversation", decoded],
    queryFn: () => api.conversation(decoded),
  });

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
        {/* Sidebar com dados */}
        <div className="space-y-4 lg:order-2">
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
                {data?.profile?.calendar_event_id && (
                  <div className="text-[10px] text-muted-foreground font-mono mt-1">
                    {data.profile.calendar_event_id}
                  </div>
                )}
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

        {/* WhatsApp-like chat */}
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
                </div>
              </div>
            </div>

            <div className="whatsapp-bg-light dark:whatsapp-bg p-4 max-h-[70vh] overflow-y-auto">
              {isLoading ? (
                <div className="space-y-3">
                  <Skeleton className="h-16 w-2/3" />
                  <Skeleton className="h-12 w-1/2 ml-auto" />
                  <Skeleton className="h-20 w-3/4" />
                </div>
              ) : !data?.history?.length ? (
                <div className="text-center text-sm text-muted-foreground py-12">Sem mensagens.</div>
              ) : (
                <div className="space-y-2">
                  {data.history.map((m, i) => (
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
                          {m.role !== "user" && <CheckCheck className="size-3 text-blue-500" />}
                        </div>
                      </div>
                    </motion.div>
                  ))}
                </div>
              )}
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
