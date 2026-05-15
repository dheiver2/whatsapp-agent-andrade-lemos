"use client";
import { useQuery } from "@tanstack/react-query";
import { motion } from "framer-motion";
import { Sparkles, Bot, Calendar, Mail, Hash, Clock, CheckCircle2, XCircle } from "lucide-react";
import { api } from "@/lib/api";
import { PageHeader } from "@/components/page-header";
import { Card, CardContent } from "@/components/ui/card";
import { Badge, Skeleton } from "@/components/ui/index";

export default function SettingsPage() {
  const { data, isLoading } = useQuery({ queryKey: ["llm-info"], queryFn: api.llmInfo });

  return (
    <>
      <PageHeader title="Configurações" description="Provedor LLM, agenda e parâmetros do bot" />
      <div className="p-6 space-y-6">
        <motion.div initial={{ opacity: 0, y: 6 }} animate={{ opacity: 1, y: 0 }}>
          <Card>
            <CardContent className="p-5">
              <div className="flex items-center gap-2 mb-4">
                <Sparkles className="size-5 text-primary" />
                <h2 className="text-lg font-semibold">Modelos de IA</h2>
              </div>
              {isLoading ? (
                <div className="space-y-2"><Skeleton className="h-12" /><Skeleton className="h-12" /></div>
              ) : (
                <div className="grid sm:grid-cols-2 gap-3">
                  <div className="p-4 rounded-lg border bg-emerald-500/5 border-emerald-500/30">
                    <div className="text-xs uppercase text-emerald-500 font-semibold mb-1">Primary</div>
                    <div className="font-semibold capitalize">{data?.primary || "?"}</div>
                    <div className="text-sm text-muted-foreground font-mono mt-1">
                      {data?.primary === "openai" ? data?.openai_model : data?.openrouter_model}
                    </div>
                  </div>
                  <div className="p-4 rounded-lg border bg-amber-500/5 border-amber-500/30">
                    <div className="text-xs uppercase text-amber-500 font-semibold mb-1">Fallback</div>
                    <div className="font-semibold capitalize">{data?.fallback || "?"}</div>
                    <div className="text-sm text-muted-foreground font-mono mt-1">
                      {data?.fallback === "openai" ? data?.openai_model
                       : data?.fallback === "openai_fallback" ? data?.openai_model_fallback
                       : data?.openrouter_model}
                    </div>
                  </div>
                </div>
              )}
              <div className="mt-4 flex items-center gap-4 text-sm">
                <div className="flex items-center gap-1.5">
                  {data?.openai_configured ? <CheckCircle2 className="size-4 text-emerald-500" /> : <XCircle className="size-4 text-rose-500" />}
                  OpenAI
                </div>
                <div className="flex items-center gap-1.5">
                  {data?.openrouter_configured ? <CheckCircle2 className="size-4 text-emerald-500" /> : <XCircle className="size-4 text-rose-500" />}
                  OpenRouter
                </div>
              </div>
            </CardContent>
          </Card>
        </motion.div>

        <motion.div initial={{ opacity: 0, y: 6 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.05 }}>
          <Card>
            <CardContent className="p-5">
              <div className="flex items-center gap-2 mb-4">
                <Bot className="size-5 text-primary" />
                <h2 className="text-lg font-semibold">Recursos OpenAI ativos</h2>
              </div>
              <div className="grid sm:grid-cols-2 gap-3">
                <FeatureRow label="Chat (Natasha)" model={data?.openai_model || "—"} />
                <FeatureRow label="Transcrição áudio" model="whisper-1" />
                <FeatureRow label="OCR fotos/boletos" model="gpt-4o-mini (vision)" />
                <FeatureRow label="Fallback robusto" model={data?.openai_model_fallback || "—"} />
              </div>
            </CardContent>
          </Card>
        </motion.div>

        <motion.div initial={{ opacity: 0, y: 6 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }}>
          <Card>
            <CardContent className="p-5">
              <div className="flex items-center gap-2 mb-4">
                <Calendar className="size-5 text-primary" />
                <h2 className="text-lg font-semibold">Agenda do Dr. Filipe</h2>
              </div>
              <div className="space-y-2 text-sm">
                <Kv icon={Mail} label="Calendar" value={data?.calendar_id || "—"} mono />
                <Kv icon={Mail} label="E-mail Felipe" value={data?.lawyer_email || "—"} mono />
                <Kv icon={Clock} label="Duração consulta" value={`${data?.meeting_duration_min || 30} minutos`} />
                <Kv icon={Hash} label="Slots por sugestão" value={String(data?.scheduling_slots_count || 2)} />
              </div>
            </CardContent>
          </Card>
        </motion.div>
      </div>
    </>
  );
}

function FeatureRow({ label, model }: { label: string; model: string }) {
  return (
    <div className="p-3 rounded-lg border">
      <div className="text-xs text-muted-foreground">{label}</div>
      <div className="font-mono text-sm mt-0.5">{model}</div>
    </div>
  );
}

function Kv({ icon: Icon, label, value, mono }: any) {
  return (
    <div className="flex items-center gap-2">
      <Icon className="size-4 text-muted-foreground" />
      <span className="text-xs text-muted-foreground w-32">{label}:</span>
      <span className={mono ? "font-mono" : ""}>{value}</span>
    </div>
  );
}
