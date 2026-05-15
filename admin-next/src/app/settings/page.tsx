"use client";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useState, useEffect } from "react";
import { Save, RotateCcw, AlertCircle } from "lucide-react";
import { toast } from "sonner";
import { api } from "@/lib/api";
import { PageHeader } from "@/components/page-header";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input, Skeleton } from "@/components/ui/index";

const ENV_LABELS: Record<string, string> = {
  OPENAI_MODEL: "Modelo Primário (OpenAI)",
  OPENAI_MODEL_FALLBACK: "Modelo Fallback (OpenAI)",
  LLM_PRIMARY: "Provedor Primário",
  LLM_FALLBACK: "Provedor Fallback",
  MEETING_DURATION_MIN: "Duração reunião (min)",
  SCHEDULING_SLOTS_COUNT: "Nº de horários ofertados",
  GOOGLE_CALENDAR_ID: "Google Calendar ID",
  LAWYER_EMAIL: "Email do advogado",
  ADMIN_USER: "Admin User",
  ADMIN_PASS: "Admin Senha",
  OPENROUTER_MODEL: "Modelo OpenRouter (legado)",
};

export default function SettingsPage() {
  const qc = useQueryClient();
  const { data: env, isLoading: l1 } = useQuery({ queryKey: ["env"], queryFn: api.envGet });
  const { data: llm } = useQuery({ queryKey: ["llm"], queryFn: api.llmInfo });
  const { data: tpl, isLoading: l2 } = useQuery({ queryKey: ["templates"], queryFn: api.templatesGet });

  const [envForm, setEnvForm] = useState<Record<string, string>>({});
  const [tplForm, setTplForm] = useState<{ followup: Record<string, string>; post_meeting: Record<string, string> }>({
    followup: {}, post_meeting: {}
  });

  useEffect(() => { if (env) setEnvForm(env); }, [env]);
  useEffect(() => { if (tpl) setTplForm(tpl); }, [tpl]);

  const saveEnv = useMutation({
    mutationFn: api.envSet,
    onSuccess: () => { toast.success("Configurações salvas! Reinicie containers para aplicar."); qc.invalidateQueries({ queryKey: ["env"] }); },
    onError: (e: any) => toast.error(e.message),
  });

  const saveTpl = useMutation({
    mutationFn: api.templatesSet,
    onSuccess: () => { toast.success("Templates salvos!"); qc.invalidateQueries({ queryKey: ["templates"] }); },
    onError: (e: any) => toast.error(e.message),
  });

  return (
    <>
      <PageHeader title="Configurações" description="Edição direta de .env e templates de mensagens" />
      <div className="p-6 space-y-6 max-w-5xl">
        {/* Variáveis de ambiente */}
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between mb-4">
              <div>
                <h3 className="text-lg font-semibold">Variáveis de Ambiente</h3>
                <p className="text-xs text-muted-foreground">Edição limitada a chaves seguras. Outras vars (OPENAI_API_KEY, etc.) só por SSH.</p>
              </div>
              <Button onClick={() => saveEnv.mutate(envForm)} disabled={saveEnv.isPending}>
                <Save className="size-4 mr-1.5" /> Salvar .env
              </Button>
            </div>
            {l1 ? <Skeleton className="h-40" /> : (
              <div className="grid md:grid-cols-2 gap-4">
                {Object.entries(envForm).map(([k, v]) => (
                  <div key={k}>
                    <label className="text-xs text-muted-foreground">{ENV_LABELS[k] || k}</label>
                    <Input
                      value={v}
                      onChange={(e) => setEnvForm({ ...envForm, [k]: e.target.value })}
                      className="font-mono text-sm"
                      placeholder={k}
                    />
                    <div className="text-[10px] text-muted-foreground mt-0.5 font-mono">{k}</div>
                  </div>
                ))}
              </div>
            )}
            <div className="mt-4 text-xs text-amber-600 flex items-center gap-1.5">
              <AlertCircle className="size-3.5" />
              Reinicie containers (Controle → Reset) para aplicar alterações.
            </div>
          </CardContent>
        </Card>

        {/* Status atual LLMs */}
        {llm && (
          <Card>
            <CardContent className="p-6">
              <h3 className="text-lg font-semibold mb-3">Status LLM</h3>
              <div className="grid sm:grid-cols-2 gap-3 text-sm">
                <Row label="Primário" value={`${llm.primary} (${llm.openai_model})`} />
                <Row label="Fallback" value={`${llm.fallback} (${llm.openai_model_fallback})`} />
                <Row label="OpenAI" value={llm.openai_configured ? "✅ Configurado" : "❌ Sem chave"} />
                <Row label="OpenRouter" value={llm.openrouter_configured ? "✅ Configurado" : "❌ Sem chave"} />
                <Row label="Calendar" value={llm.calendar_id || "—"} />
                <Row label="Duração reunião" value={`${llm.meeting_duration_min} min · ${llm.scheduling_slots_count} slots`} />
              </div>
            </CardContent>
          </Card>
        )}

        {/* Templates */}
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between mb-4">
              <div>
                <h3 className="text-lg font-semibold">Templates — Follow-up D+N</h3>
                <p className="text-xs text-muted-foreground">{`Disparados quando o lead fica em silêncio. Use {nome} para personalizar.`}</p>
              </div>
              <Button onClick={() => saveTpl.mutate({ followup: tplForm.followup })} disabled={saveTpl.isPending}>
                <Save className="size-4 mr-1.5" /> Salvar
              </Button>
            </div>
            {l2 ? <Skeleton className="h-32" /> : (
              <div className="space-y-3">
                {Object.entries(tplForm.followup).map(([day, msg]) => (
                  <div key={day}>
                    <label className="text-xs text-muted-foreground font-mono">D+{day}</label>
                    <textarea
                      value={msg}
                      onChange={(e) => setTplForm({ ...tplForm, followup: { ...tplForm.followup, [day]: e.target.value } })}
                      className="w-full mt-1 p-2 text-sm border rounded-md bg-background min-h-[60px]"
                    />
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between mb-4">
              <div>
                <h3 className="text-lg font-semibold">Templates — Pós-Reunião Dia 1..7</h3>
                <p className="text-xs text-muted-foreground">{`Sequência após reunião com Dr. Filipe. Use {nome} para personalizar.`}</p>
              </div>
              <Button onClick={() => saveTpl.mutate({ post_meeting: tplForm.post_meeting })} disabled={saveTpl.isPending}>
                <Save className="size-4 mr-1.5" /> Salvar
              </Button>
            </div>
            {l2 ? <Skeleton className="h-32" /> : (
              <div className="space-y-3">
                {Object.entries(tplForm.post_meeting).map(([day, msg]) => (
                  <div key={day}>
                    <label className="text-xs text-muted-foreground font-mono">Dia {day}</label>
                    <textarea
                      value={msg}
                      onChange={(e) => setTplForm({ ...tplForm, post_meeting: { ...tplForm.post_meeting, [day]: e.target.value } })}
                      className="w-full mt-1 p-2 text-sm border rounded-md bg-background min-h-[100px]"
                    />
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

function Row({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex justify-between border-b border-border/50 py-1.5">
      <span className="text-muted-foreground">{label}</span>
      <span className="font-mono text-xs">{value}</span>
    </div>
  );
}
